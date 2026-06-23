"""
Drag-and-Drop Widget
=====================
Qt widget that accepts PDF file drops, with click-to-browse fallback.

Drag-and-drop is native to Qt, so (unlike the tkinter version) this needs no
optional third-party package.
"""

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout

from .settings import DIMENSIONS


class DragDropZone(QFrame):
    """Drop zone for PDF files. Emits ``files_added`` with a list of Paths."""

    files_added = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(DIMENSIONS["drop_zone_height"])
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        self.label = QLabel(
            "Drag & Drop PDF Files Here\n\nor click to browse"
        )
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self._apply_style(hover=False)

    # -- styling ---------------------------------------------------------
    def _apply_style(self, hover: bool):
        # Use palette roles so the zone follows the system light/dark theme.
        if hover:
            bg, fg, border = "palette(highlight)", "palette(highlighted-text)", "palette(highlight)"
        else:
            bg, fg, border = "palette(base)", "palette(text)", "palette(mid)"
        self.setStyleSheet(
            f"""
            DragDropZone {{
                background-color: {bg};
                border: 2px dashed {border};
                border-radius: 8px;
            }}
            QLabel {{
                color: {fg};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
            """
        )

    # -- drag-and-drop ---------------------------------------------------
    def dragEnterEvent(self, event):
        if self._has_pdf(event):
            event.acceptProposedAction()
            self._apply_style(hover=True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._apply_style(hover=False)

    def dropEvent(self, event):
        self._apply_style(hover=False)
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        pdfs = self._validate(paths)
        if pdfs:
            self.files_added.emit(pdfs)
            event.acceptProposedAction()

    # -- click to browse -------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select PDF Files", "", "PDF files (*.pdf);;All files (*.*)"
            )
            pdfs = self._validate(Path(f) for f in files)
            if pdfs:
                self.files_added.emit(pdfs)
        super().mousePressEvent(event)

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _has_pdf(event) -> bool:
        md = event.mimeData()
        if not md.hasUrls():
            return False
        return any(
            url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
            for url in md.urls()
        )

    @staticmethod
    def _validate(paths) -> List[Path]:
        return [
            p for p in paths
            if p.exists() and p.suffix.lower() == ".pdf"
        ]
