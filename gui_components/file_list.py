"""
File Queue Manager Widget
=========================
Manages the list of PDF files queued for processing (PySide6).
"""

from pathlib import Path
from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FileListManager(QWidget):
    """Widget for managing the file processing queue."""

    files_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: List[Path] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self.count_label = QLabel("Files to Process (0):")
        self.count_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self.count_label)
        header.addStretch()

        self.clear_button = QPushButton("Clear All")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_all)
        header.addWidget(self.clear_button)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(
            lambda _: self.remove_selected()
        )
        layout.addWidget(self.list_widget)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_selected)
        layout.addWidget(self.remove_button)

    def add_files(self, paths: List[Path]):
        """Add files to the queue, avoiding duplicates."""
        added = 0
        for path in paths:
            if path not in self.files:
                self.files.append(path)
                self.list_widget.addItem(path.name)
                added += 1
        if added:
            self._refresh()

    def remove_selected(self):
        """Remove the currently selected file from the queue."""
        row = self.list_widget.currentRow()
        if row < 0:
            return
        self.list_widget.takeItem(row)
        del self.files[row]
        self._refresh()

    def clear_all(self):
        """Clear all files from the queue."""
        self.list_widget.clear()
        self.files.clear()
        self._refresh()

    def get_files(self) -> List[Path]:
        """Return a copy of the queued files."""
        return self.files.copy()

    def has_files(self) -> bool:
        """True if the queue is not empty."""
        return bool(self.files)

    def _refresh(self):
        count = len(self.files)
        self.count_label.setText(f"Files to Process ({count}):")
        self.clear_button.setEnabled(count > 0)
        self.remove_button.setEnabled(count > 0)
        self.files_changed.emit()
