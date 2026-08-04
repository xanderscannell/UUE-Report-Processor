#!/usr/bin/env python3
"""
Setup Report Processor - GUI (PySide6)
======================================
Drag-and-drop desktop interface for processing Daily Setup Report PDFs.

The window is staged: it shows an inviting drop target when empty, a working
queue once files are added, and a results summary when a run finishes. Only
what matters at the current step is on screen; setup actions live in the
Settings menu and the processing log behind a "Details" disclosure.

Features:
- Drag-and-drop PDF files anywhere in the window (native Qt)
- Batch processing on a background thread, with per-file status
- Excel and/or CSV output
- Embedded event timeline (pyqtgraph Gantt chart)
- Live, color-coded logging, tucked out of the way until needed
- Custom light/dark theme, crisp on high-DPI/scaled displays
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Resolve base directory (works for both script and frozen .exe)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

from gui_components import (
    DIMENSIONS,
    GUI_DEFAULTS,
    SPACE,
    BuildingColorEditor,
    BuildingColors,
    Card,
    CollapsibleSection,
    DragDropZone,
    FileListManager,
    GanttWindow,
    HeaderBar,
    LocationEditor,
    LogPanel,
    ProcessorWorker,
    QtLogHandler,
    ResultPanel,
    StatusGlyph,
    apply_theme,
    label,
    prefix_of,
)

STAGE_EMPTY, STAGE_WORK, STAGE_DONE = 0, 1, 2


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(GUI_DEFAULTS["window_title"])
        self.resize(GUI_DEFAULTS["window_width"], GUI_DEFAULTS["window_height"])
        self.setMinimumSize(
            GUI_DEFAULTS["window_min_width"], GUI_DEFAULTS["window_min_height"]
        )
        self.setAcceptDrops(True)

        icon_path = BASE_DIR / "UUE.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.worker = None
        self.processing = False
        self.gantt_window = None
        self._gantt_data = {}  # {report label: gantt rows}
        self.output_dir = Path(GUI_DEFAULTS["output_dir"])
        self.config_path = BASE_DIR / "location_config.json"
        self.building_colors = BuildingColors.load(self.config_path)

        self._build_ui()
        self._setup_logging()
        self._set_stage(STAGE_EMPTY)

    # ==================================================================
    # UI construction
    # ==================================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Brand header (full-bleed)
        self.header = HeaderBar(
            GUI_DEFAULTS["window_title"], GUI_DEFAULTS["window_subtitle"]
        )
        self.header.menu_button.clicked.connect(self._show_settings_menu)
        root.addWidget(self.header)

        # Centered content column
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        wrapper.addStretch()

        content = QWidget()
        content.setMaximumWidth(DIMENSIONS["content_max_width"] + 60)
        column = QVBoxLayout(content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(SPACE["md"])

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_empty_page())
        self.stack.addWidget(self._build_workspace_page())
        self.stack.addWidget(self._build_result_page())
        column.addWidget(self.stack, stretch=1)

        column.addWidget(self._build_details())

        wrapper.addWidget(content, stretch=1)
        wrapper.addStretch()
        root.addLayout(wrapper, stretch=1)

    # -- stage 1: empty --------------------------------------------------
    def _build_empty_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE["lg"])

        layout.addStretch()

        self.hero_drop = DragDropZone(compact=False)
        self.hero_drop.setMaximumHeight(DIMENSIONS["drop_zone_max_height"])
        self.hero_drop.files_added.connect(self._on_files_added)
        self.hero_drop.files_rejected.connect(self._on_files_rejected)
        layout.addWidget(self.hero_drop, stretch=1)

        layout.addStretch()

        steps = QHBoxLayout()
        steps.setSpacing(SPACE["md"])
        for i, (title, body) in enumerate(
            [
                ("Add PDFs", "Drop one or more Daily Setup Reports."),
                ("Choose output", "Excel, CSV, or both."),
                ("Process", "Get a sorted schedule and a timeline."),
            ],
            start=1,
        ):
            steps.addWidget(self._build_step(i, title, body), stretch=1)
        layout.addLayout(steps)
        return page

    def _build_step(self, number: int, title: str, body: str) -> QWidget:
        card = Card(variant="sunken", padding=SPACE["md"])
        card.body.setSpacing(SPACE["xs"])

        head = QHBoxLayout()
        head.setSpacing(SPACE["sm"])
        badge = QLabel(str(number))
        badge.setObjectName("StepBadge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(20, 20)
        head.addWidget(badge)
        head.addWidget(label(title, "body"))
        head.addStretch()
        card.body.addLayout(head)

        text = label(body, "faint")
        text.setWordWrap(True)
        card.body.addWidget(text)
        return card

    # -- stage 2: workspace ----------------------------------------------
    def _build_workspace_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE["md"])

        self.compact_drop = DragDropZone(compact=True)
        self.compact_drop.files_added.connect(self._on_files_added)
        self.compact_drop.files_rejected.connect(self._on_files_rejected)
        layout.addWidget(self.compact_drop)

        self.file_list = FileListManager()
        self.file_list.files_changed.connect(self._on_queue_changed)
        layout.addWidget(self.file_list)

        layout.addWidget(self._build_output_card())
        layout.addWidget(self._build_action_area())
        layout.addStretch()
        return page

    def _build_output_card(self) -> QWidget:
        card = Card(padding=SPACE["md"])
        card.body.setSpacing(SPACE["sm"])

        card.body.addWidget(label("OUTPUT", "eyebrow"))

        row = QHBoxLayout()
        row.setSpacing(SPACE["sm"])

        self.excel_toggle = QPushButton("Excel  .xlsx")
        self.csv_toggle = QPushButton("CSV  .csv")
        for toggle, default in (
            (self.excel_toggle, GUI_DEFAULTS["excel_enabled"]),
            (self.csv_toggle, GUI_DEFAULTS["csv_enabled"]),
        ):
            toggle.setProperty("variant", "toggle")
            toggle.setCheckable(True)
            toggle.setChecked(default)
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.toggled.connect(self._update_process_button)
            row.addWidget(toggle)

        row.addStretch()

        row.addWidget(label("Saving to", "faint"))
        self.folder_button = QPushButton()
        self.folder_button.setProperty("variant", "quiet")
        self.folder_button.setCursor(Qt.PointingHandCursor)
        self.folder_button.clicked.connect(self._browse_output_folder)
        row.addWidget(self.folder_button)
        card.body.addLayout(row)

        self._refresh_folder_button()
        return card

    def _build_action_area(self) -> QWidget:
        holder = QWidget()
        layout = QVBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE["sm"])

        # Idle and running share this slot. They are shown/hidden rather than
        # stacked so the area is only ever as tall as what it is showing.
        self.idle_panel = QWidget()
        idle_layout = QVBoxLayout(self.idle_panel)
        idle_layout.setContentsMargins(0, 0, 0, 0)
        idle_layout.setSpacing(SPACE["xs"])
        self.process_button = QPushButton("Process files")
        self.process_button.setProperty("variant", "primary")
        self.process_button.setCursor(Qt.PointingHandCursor)
        self.process_button.setMinimumHeight(46)
        self.process_button.clicked.connect(self._start_processing)
        idle_layout.addWidget(self.process_button)
        self.hint_label = label("", "faint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        idle_layout.addWidget(self.hint_label)

        # Running: progress and a way out.
        self.running_panel = QWidget()
        self.running_panel.hide()
        run_layout = QVBoxLayout(self.running_panel)
        run_layout.setContentsMargins(0, 0, 0, 0)
        run_layout.setSpacing(SPACE["sm"])

        status_row = QHBoxLayout()
        self.progress_label = label("Starting…", "muted")
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        self.progress_count = label("", "faint")
        status_row.addWidget(self.progress_count)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("variant", "ghost")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self._cancel_processing)
        status_row.addWidget(self.cancel_button)
        run_layout.addLayout(status_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        run_layout.addWidget(self.progress_bar)

        layout.addWidget(self.idle_panel)
        layout.addWidget(self.running_panel)
        return holder

    def _show_running(self, running: bool):
        """Swap the primary call to action for the progress readout."""
        self.idle_panel.setVisible(not running)
        self.running_panel.setVisible(running)

    # -- stage 3: results ------------------------------------------------
    def _build_result_page(self) -> QWidget:
        self.result_panel = ResultPanel()
        self.result_panel.open_folder_requested.connect(self._open_output_folder)
        self.result_panel.open_gantt_requested.connect(self._open_gantt)
        self.result_panel.process_more_requested.connect(self._back_to_workspace)
        return self.result_panel

    # -- persistent details disclosure -----------------------------------
    def _build_details(self) -> QWidget:
        self.log_panel = LogPanel(max_lines=GUI_DEFAULTS["max_log_lines"])
        self.log_panel.setFixedHeight(DIMENSIONS["log_height"])
        self.log_panel.counts_changed.connect(self._on_log_counts)

        self.details = CollapsibleSection("Details", self.log_panel, expanded=False)

        clear_button = QPushButton("Clear")
        clear_button.setProperty("variant", "ghost")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.log_panel.clear_log)
        self.details.add_trailing(clear_button)

        holder = QFrame()
        holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(self.details)
        return holder

    # ==================================================================
    # Settings menu
    # ==================================================================
    def _show_settings_menu(self):
        menu = QMenu(self)

        locations = QAction("Location Whitelist…", self)
        locations.triggered.connect(self._open_location_editor)
        menu.addAction(locations)

        buildings = QAction("Building Colors…", self)
        buildings.triggered.connect(self._open_building_editor)
        menu.addAction(buildings)

        folder = QAction("Output Folder…", self)
        folder.triggered.connect(self._browse_output_folder)
        menu.addAction(folder)

        menu.addSeparator()

        self.gantt_auto_action = QAction("Open timeline when finished", self)
        self.gantt_auto_action.setCheckable(True)
        self.gantt_auto_action.setChecked(self._gantt_autolaunch)
        self.gantt_auto_action.toggled.connect(self._set_gantt_autolaunch)
        menu.addAction(self.gantt_auto_action)

        verbose = QAction("Verbose logging", self)
        verbose.setCheckable(True)
        verbose.setChecked(self._verbose)
        verbose.toggled.connect(self._set_verbose)
        menu.addAction(verbose)

        menu.addSeparator()

        log_file = QAction("Open log file", self)
        log_file.triggered.connect(self._view_log_file)
        menu.addAction(log_file)

        shortcut = QAction("Add desktop shortcut", self)
        shortcut.triggered.connect(self._create_desktop_shortcut)
        menu.addAction(shortcut)

        menu.addSeparator()
        about = QAction("About", self)
        about.triggered.connect(self._show_about)
        menu.addAction(about)

        button = self.header.menu_button
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Setup Report Processor",
            f"<b>{GUI_DEFAULTS['window_title']}</b><br><br>"
            "Extracts event schedules from Daily Setup Report PDFs and writes "
            "chronologically sorted Excel/CSV files, plus an interactive "
            "timeline of the day.<br><br>"
            f"Working folder: {BASE_DIR}",
        )

    # ==================================================================
    # Logging
    # ==================================================================
    def _setup_logging(self):
        self._verbose = GUI_DEFAULTS["verbose_logging"]
        self._gantt_autolaunch = GUI_DEFAULTS["gantt_autolaunch"]

        self.log_handler = QtLogHandler()
        self.log_handler.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
        self.log_handler.message.connect(self.log_panel.append_record)

        processor_logger = logging.getLogger("setup_report_processor")
        processor_logger.addHandler(self.log_handler)
        self._set_verbose(self._verbose)

    def _set_verbose(self, enabled: bool):
        self._verbose = enabled
        logging.getLogger("setup_report_processor").setLevel(
            logging.DEBUG if enabled else logging.INFO
        )

    def _set_gantt_autolaunch(self, enabled: bool):
        self._gantt_autolaunch = enabled

    def _on_log_counts(self, warnings: int, errors: int):
        """Badge the collapsed Details section so problems are never silent."""
        if errors:
            self.details.set_badge(f"{errors} error{'' if errors == 1 else 's'}", "error")
        elif warnings:
            self.details.set_badge(
                f"{warnings} warning{'' if warnings == 1 else 's'}", "warning"
            )
        else:
            self.details.set_badge("")

    # ==================================================================
    # Stage management
    # ==================================================================
    def _set_stage(self, stage: int):
        self._stage = stage
        self.stack.setCurrentIndex(stage)

    def _back_to_workspace(self):
        self.file_list.reset_statuses()
        self._set_stage(STAGE_WORK if self.file_list.has_files() else STAGE_EMPTY)
        self._update_process_button()

    # ==================================================================
    # File queue
    # ==================================================================
    def _on_files_added(self, paths):
        if self.processing:
            return
        if self._stage == STAGE_DONE:
            self.file_list.reset_statuses()
        added = self.file_list.add_files(paths)
        if added:
            self._set_stage(STAGE_WORK)
        self._update_process_button()

    def _on_files_rejected(self, paths):
        for path in paths:
            logging.getLogger("setup_report_processor").warning(
                f"Ignored non-PDF file: {path.name}"
            )

    def _on_queue_changed(self):
        if not self.file_list.has_files() and not self.processing:
            self._set_stage(STAGE_EMPTY)
        self._update_process_button()

    def _is_dry_run(self) -> bool:
        """True when no file format is selected — timeline only, nothing saved."""
        return not (self.excel_toggle.isChecked() or self.csv_toggle.isChecked())

    def _update_process_button(self):
        count = self.file_list.count()
        dry_run = self._is_dry_run()

        if not count:
            self.process_button.setText("Process files")
        else:
            verb = "Preview" if dry_run else "Process"
            self.process_button.setText(f"{verb} {count} file{'' if count == 1 else 's'}")
        self.process_button.setEnabled(bool(count) and not self.processing)

        if not count:
            self.hint_label.setText("Add at least one PDF to continue")
        elif dry_run:
            self.hint_label.setText("Timeline only — no files will be saved")
        else:
            self.hint_label.setText("The timeline is always available afterwards")

    # ==================================================================
    # Options
    # ==================================================================
    def _refresh_folder_button(self):
        resolved = self.output_dir.resolve()
        self.folder_button.setText(resolved.name)
        self.folder_button.setToolTip(f"Change output folder\n{resolved}")

    def _open_location_editor(self):
        editor = LocationEditor(self.config_path, self)
        if editor.exec():
            QMessageBox.information(
                self, "Locations Saved",
                "Location configuration updated.\n\n"
                "Changes apply to files processed from now on.",
            )

    def _open_building_editor(self):
        """Edit timeline colors per building, then re-apply them live."""
        editor = BuildingColorEditor(
            self.config_path, self._seen_building_prefixes(), self
        )
        if editor.exec():
            self.building_colors = editor.colors
            if self.gantt_window is not None:
                self.gantt_window.buildings = self.building_colors
                self.gantt_window.refresh()

    def _seen_building_prefixes(self):
        """Building prefixes found in the reports processed this session."""
        return {
            prefix_of(row.get("Location", ""))
            for rows in self._gantt_data.values()
            for row in rows
        }

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", str(self.output_dir.resolve())
        )
        if folder:
            self.output_dir = Path(folder)
            self._refresh_folder_button()

    # ==================================================================
    # Processing
    # ==================================================================
    def _start_processing(self):
        files = self.file_list.get_files()
        if not files:
            return

        config_path = self.config_path
        options = {
            "excel_enabled": self.excel_toggle.isChecked(),
            "csv_enabled": self.csv_toggle.isChecked(),
            "output_dir": self.output_dir,
            "config_path": str(config_path) if config_path.exists() else None,
        }

        self.processing = True
        self.file_list.set_locked(True)
        self.file_list.reset_statuses()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting…")
        self.progress_count.setText(f"0 / {len(files)}")
        self._show_running(True)
        self.log_panel.clear_log()

        self._gantt_data = {}

        self.worker = ProcessorWorker(files, options)
        self.worker.status.connect(self.progress_label.setText)
        self.worker.progress.connect(self._on_progress)
        self.worker.file_started.connect(self._on_file_started)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.gantt_ready.connect(self._on_gantt_ready)
        self.worker.finished_all.connect(self._on_finished)
        self.worker.start()

    def _cancel_processing(self):
        if self.worker:
            self.cancel_button.setEnabled(False)
            self.progress_label.setText("Finishing current file…")
            self.worker.cancel()

    def _on_progress(self, percent: int, current: int, total: int):
        self.progress_bar.setValue(percent)
        self.progress_count.setText(f"{current} / {total}")

    def _on_file_started(self, path: Path):
        self.file_list.set_status(path, StatusGlyph.RUNNING, "working…")

    def _on_file_done(self, path: Path, state: str, detail: str):
        self.file_list.set_status(path, state, detail)

    def _on_gantt_ready(self, report: str, rows: list):
        self._gantt_data[report] = rows
        if self.gantt_window is not None and self.gantt_window.isVisible():
            self.gantt_window.set_datasets(self._gantt_data)

    def _on_finished(self, cancelled: bool, summary: dict):
        self.processing = False
        self.file_list.set_locked(False)
        self.cancel_button.setEnabled(True)
        self._show_running(False)
        self._update_process_button()

        formats = []
        if self.excel_toggle.isChecked():
            formats.append("Excel")
        if self.csv_toggle.isChecked():
            formats.append("CSV")

        self.result_panel.set_results(
            {
                **summary,
                "cancelled": cancelled,
                "output_dir": self.output_dir if summary.get("ok") else None,
                "formats": formats if summary.get("ok") else [],
                "has_gantt": bool(self._gantt_data),
            }
        )
        self._set_stage(STAGE_DONE)

        # Surface problems instead of hiding them behind the disclosure.
        if self.log_panel.error_count or self.log_panel.warning_count:
            self.details.set_expanded(True)

        if not cancelled and self._gantt_autolaunch and self._gantt_data:
            self._open_gantt()

    # ==================================================================
    # Timeline
    # ==================================================================
    def _open_gantt(self):
        if not self._gantt_data:
            return
        # Any building seen for the first time gets a color now, so the chart
        # never falls back to gray just because a venue is new.
        if self.building_colors.ensure(self._seen_building_prefixes()):
            self.building_colors.save(self.config_path)
        if self.gantt_window is None:
            self.gantt_window = GanttWindow(self, self.building_colors)
        self.gantt_window.buildings = self.building_colors
        self.gantt_window.set_datasets(self._gantt_data)
        self.gantt_window.show()
        self.gantt_window.raise_()
        self.gantt_window.activateWindow()

    # ==================================================================
    # Window-wide drag and drop
    # ==================================================================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.processing:
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and not self.processing:
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        zone = self.hero_drop if self._stage == STAGE_EMPTY else self.compact_drop
        zone.handle_paths(paths)
        event.acceptProposedAction()

    # ==================================================================
    # Misc actions
    # ==================================================================
    def _open_output_folder(self):
        output_dir = self.output_dir
        if not output_dir.exists():
            QMessageBox.warning(
                self, "Folder Not Found",
                f"Output folder does not exist yet:\n{output_dir.resolve()}",
            )
            return
        self._open_path(output_dir)

    def _view_log_file(self):
        log_file = Path("setup_report_processor.log")
        if not log_file.exists():
            QMessageBox.information(
                self, "No Log File",
                "The log file does not exist yet. Process some files first.",
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

    # ==================================================================
    # Theme
    # ==================================================================
    def refresh_theme(self):
        """Re-apply the stylesheet and repaint custom-drawn widgets."""
        app = QApplication.instance()
        if app is not None:
            apply_theme(app)
        self.hero_drop.refresh_style()
        self.compact_drop.refresh_style()
        self.update()


def main():
    """Main entry point for the GUI application."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    apply_theme(app)

    window = MainWindow()

    # Follow the OS when it switches between light and dark (Qt 6.5+).
    hints = app.styleHints()
    if hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(lambda _: window.refresh_theme())

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
