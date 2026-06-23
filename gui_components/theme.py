"""
Theme Helpers
=============
Small utilities for adapting custom-drawn widgets to the system light/dark
color scheme. Standard Qt widgets follow the palette automatically; these
helpers cover the few places we draw our own colors.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def is_dark_mode() -> bool:
    """Return True if the application is currently using a dark color scheme."""
    app = QApplication.instance()
    if app is None:
        return False

    # Qt 6.5+: authoritative color-scheme hint.
    scheme = getattr(app.styleHints(), "colorScheme", None)
    if scheme is not None:
        try:
            return scheme() == Qt.ColorScheme.Dark
        except Exception:
            pass

    # Fallback: infer from how light the window background is.
    return app.palette().window().color().lightness() < 128
