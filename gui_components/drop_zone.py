"""
Drag-and-Drop Widget
=====================
Qt widget that accepts PDF file drops, with click-to-browse fallback.

Two presentations share one implementation:

- ``hero``    — the large, inviting target shown when nothing is queued yet
- ``compact`` — a slim "add more" strip shown once files are in the queue
"""

from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from .settings import DIMENSIONS
from .style import RADIUS, SPACE, TYPE, tokens
from .widgets import DropIcon


class DragDropZone(QFrame):
    """
    Drop target for PDF files.

    Signals:
        files_added: list[Path] of accepted PDFs
        files_rejected: list[Path] of dropped files that were not PDFs
    """

    files_added = Signal(list)
    files_rejected = Signal(list)

    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self._hover = False

        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.NoFrame)

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_text)

        self._build_ui()
        self.refresh_style()

    # -- UI --------------------------------------------------------------
    def _build_ui(self):
        if self.compact:
            self.setFixedHeight(DIMENSIONS["drop_zone_compact_height"])
            layout = QHBoxLayout(self)
            layout.setContentsMargins(SPACE["md"], 0, SPACE["md"], 0)
            layout.setSpacing(SPACE["md"])
            layout.addStretch()
            self.icon = DropIcon(22)
            layout.addWidget(self.icon)
            self.title = QLabel(self._default_title())
            layout.addWidget(self.title)
            layout.addStretch()
            self.subtitle = None
        else:
            self.setMinimumHeight(DIMENSIONS["drop_zone_height"])
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(SPACE["lg"], SPACE["xl"], SPACE["lg"], SPACE["xl"])
            layout.setSpacing(SPACE["sm"])
            layout.addStretch()

            icon_row = QHBoxLayout()
            icon_row.addStretch()
            self.icon = DropIcon(64)
            icon_row.addWidget(self.icon)
            icon_row.addStretch()
            layout.addLayout(icon_row)
            layout.addSpacing(SPACE["sm"])

            self.title = QLabel(self._default_title())
            self.title.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.title)

            self.subtitle = QLabel("or click anywhere in this box to browse")
            self.subtitle.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.subtitle)
            layout.addStretch()

    def _default_title(self) -> str:
        return "Add more PDFs" if self.compact else "Drop your Daily Setup Report PDFs here"

    # -- styling ---------------------------------------------------------
    def refresh_style(self):
        """(Re)apply theme colors. Call after the OS color scheme changes."""
        t = tokens()
        if self._hover:
            bg, border = t["selection"], t["focus"]
            title_color = t["text"]
        else:
            bg, border = t["surface"], t["border_strong"]
            title_color = t["text"] if not self.compact else t["text_muted"]

        title_size = TYPE["small"] if self.compact else TYPE["title"]
        radius = RADIUS["md"] if self.compact else RADIUS["lg"]
        self.setStyleSheet(
            f"""
            DragDropZone {{
                background-color: {bg};
                border: 2px dashed {border};
                border-radius: {radius}px;
            }}
            DragDropZone QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )
        self.title.setStyleSheet(
            f"color: {title_color}; font-size: {title_size}pt; font-weight: 600;"
        )
        if self.subtitle is not None:
            self.subtitle.setStyleSheet(
                f"color: {t['text_muted']}; font-size: {TYPE['subtitle']}pt;"
            )
        self.icon.set_accent(self._hover)

    def _set_hover(self, hover: bool):
        if hover != self._hover:
            self._hover = hover
            self.refresh_style()

    # -- transient messaging ---------------------------------------------
    def _flash(self, message: str):
        """Briefly replace the title with a message, then restore it."""
        self.title.setText(message)
        self._reset_timer.start(2600)

    def _reset_text(self):
        self.title.setText(self._default_title())

    # -- drag-and-drop ---------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_hover(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_hover(False)

    def dropEvent(self, event):
        self._set_hover(False)
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        self.handle_paths(paths)
        event.acceptProposedAction()

    # -- click to browse -------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Daily Setup Report PDFs", "",
                "PDF files (*.pdf);;All files (*.*)",
            )
            self.handle_paths([Path(f) for f in files])
        super().mousePressEvent(event)

    # -- helpers ---------------------------------------------------------
    def handle_paths(self, paths: List[Path]):
        """Split paths into PDFs and rejects, then emit the matching signals."""
        pdfs, rejected = self._partition(paths)
        if pdfs:
            self.files_added.emit(pdfs)
        if rejected:
            self.files_rejected.emit(rejected)
            self._flash(
                "Only PDF files can be processed"
                if not pdfs
                else f"Skipped {len(rejected)} non-PDF file(s)"
            )

    @staticmethod
    def _partition(paths) -> Tuple[List[Path], List[Path]]:
        pdfs, rejected = [], []
        for p in paths:
            if p.is_file() and p.suffix.lower() == ".pdf":
                pdfs.append(p)
            else:
                rejected.append(p)
        return pdfs, rejected
