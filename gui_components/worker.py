"""
Background Processing Worker
============================
Runs PDF processing off the GUI thread using a QThread, communicating back
through Qt signals (delivered on the GUI thread automatically).
"""

import logging
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QThread, Signal

from setup_report_processor import SetupReportProcessor

logger = logging.getLogger("setup_report_processor")


class ProcessorWorker(QThread):
    """Processes a queue of PDF files and reports progress via signals."""

    status = Signal(str)                 # human-readable status line
    progress = Signal(int, int, int)     # percent, current, total
    gantt_ready = Signal(str, list)      # label, list[{Location, StartTime, EndTime}]
    finished_all = Signal(bool)          # cancelled?

    def __init__(self, files: List[Path], options: Dict, parent=None):
        super().__init__(parent)
        self.files = files
        self.options = options
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        total = len(self.files)

        for i, pdf_path in enumerate(self.files):
            if self._cancelled:
                self.status.emit("Processing cancelled by user")
                break

            self.status.emit(f"Processing {pdf_path.name}...")

            try:
                processor = SetupReportProcessor(
                    str(pdf_path), config_path=self.options.get("config_path")
                )
                df = processor.process()

                if len(df) == 0:
                    logger.warning(f"No valid events found in {pdf_path.name}")
                    continue

                output_dir = self.options["output_dir"]
                output_dir.mkdir(parents=True, exist_ok=True)
                basename = processor.get_output_basename()

                if self.options["excel_enabled"]:
                    processor.save_to_excel(df, str(output_dir / f"{basename}_schedule.xlsx"))

                if self.options["csv_enabled"]:
                    processor.save_to_csv(df, str(output_dir / f"{basename}_schedule.csv"))

                gantt_rows = processor.create_gantt_rows(processor._events)
                if gantt_rows:
                    self.gantt_ready.emit(basename or pdf_path.stem, gantt_rows)

                self.progress.emit(int((i + 1) / total * 100), i + 1, total)
                logger.info(f"Successfully processed {pdf_path.name}")

            except FileNotFoundError:
                logger.error(f"File not found: {pdf_path.name}")
            except ValueError as e:
                logger.error(f"Invalid file: {pdf_path.name} - {e}")
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")

        self.finished_all.emit(self._cancelled)
