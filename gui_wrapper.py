#!/usr/bin/env python3
"""
Setup Report Processor - GUI (PySide6)
======================================
Drag-and-drop desktop interface for processing Daily Setup Report PDFs.

Features:
- Drag-and-drop PDF files (native Qt, no extra dependency)
- Batch processing on a background thread
- Excel and/or CSV output
- Embedded Gantt chart (pyqtgraph) for the event schedule
- Real-time progress tracking and live, color-coded logging
- High-DPI crisp rendering on scaled displays
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Resolve base directory (works for both script and frozen .exe)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

from gui_components import (
    GUI_DEFAULTS,
    QtLogHandler,
    LogPanel,
    DragDropZone,
    FileListManager,
    LocationEditor,
    ProcessorWorker,
    GanttWindow,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(GUI_DEFAULTS["window_title"])
        self.resize(GUI_DEFAULTS["window_width"], GUI_DEFAULTS["window_height"])

        icon_path = BASE_DIR / "UUE.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.worker = None
        self.processing = False
        self.gantt_window = None
        self._gantt_data = {}  # {report label: gantt rows}

        self._build_ui()
        self._setup_logging()

    # -- UI construction -------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Drop zone
        self.drop_zone = DragDropZone()
        self.drop_zone.files_added.connect(self._on_files_added)
        root.addWidget(self.drop_zone)

        # File list
        self.file_list = FileListManager()
        self.file_list.files_changed.connect(self._update_process_button)
        root.addWidget(self.file_list)

        # Output options
        root.addWidget(self._build_options())

        # Action buttons
        root.addLayout(self._build_action_buttons())

        # Process button
        self.process_button = QPushButton("Process Files")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._start_processing)
        root.addWidget(self.process_button)

        # Progress
        root.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        root.addWidget(self.progress_bar)
        self.progress_label = QLabel("Ready")
        root.addWidget(self.progress_label)

        # Status log
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout(log_group)
        self.log_panel = LogPanel(max_lines=GUI_DEFAULTS["max_log_lines"])
        log_layout.addWidget(self.log_panel)
        root.addWidget(log_group, stretch=1)

    def _build_options(self) -> QGroupBox:
        group = QGroupBox("Output Options")
        layout = QVBoxLayout(group)

        loc_btn = QPushButton("Location Whitelist...")
        loc_btn.clicked.connect(self._open_location_editor)
        layout.addWidget(loc_btn, alignment=Qt.AlignLeft)

        formats = QHBoxLayout()
        self.excel_check = QCheckBox("Excel (.xlsx)")
        self.excel_check.setChecked(GUI_DEFAULTS["excel_enabled"])
        self.csv_check = QCheckBox("CSV (.csv)")
        self.csv_check.setChecked(GUI_DEFAULTS["csv_enabled"])
        self.gantt_check = QCheckBox("Auto-launch Gantt Chart")
        self.gantt_check.setChecked(GUI_DEFAULTS["gantt_autolaunch"])
        formats.addWidget(self.excel_check)
        formats.addWidget(self.csv_check)
        formats.addWidget(self.gantt_check)
        formats.addStretch()
        layout.addLayout(formats)

        folder = QHBoxLayout()
        folder.addWidget(QLabel("Output Folder:"))
        self.output_dir_edit = QLineEdit(str(GUI_DEFAULTS["output_dir"]))
        folder.addWidget(self.output_dir_edit, stretch=1)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_output_folder)
        folder.addWidget(browse)
        layout.addLayout(folder)

        self.verbose_check = QCheckBox("Verbose Logging")
        self.verbose_check.setChecked(GUI_DEFAULTS["verbose_logging"])
        self.verbose_check.toggled.connect(self._toggle_verbose)
        layout.addWidget(self.verbose_check)

        return group

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()

        open_btn = QPushButton("Open Output Folder")
        open_btn.clicked.connect(self._open_output_folder)

        self.gantt_button = QPushButton("View Gantt")
        self.gantt_button.setEnabled(False)
        self.gantt_button.clicked.connect(self._open_gantt)

        clear_btn = QPushButton("Clear Status")
        clear_btn.clicked.connect(lambda: self.log_panel.clear_log())

        log_btn = QPushButton("View Log File")
        log_btn.clicked.connect(self._view_log_file)

        shortcut_btn = QPushButton("Add Desktop Shortcut")
        shortcut_btn.clicked.connect(self._create_desktop_shortcut)

        for btn in (open_btn, self.gantt_button, clear_btn, log_btn, shortcut_btn):
            row.addWidget(btn)
        return row

    # -- logging ---------------------------------------------------------
    def _setup_logging(self):
        self.log_handler = QtLogHandler()
        self.log_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        self.log_handler.message.connect(self.log_panel.append_record)

        processor_logger = logging.getLogger("setup_report_processor")
        processor_logger.addHandler(self.log_handler)
        self._toggle_verbose(self.verbose_check.isChecked())

    def _toggle_verbose(self, enabled: bool):
        logger = logging.getLogger("setup_report_processor")
        logger.setLevel(logging.DEBUG if enabled else logging.INFO)

    # -- file queue ------------------------------------------------------
    def _on_files_added(self, paths):
        self.file_list.add_files(paths)

    def _update_process_button(self):
        self.process_button.setEnabled(self.file_list.has_files() and not self.processing)

    # -- options actions -------------------------------------------------
    def _open_location_editor(self):
        editor = LocationEditor(BASE_DIR / "location_config.json", self)
        if editor.exec():
            QMessageBox.information(
                self, "Settings Saved",
                "Location configuration updated.\n\nChanges apply to newly processed files.",
            )

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.output_dir_edit.text()
        )
        if folder:
            self.output_dir_edit.setText(folder)

    # -- processing ------------------------------------------------------
    def _start_processing(self):
        if not (self.excel_check.isChecked() or self.csv_check.isChecked()
                or self.gantt_check.isChecked()):
            QMessageBox.warning(
                self, "No Output Selected",
                "Please select at least one output (Excel, CSV, or Gantt Chart).",
            )
            return

        files = self.file_list.get_files()
        if not files:
            return

        config_path = BASE_DIR / "location_config.json"
        options = {
            "excel_enabled": self.excel_check.isChecked(),
            "csv_enabled": self.csv_check.isChecked(),
            "output_dir": Path(self.output_dir_edit.text()),
            "config_path": str(config_path) if config_path.exists() else None,
        }

        self.processing = True
        self.process_button.setText("Cancel")
        self.process_button.clicked.disconnect()
        self.process_button.clicked.connect(self._cancel_processing)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting...")
        self.log_panel.clear_log()

        # Reset Gantt data for this run.
        self._gantt_data = {}
        self.gantt_button.setEnabled(False)

        self.worker = ProcessorWorker(files, options)
        self.worker.status.connect(self.progress_label.setText)
        self.worker.progress.connect(self._on_progress)
        self.worker.gantt_ready.connect(self._on_gantt_ready)
        self.worker.finished_all.connect(self._on_finished)
        self.worker.start()

    def _cancel_processing(self):
        if self.worker:
            self.worker.cancel()

    def _on_progress(self, percent: int, current: int, total: int):
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"Processing... ({current}/{total} files)")

    def _on_gantt_ready(self, label: str, rows: list):
        self._gantt_data[label] = rows
        self.gantt_button.setEnabled(True)
        # Live-update the chart if it is already open.
        if self.gantt_window is not None and self.gantt_window.isVisible():
            self.gantt_window.set_datasets(self._gantt_data)

    def _on_finished(self, cancelled: bool):
        self.processing = False
        self.process_button.setText("Process Files")
        self.process_button.clicked.disconnect()
        self.process_button.clicked.connect(self._start_processing)
        self.progress_label.setText("Ready")
        self._update_process_button()

        if not cancelled:
            message = f"Finished processing {len(self.file_list.get_files())} file(s)."
            if self.excel_check.isChecked() or self.csv_check.isChecked():
                message += f"\n\nOutput saved to: {self.output_dir_edit.text()}"
            QMessageBox.information(self, "Processing Complete", message)
            if self.gantt_check.isChecked() and self._gantt_data:
                self._open_gantt()

    # -- gantt -----------------------------------------------------------
    def _open_gantt(self):
        if not self._gantt_data:
            return
        if self.gantt_window is None:
            self.gantt_window = GanttWindow(self)
        self.gantt_window.set_datasets(self._gantt_data)
        self.gantt_window.show()
        self.gantt_window.raise_()
        self.gantt_window.activateWindow()

    # -- misc actions ----------------------------------------------------
    def _open_output_folder(self):
        output_dir = Path(self.output_dir_edit.text())
        if not output_dir.exists():
            QMessageBox.warning(
                self, "Folder Not Found",
                f"Output folder does not exist yet:\n{output_dir}",
            )
            return
        self._open_path(output_dir)

    def _view_log_file(self):
        log_file = Path("setup_report_processor.log")
        if not log_file.exists():
            QMessageBox.information(
                self, "No Log File",
                "Log file does not exist yet. Process some files first.",
            )
            return
        self._open_path(log_file)

    @staticmethod
    def _open_path(path: Path):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])

    def _create_desktop_shortcut(self):
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        try:
            result = subprocess.run(
                ["powershell", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                desktop = Path(result.stdout.strip())
        except Exception:
            pass
        shortcut = desktop / "Setup Report Processor.lnk"

        if shortcut.exists():
            QMessageBox.information(self, "Shortcut Exists", "A desktop shortcut already exists.")
            return

        target = Path(sys.executable)
        if getattr(sys, "frozen", False):
            args_line = ""
            icon_line = f'$s.IconLocation = "{target},0"; '
        else:
            args_line = f'$s.Arguments = "{Path(__file__).resolve()}"; '
            icon_path = BASE_DIR / "UUE.ico"
            icon_line = f'$s.IconLocation = "{icon_path}"; ' if icon_path.exists() else ""

        ps_script = (
            f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut}"); '
            f'$s.TargetPath = "{target}"; '
            f"{args_line}"
            f'$s.WorkingDirectory = "{BASE_DIR}"; '
            f"{icon_line}"
            "$s.Save()"
        )
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script], capture_output=True, text=True
            )
            if result.returncode == 0:
                QMessageBox.information(self, "Shortcut Created", "Desktop shortcut has been created.")
            else:
                QMessageBox.critical(self, "Shortcut Failed", f"Could not create shortcut:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Shortcut Failed", f"Error creating shortcut:\n{e}")


def main():
    """Main entry point for the GUI application."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
