"""
Custom Logging Handler for GUI
================================
Redirects logging output to a tkinter Text widget with color coding.
"""

import logging
from tkinter import scrolledtext


class TextHandler(logging.Handler):
    """
    Custom logging handler that writes to a tkinter ScrolledText widget.

    Features:
    - Thread-safe updates using widget.after()
    - Color-coded messages by log level
    - Auto-scroll to bottom
    - Optional line limit to prevent memory issues
    """

    def __init__(self, text_widget: scrolledtext.ScrolledText, max_lines: int = 1000):
        """
        Initialize the text handler.

        Args:
            text_widget: ScrolledText widget to write logs to
            max_lines: Maximum number of lines to keep (prevents memory bloat)
        """
        super().__init__()
        self.text_widget = text_widget
        self.max_lines = max_lines

        # Configure widget as read-only
        self.text_widget.config(state="disabled")

        # Configure color tags
        self.text_widget.tag_config("DEBUG", foreground="gray")
        self.text_widget.tag_config("INFO", foreground="black")
        self.text_widget.tag_config("WARNING", foreground="orange")
        self.text_widget.tag_config("ERROR", foreground="red")
        self.text_widget.tag_config("CRITICAL", foreground="red", font=("Arial", 10, "bold"))

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the text widget.

        Args:
            record: LogRecord to display
        """
        try:
            msg = self.format(record)
            tag = record.levelname

            # Schedule UI update on main thread
            self.text_widget.after(0, lambda: self._append_text(msg, tag))
        except Exception:
            self.handleError(record)

    def _append_text(self, message: str, tag: str):
        """
        Append text to the widget (must run on main thread).

        Args:
            message: Message to append
            tag: Tag name for styling (log level)
        """
        # Enable editing
        self.text_widget.config(state="normal")

        # Append message
        self.text_widget.insert("end", message + "\n", tag)

        # Trim old lines if needed
        line_count = int(self.text_widget.index("end-1c").split(".")[0])
        if line_count > self.max_lines:
            self.text_widget.delete("1.0", f"{line_count - self.max_lines}.0")

        # Auto-scroll to bottom
        self.text_widget.see("end")

        # Disable editing
        self.text_widget.config(state="disabled")

    def clear(self):
        """Clear all text from the widget."""
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.config(state="disabled")
