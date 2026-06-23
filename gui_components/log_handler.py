"""
Logging Bridge for the Qt GUI
=============================
Routes Python logging records to a QPlainTextEdit with color coding.

A logging.Handler cannot safely touch widgets from a worker thread, so the
handler only emits a Qt signal. Qt delivers queued signals on the GUI thread,
which makes the cross-thread hand-off safe.
"""

import html
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPlainTextEdit

from .theme import is_dark_mode


class QtLogHandler(logging.Handler, QObject):
    """Logging handler that re-emits formatted records as a Qt signal."""

    message = Signal(str, str)  # (formatted message, level name)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.message.emit(msg, record.levelname)
        except Exception:
            self.handleError(record)


class LogPanel(QPlainTextEdit):
    """Read-only, auto-scrolling, color-coded log display."""

    def __init__(self, max_lines: int = 1000, parent=None):
        super().__init__(parent)
        self.max_lines = max_lines
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        # Follow the system theme for background/default text.
        self.setStyleSheet(
            "QPlainTextEdit { background: palette(base); color: palette(text); }"
        )

    def append_record(self, message: str, level: str):
        """Append one colored line (connected to QtLogHandler.message)."""
        safe = html.escape(message)
        color = self._level_color(level)
        if color:
            weight = "bold" if level == "CRITICAL" else "normal"
            self.appendHtml(
                f'<span style="color:{color}; font-weight:{weight};">{safe}</span>'
            )
        else:
            # INFO: inherit the palette text color so it reads on light or dark.
            self.appendHtml(safe)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    @staticmethod
    def _level_color(level: str):
        """Theme-aware color per level, or None to use the default text color."""
        dark = is_dark_mode()
        if level in ("ERROR", "CRITICAL"):
            return "#ef5350" if dark else "#c62828"
        if level == "WARNING":
            return "#ffb74d" if dark else "#e65100"
        if level == "DEBUG":
            return "#9e9e9e" if dark else "#6d6d6d"
        return None  # INFO

    def clear_log(self):
        """Clear all text from the panel."""
        self.clear()
