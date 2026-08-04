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

from .style import tokens


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
    """
    Read-only, auto-scrolling, color-coded log display.

    Tracks how many warnings and errors have been seen so the surrounding UI
    can surface a badge without the panel being open.
    """

    counts_changed = Signal(int, int)  # (warnings, errors)

    def __init__(self, max_lines: int = 1000, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPanel")
        self.max_lines = max_lines
        self.warning_count = 0
        self.error_count = 0
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setPlaceholderText("Processing details will appear here.")

    def append_record(self, message: str, level: str):
        """Append one colored line (connected to QtLogHandler.message)."""
        if level == "WARNING":
            self.warning_count += 1
            self.counts_changed.emit(self.warning_count, self.error_count)
        elif level in ("ERROR", "CRITICAL"):
            self.error_count += 1
            self.counts_changed.emit(self.warning_count, self.error_count)

        safe = html.escape(message)
        color = self._level_color(level)
        if color:
            weight = "bold" if level == "CRITICAL" else "normal"
            self.appendHtml(
                f'<span style="color:{color}; font-weight:{weight};">{safe}</span>'
            )
        else:
            self.appendHtml(safe)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    @staticmethod
    def _level_color(level: str):
        """Theme-aware color per level, or None to use the default text color."""
        t = tokens()
        if level in ("ERROR", "CRITICAL"):
            return t["error"]
        if level == "WARNING":
            return t["warning"]
        if level == "DEBUG":
            return t["text_faint"]
        return None  # INFO inherits the panel's own color

    def clear_log(self):
        """Clear all text and reset the warning/error counters."""
        self.clear()
        self.warning_count = 0
        self.error_count = 0
        self.counts_changed.emit(0, 0)
