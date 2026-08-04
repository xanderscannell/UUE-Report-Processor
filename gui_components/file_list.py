"""
File Queue Manager Widget
=========================
The list of PDF files queued for processing.

Each file is a card row showing its state (queued / running / done / failed),
its name and folder, a result detail, and its own remove button — so removing
one file no longer means "select it, then find the Remove button".
"""

from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .style import SPACE, tokens
from .widgets import FileGlyph, StatusGlyph, label

ROW_HEIGHT = 54
MAX_VISIBLE_ROWS = 6


class FileRow(QFrame):
    """One file in the queue: status, name, folder, detail, and remove button."""

    remove_requested = Signal(Path)

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = path
        self.setProperty("card", "sunken")
        self.setFixedHeight(ROW_HEIGHT - 6)

        row = QHBoxLayout(self)
        row.setContentsMargins(SPACE["md"], SPACE["sm"], SPACE["sm"], SPACE["sm"])
        row.setSpacing(SPACE["md"])

        self.status = StatusGlyph(18)
        row.addWidget(self.status)

        self.glyph = FileGlyph(20)
        row.addWidget(self.glyph)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)
        self.name_label = QLabel(path.name)
        self.name_label.setStyleSheet("font-weight: 600;")
        self.folder_label = label(self._short_folder(path), "faint")
        text_col.addWidget(self.name_label)
        text_col.addWidget(self.folder_label)
        row.addLayout(text_col, stretch=1)

        self.detail_label = label("", "muted")
        self.detail_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self.detail_label)

        self.remove_button = QPushButton("✕")
        self.remove_button.setProperty("variant", "icon")
        self.remove_button.setFixedSize(QSize(26, 26))
        self.remove_button.setCursor(Qt.PointingHandCursor)
        self.remove_button.setToolTip("Remove from queue")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.path))
        row.addWidget(self.remove_button)

    def set_state(self, state: str, detail: str = ""):
        """Update the status glyph and the right-hand detail text."""
        self.status.set_state(state)
        self.detail_label.setText(detail)
        t = tokens()
        color = {
            StatusGlyph.DONE: t["success"],
            StatusGlyph.FAILED: t["error"],
            StatusGlyph.SKIPPED: t["warning"],
        }.get(state, t["text_muted"])
        self.detail_label.setStyleSheet(f"color: {color};")

    @staticmethod
    def _short_folder(path: Path) -> str:
        """Show the containing folder, trimmed to its last two segments."""
        parts = path.resolve().parent.parts
        return "\\".join(parts[-2:]) if len(parts) > 1 else str(path.parent)


class FileListManager(QWidget):
    """Widget for managing the file processing queue."""

    files_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: List[Path] = []
        self._rows: Dict[Path, FileRow] = {}
        self._locked = False
        self._build_ui()

        # Drives the running-state spinner on active rows.
        self._spinner = QTimer(self)
        self._spinner.setInterval(90)
        self._spinner.timeout.connect(self._advance_spinners)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE["sm"])

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.count_label = label("QUEUE", "eyebrow")
        header.addWidget(self.count_label)
        header.addStretch()

        self.clear_button = QPushButton("Clear all")
        self.clear_button.setProperty("variant", "ghost")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_all)
        header.addWidget(self.clear_button)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setFixedHeight(ROW_HEIGHT + 4)
        layout.addWidget(self.list_widget)

    # -- queue mutation --------------------------------------------------
    def add_files(self, paths: List[Path]) -> int:
        """Add files to the queue, skipping duplicates. Returns the count added."""
        added = 0
        for path in paths:
            if path in self._rows:
                continue
            self.files.append(path)

            row = FileRow(path)
            row.remove_requested.connect(self.remove_file)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, ROW_HEIGHT))
            item.setData(Qt.UserRole, str(path))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
            self._rows[path] = row
            added += 1

        if added:
            self._refresh()
        return added

    def remove_file(self, path: Path):
        """Remove one file from the queue."""
        if self._locked or path not in self._rows:
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == str(path):
                self.list_widget.takeItem(i)
                break
        del self._rows[path]
        self.files = [f for f in self.files if f != path]
        self._refresh()

    def clear_all(self):
        """Clear all files from the queue."""
        if self._locked:
            return
        self.list_widget.clear()
        self.files.clear()
        self._rows.clear()
        self._refresh()

    # -- queue state -----------------------------------------------------
    def get_files(self) -> List[Path]:
        """Return a copy of the queued files."""
        return self.files.copy()

    def has_files(self) -> bool:
        """True if the queue is not empty."""
        return bool(self.files)

    def count(self) -> int:
        """Number of files in the queue."""
        return len(self.files)

    # -- per-file status -------------------------------------------------
    def set_status(self, path: Path, state: str, detail: str = ""):
        """Update one row's status glyph and detail text."""
        row = self._rows.get(path)
        if row is not None:
            row.set_state(state, detail)
        if state == StatusGlyph.RUNNING:
            self._spinner.start()
        elif not self._any_running():
            self._spinner.stop()

    def reset_statuses(self):
        """Return every row to the queued state."""
        for row in self._rows.values():
            row.set_state(StatusGlyph.QUEUED, "")
        self._spinner.stop()

    def set_locked(self, locked: bool):
        """Disable queue edits while processing is running."""
        self._locked = locked
        self.clear_button.setEnabled(not locked and bool(self.files))
        for row in self._rows.values():
            row.remove_button.setEnabled(not locked)

    # -- internals -------------------------------------------------------
    def _any_running(self) -> bool:
        return any(r.status._state == StatusGlyph.RUNNING for r in self._rows.values())

    def _advance_spinners(self):
        for row in self._rows.values():
            row.status.advance()

    def _refresh(self):
        count = len(self.files)
        noun = "FILE" if count == 1 else "FILES"
        self.count_label.setText(f"QUEUE · {count} {noun}")
        self.clear_button.setEnabled(count > 0 and not self._locked)
        # Size the list to its contents (up to MAX_VISIBLE_ROWS, then scroll) so
        # a short queue does not leave a dead gap above the output options.
        visible = max(1, min(count, MAX_VISIBLE_ROWS))
        self.list_widget.setFixedHeight(visible * ROW_HEIGHT + 4)
        self.files_changed.emit()
