"""
Background Processing Worker
============================
Runs PDF processing off the GUI thread using a QThread, communicating back
through Qt signals (delivered on the GUI thread automatically).

The worker reports per-file outcomes as well as overall progress so the UI can
show live status on each queued file and a summary once the run ends.
"""

import logging
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QThread, Signal

from setup_report_processor import SetupReportProcessor

logger = logging.getLogger("setup_report_processor")

DONE = "done"
FAILED = "failed"
SKIPPED = "skipped"


class ProcessorWorker(QThread):
    """Processes a queue of PDF files and reports progress via signals."""

    status = Signal(str)                    # human-readable status line
    progress = Signal(int, int, int)        # percent, current, total
    file_started = Signal(object)           # Path
    file_done = Signal(object, str, str)    # Path, state, detail text
    gantt_ready = Signal(str, list)         # label, list[{Location, StartTime, EndTime}]
    finished_all = Signal(bool, dict)       # cancelled?, summary

    def __init__(self, files: List[Path], options: Dict, parent=None):
        super().__init__(parent)
        self.files = files
        self.options = options
        self._cancelled = False

    def cancel(self):
        """Request cancellation; takes effect between files."""
        self._cancelled = True

    def run(self):
        total = len(self.files)
        summary = {"ok": 0, "failed": 0, "empty": 0, "events": 0}

        for i, pdf_path in enumerate(self.files):
            if self._cancelled:
                self.status.emit("Cancelled")
                break

            self.status.emit(f"Reading {pdf_path.name}…")
            self.file_started.emit(pdf_path)

            try:
                processor = SetupReportProcessor(
                    str(pdf_path), config_path=self.options.get("config_path")
                )
                df = processor.process()
                event_count = len(processor._events)

                if len(df) == 0:
                    logger.warning(
                        f"No events matched the location whitelist in {pdf_path.name}"
                    )
                    summary["empty"] += 1
                    self.file_done.emit(pdf_path, SKIPPED, "no matching events")
                else:
                    output_dir = self.options["output_dir"]
                    basename = processor.get_output_basename()

                    # Dry run (no format selected) builds the timeline only —
                    # don't even create the output folder.
                    if self.options["excel_enabled"] or self.options["csv_enabled"]:
                        output_dir.mkdir(parents=True, exist_ok=True)

                    if self.options["excel_enabled"]:
                        processor.save_to_excel(
                            df, str(output_dir / f"{basename}_schedule.xlsx")
                        )
                    if self.options["csv_enabled"]:
                        processor.save_to_csv(
                            df, str(output_dir / f"{basename}_schedule.csv")
                        )

                    gantt_rows = processor.create_gantt_rows(processor._events)
                    if gantt_rows:
                        self.gantt_ready.emit(basename or pdf_path.stem, gantt_rows)

                    summary["ok"] += 1
                    summary["events"] += event_count
                    noun = "event" if event_count == 1 else "events"
                    self.file_done.emit(pdf_path, DONE, f"{event_count} {noun}")
                    logger.info(
                        f"Read {pdf_path.name} ({event_count} {noun}); no files written"
                        if not (self.options["excel_enabled"] or self.options["csv_enabled"])
                        else f"Successfully processed {pdf_path.name}"
                    )

            except FileNotFoundError:
                logger.error(f"File not found: {pdf_path.name}")
                summary["failed"] += 1
                self.file_done.emit(pdf_path, FAILED, "file not found")
            except ValueError as e:
                logger.error(f"Invalid file: {pdf_path.name} - {e}")
                summary["failed"] += 1
                self.file_done.emit(pdf_path, FAILED, "not a readable PDF")
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                summary["failed"] += 1
                self.file_done.emit(pdf_path, FAILED, "failed")

            # Always advance, including for skipped and failed files.
            self.progress.emit(int((i + 1) / total * 100), i + 1, total)

        self.finished_all.emit(self._cancelled, summary)
