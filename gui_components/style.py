"""
Visual Design System
====================
Design tokens and the application stylesheet.

The app ships its own light and dark palettes rather than inheriting the raw
system theme, so it looks identical on every machine while still flipping with
the OS color scheme. Colors are built on the UM-Dearborn identity: Michigan
Blue as the brand surface, Maize as the single accent reserved for the primary
action.

Usage:
    from .style import apply_theme
    apply_theme(app)          # sets Fusion style, palette, and stylesheet
    T = tokens()              # current color tokens, for custom-painted widgets
"""

import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication

from .theme import is_dark_mode

# -- color tokens --------------------------------------------------------

LIGHT = {
    "bg": "#EDF1F5",
    "surface": "#FFFFFF",
    "surface_alt": "#F5F8FA",
    "surface_sunken": "#E8EDF2",
    "border": "#D3DDE7",
    "border_strong": "#B4C3D2",
    "text": "#0F2033",
    "text_muted": "#5A6B7D",
    "text_faint": "#8494A5",
    "brand": "#00274C",
    "brand_alt": "#013A6B",
    "on_brand": "#FFFFFF",
    "on_brand_muted": "#A9C2DA",
    "accent": "#FFCB05",
    "accent_hover": "#FFD633",
    "accent_press": "#E3B400",
    "on_accent": "#00274C",
    "success": "#177245",
    "success_bg": "#E4F3EA",
    "warning": "#A65A00",
    "warning_bg": "#FBF0DF",
    "error": "#B5321F",
    "error_bg": "#FBE9E6",
    "info": "#1E5A94",
    "focus": "#2F6FB0",
    "selection": "#DBE8F6",
    "shadow": "#C3CFDB",
}

DARK = {
    "bg": "#0E141C",
    "surface": "#18212C",
    "surface_alt": "#1F2A37",
    "surface_sunken": "#111923",
    "border": "#2B3846",
    "border_strong": "#3D4E60",
    "text": "#E7EDF4",
    "text_muted": "#9BAABB",
    "text_faint": "#71818F",
    "brand": "#0B2B4D",
    "brand_alt": "#1C4C7C",
    "on_brand": "#F2F7FC",
    "on_brand_muted": "#8FAAC6",
    "accent": "#FFCB05",
    "accent_hover": "#FFD84A",
    "accent_press": "#D9AC00",
    "on_accent": "#10192A",
    "success": "#4ADE9B",
    "success_bg": "#12301F",
    "warning": "#F0B45C",
    "warning_bg": "#33240E",
    "error": "#FF7A66",
    "error_bg": "#331812",
    "info": "#79B4F0",
    "focus": "#5FA0E0",
    "selection": "#1D3550",
    "shadow": "#05090E",
}

# -- spacing / type scale ------------------------------------------------

SPACE = {"xs": 4, "sm": 8, "md": 14, "lg": 20, "xl": 28, "xxl": 40}

RADIUS = {"sm": 4, "md": 8, "lg": 12, "xl": 16}

FONT_STACK = '"Segoe UI Variable Text", "Segoe UI", "Inter", system-ui, sans-serif'
FONT_STACK_DISPLAY = '"Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI", sans-serif'
FONT_STACK_MONO = '"Cascadia Mono", "Consolas", "SF Mono", monospace'

# Point sizes (Qt stylesheets scale these with the display DPI).
TYPE = {
    "display": 22,
    "title": 15,
    "subtitle": 12,
    "body": 10,
    "small": 9,
    "micro": 8,
}


# The scheme the app is actually running in. ``apply_theme`` owns this; custom
# widgets must read it rather than re-asking the OS, or a forced light/dark run
# ends up with half the UI painted from the other palette.
_ACTIVE_DARK = None


def tokens(dark: bool = None) -> dict:
    """Return the color tokens for the active (or explicitly requested) scheme."""
    if dark is None:
        dark = _ACTIVE_DARK if _ACTIVE_DARK is not None else is_dark_mode()
    return DARK if dark else LIGHT


def active_dark() -> bool:
    """True when the app is currently themed dark."""
    return _ACTIVE_DARK if _ACTIVE_DARK is not None else is_dark_mode()


# -- palette -------------------------------------------------------------

def build_palette(dark: bool) -> QPalette:
    """Base QPalette so unstyled/native-drawn widgets match the theme."""
    t = tokens(dark)
    p = QPalette()
    p.setColor(QPalette.Window, QColor(t["bg"]))
    p.setColor(QPalette.WindowText, QColor(t["text"]))
    p.setColor(QPalette.Base, QColor(t["surface"]))
    p.setColor(QPalette.AlternateBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.Text, QColor(t["text"]))
    p.setColor(QPalette.PlaceholderText, QColor(t["text_faint"]))
    p.setColor(QPalette.Button, QColor(t["surface"]))
    p.setColor(QPalette.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.Highlight, QColor(t["focus"]))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.ToolTipBase, QColor(t["surface"]))
    p.setColor(QPalette.ToolTipText, QColor(t["text"]))
    p.setColor(QPalette.Link, QColor(t["info"]))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(t["text_faint"]))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(t["text_faint"]))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(t["text_faint"]))
    return p


# -- stylesheet ----------------------------------------------------------

def _checkmark_url() -> str:
    """
    Render a white checkmark to a PNG and return it as a stylesheet ``url()``.

    Qt stylesheets can only point ``image:`` at a real file, and a styled
    ``::indicator`` loses the platform style's built-in tick — so we draw our
    own once and cache it beside the other temp files.
    """
    path = Path(tempfile.gettempdir()) / "srp_checkmark_16.png"
    if not path.exists():
        try:
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor("#FFFFFF"))
            pen.setWidthF(2.2)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QPointF(3.5, 8.4), QPointF(6.6, 11.5))
            painter.drawLine(QPointF(6.6, 11.5), QPointF(12.5, 4.8))
            painter.end()
            pixmap.save(str(path), "PNG")
        except Exception:
            return ""
    return path.as_posix()


def build_stylesheet(dark: bool) -> str:
    """Return the full application stylesheet for the given color scheme."""
    t = tokens(dark)
    check = _checkmark_url()
    check_image = f"image: url({check});" if check else ""
    return f"""
/* ---------- base ---------- */
QWidget {{
    font-family: {FONT_STACK};
    font-size: {TYPE["body"]}pt;
    color: {t["text"]};
}}
QMainWindow, QDialog {{
    background: {t["bg"]};
}}

/* ---------- typography roles ---------- */
QLabel[role="display"] {{
    font-family: {FONT_STACK_DISPLAY};
    font-size: {TYPE["display"]}pt;
    font-weight: 600;
    color: {t["text"]};
}}
QLabel[role="title"] {{
    font-family: {FONT_STACK_DISPLAY};
    font-size: {TYPE["title"]}pt;
    font-weight: 600;
    color: {t["text"]};
}}
QLabel[role="subtitle"] {{
    font-size: {TYPE["subtitle"]}pt;
    color: {t["text_muted"]};
}}
QLabel[role="muted"] {{
    font-size: {TYPE["small"]}pt;
    color: {t["text_muted"]};
}}
QLabel[role="faint"] {{
    font-size: {TYPE["small"]}pt;
    color: {t["text_faint"]};
}}
QLabel[role="eyebrow"] {{
    font-size: {TYPE["micro"]}pt;
    font-weight: 700;
    color: {t["text_faint"]};
    letter-spacing: 1px;
}}
QLabel[role="metric"] {{
    font-family: {FONT_STACK_DISPLAY};
    font-size: {TYPE["display"]}pt;
    font-weight: 700;
    color: {t["text"]};
}}

/* ---------- header bar ---------- */
#HeaderBar {{
    background: {t["brand"]};
    border: none;
}}
#HeaderRule {{
    background: {t["accent"]};
    border-radius: 2px;
}}
#HeaderTitle {{
    font-family: {FONT_STACK_DISPLAY};
    font-size: {TYPE["title"]}pt;
    font-weight: 600;
    color: {t["on_brand"]};
}}
#HeaderSubtitle {{
    font-size: {TYPE["small"]}pt;
    color: {t["on_brand_muted"]};
}}
#HeaderButton {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: {RADIUS["md"]}px;
    color: {t["on_brand"]};
    padding: 6px 12px;
    font-size: {TYPE["small"]}pt;
}}
#HeaderButton:hover {{
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.4);
}}
#HeaderButton:pressed {{
    background: rgba(0, 0, 0, 0.18);
}}
#HeaderButton::menu-indicator {{
    image: none;
    width: 0;
}}

#StepBadge {{
    background: {t["accent"]};
    color: {t["on_accent"]};
    border-radius: 10px;
    font-weight: 700;
    font-size: {TYPE["micro"]}pt;
}}

/* ---------- cards ---------- */
QFrame[card="true"] {{
    background: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["lg"]}px;
}}
QFrame[card="sunken"] {{
    background: {t["surface_alt"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["md"]}px;
}}
#Divider {{
    background: {t["border"]};
    border: none;
}}

/* ---------- buttons ---------- */
QPushButton {{
    background: {t["surface"]};
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["md"]}px;
    padding: 8px 16px;
    color: {t["text"]};
}}
QPushButton:hover {{
    background: {t["surface_alt"]};
    border-color: {t["focus"]};
}}
QPushButton:pressed {{
    background: {t["surface_sunken"]};
}}
QPushButton:disabled {{
    background: {t["surface_alt"]};
    border-color: {t["border"]};
    color: {t["text_faint"]};
}}
QPushButton:focus {{
    outline: none;
    border-color: {t["focus"]};
}}

QPushButton[variant="primary"] {{
    background: {t["accent"]};
    border: 1px solid {t["accent_press"]};
    color: {t["on_accent"]};
    font-family: {FONT_STACK_DISPLAY};
    font-size: {TYPE["subtitle"]}pt;
    font-weight: 600;
    padding: 13px 26px;
    border-radius: {RADIUS["md"]}px;
}}
QPushButton[variant="primary"]:hover {{
    background: {t["accent_hover"]};
}}
QPushButton[variant="primary"]:pressed {{
    background: {t["accent_press"]};
}}
QPushButton[variant="primary"]:disabled {{
    background: {t["surface_alt"]};
    border-color: {t["border"]};
    color: {t["text_faint"]};
}}

QPushButton[variant="secondary"] {{
    background: {t["brand_alt"]};
    border: 1px solid {t["brand_alt"]};
    color: {t["on_brand"]};
    font-weight: 600;
    padding: 10px 18px;
}}
QPushButton[variant="secondary"]:hover {{
    background: {t["brand"]};
    border-color: {t["focus"]};
}}
QPushButton[variant="secondary"]:pressed {{
    background: {t["brand"]};
}}

QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {t["text_muted"]};
    padding: 6px 10px;
    font-size: {TYPE["small"]}pt;
}}
QPushButton[variant="ghost"]:hover {{
    background: {t["surface_alt"]};
    border-color: {t["border"]};
    color: {t["text"]};
}}

QPushButton[variant="quiet"] {{
    padding: 7px 14px;
    font-size: {TYPE["small"]}pt;
}}

QPushButton[variant="icon"] {{
    background: transparent;
    border: none;
    border-radius: {RADIUS["sm"]}px;
    color: {t["text_faint"]};
    padding: 2px;
    font-size: {TYPE["subtitle"]}pt;
}}
QPushButton[variant="icon"]:hover {{
    background: {t["error_bg"]};
    color: {t["error"]};
}}

/* ---------- format toggles (segmented) ---------- */
QPushButton[variant="toggle"] {{
    background: {t["surface"]};
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["md"]}px;
    padding: 8px 18px;
    color: {t["text_muted"]};
    font-size: {TYPE["small"]}pt;
    font-weight: 600;
}}
QPushButton[variant="toggle"]:hover {{
    border-color: {t["focus"]};
    color: {t["text"]};
}}
QPushButton[variant="toggle"]:checked {{
    background: {t["selection"]};
    border-color: {t["focus"]};
    color: {t["text"]};
}}

/* ---------- inputs ---------- */
QLineEdit {{
    background: {t["surface"]};
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["md"]}px;
    padding: 8px 12px;
    selection-background-color: {t["focus"]};
    selection-color: #FFFFFF;
}}
QLineEdit:focus {{
    border-color: {t["focus"]};
}}
QLineEdit:read-only {{
    background: {t["surface_alt"]};
    color: {t["text_muted"]};
}}

QComboBox {{
    background: {t["surface"]};
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["md"]}px;
    padding: 7px 12px;
    min-width: 140px;
}}
QComboBox:hover {{ border-color: {t["focus"]}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["md"]}px;
    selection-background-color: {t["selection"]};
    selection-color: {t["text"]};
    padding: 4px;
    outline: none;
}}

QCheckBox {{
    spacing: 9px;
    color: {t["text"]};
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["sm"]}px;
    background: {t["surface"]};
}}
QCheckBox::indicator:hover {{ border-color: {t["focus"]}; }}
QCheckBox::indicator:checked {{
    background: {t["focus"]};
    border-color: {t["focus"]};
    {check_image}
}}
QCheckBox::indicator:disabled {{
    background: {t["surface_alt"]};
    border-color: {t["border"]};
}}

/* ---------- lists ---------- */
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    border: none;
    padding: 0px;
    margin: 0px 0px 6px 0px;
}}
QListWidget::item:selected {{ background: transparent; }}

QListWidget[variant="plain"] {{
    background: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["md"]}px;
    padding: 4px;
}}
QListWidget[variant="plain"]::item {{
    padding: 7px 10px;
    margin: 1px 0px;
    border-radius: {RADIUS["sm"]}px;
    color: {t["text"]};
}}
QListWidget[variant="plain"]::item:hover {{ background: {t["surface_alt"]}; }}
QListWidget[variant="plain"]::item:selected {{
    background: {t["selection"]};
    color: {t["text"]};
}}
QListWidget[variant="plain"]::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {t["border_strong"]};
    border-radius: {RADIUS["sm"]}px;
    background: {t["surface"]};
    margin-right: 4px;
}}
QListWidget[variant="plain"]::indicator:hover {{ border-color: {t["focus"]}; }}
QListWidget[variant="plain"]::indicator:checked {{
    background: {t["focus"]};
    border-color: {t["focus"]};
    {check_image}
}}

/* ---------- progress ---------- */
QProgressBar {{
    background: {t["surface_sunken"]};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {t["accent"]};
    border-radius: 5px;
}}

/* ---------- log ---------- */
#LogPanel {{
    background: {t["surface_sunken"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["md"]}px;
    font-family: {FONT_STACK_MONO};
    font-size: {TYPE["small"]}pt;
    color: {t["text_muted"]};
    padding: 8px;
}}

/* ---------- disclosure ---------- */
#DisclosureToggle {{
    background: transparent;
    border: none;
    color: {t["text_muted"]};
    font-size: {TYPE["small"]}pt;
    font-weight: 600;
    padding: 6px 4px;
    text-align: left;
}}
#DisclosureToggle:hover {{ color: {t["text"]}; }}

/* ---------- status pills ---------- */
QLabel[pill="neutral"] {{
    background: {t["surface_alt"]};
    color: {t["text_muted"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["sm"]}px;
    padding: 2px 8px;
    font-size: {TYPE["micro"]}pt;
    font-weight: 700;
}}
QLabel[pill="success"] {{
    background: {t["success_bg"]};
    color: {t["success"]};
    border: 1px solid {t["success"]};
    border-radius: {RADIUS["sm"]}px;
    padding: 2px 8px;
    font-size: {TYPE["micro"]}pt;
    font-weight: 700;
}}
QLabel[pill="warning"] {{
    background: {t["warning_bg"]};
    color: {t["warning"]};
    border: 1px solid {t["warning"]};
    border-radius: {RADIUS["sm"]}px;
    padding: 2px 8px;
    font-size: {TYPE["micro"]}pt;
    font-weight: 700;
}}
QLabel[pill="error"] {{
    background: {t["error_bg"]};
    color: {t["error"]};
    border: 1px solid {t["error"]};
    border-radius: {RADIUS["sm"]}px;
    padding: 2px 8px;
    font-size: {TYPE["micro"]}pt;
    font-weight: 700;
}}

/* ---------- menus ---------- */
QMenu {{
    background: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: {RADIUS["md"]}px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 26px 7px 26px;
    border-radius: {RADIUS["sm"]}px;
    color: {t["text"]};
}}
QMenu::item:selected {{ background: {t["selection"]}; }}
QMenu::item:disabled {{ color: {t["text_faint"]}; }}
QMenu::separator {{
    height: 1px;
    background: {t["border"]};
    margin: 6px 8px;
}}
QMenu::indicator {{
    width: 14px;
    height: 14px;
    left: 8px;
}}

/* ---------- tooltips ---------- */
QToolTip {{
    background: {t["brand"]};
    color: {t["on_brand"]};
    border: none;
    border-radius: {RADIUS["sm"]}px;
    padding: 5px 9px;
    font-size: {TYPE["small"]}pt;
}}

/* ---------- scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 11px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {t["border_strong"]};
    border-radius: 4px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {t["text_faint"]}; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 11px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {t["border_strong"]};
    border-radius: 4px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {t["text_faint"]}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------- scroll areas ---------- */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ---------- message boxes ---------- */
QMessageBox {{ background: {t["surface"]}; }}
QMessageBox QLabel {{ color: {t["text"]}; }}
QMessageBox QPushButton {{ min-width: 84px; }}
"""


def apply_theme(app: QApplication, dark: bool = None) -> bool:
    """
    Apply the Fusion base style, palette, and stylesheet to the application.

    Args:
        app: The QApplication instance.
        dark: Force a color scheme; ``None`` follows the OS.

    Returns:
        True if the dark scheme was applied.
    """
    global _ACTIVE_DARK
    if dark is None:
        dark = is_dark_mode()
    _ACTIVE_DARK = dark
    app.setStyle("Fusion")
    app.setPalette(build_palette(dark))
    app.setStyleSheet(build_stylesheet(dark))

    font = QFont()
    for family in ("Segoe UI Variable Text", "Segoe UI", "Inter"):
        font.setFamily(family)
        if QFont(family).exactMatch():
            break
    font.setPointSize(TYPE["body"])
    app.setFont(font)
    return dark
