"""
Shared UI Primitives
====================
Small, reusable building blocks used across the app: cards, dividers, the
brand header bar, the collapsible "Details" disclosure, and custom-painted
icons. Keeping them here stops the same styling from being re-invented in each
screen.
"""

from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .style import SPACE, tokens


# -- labels --------------------------------------------------------------

def label(text: str, role: str = "body", parent=None) -> QLabel:
    """Create a QLabel tagged with a typography role from the stylesheet."""
    lbl = QLabel(text, parent)
    if role != "body":
        lbl.setProperty("role", role)
    return lbl


def pill(text: str, kind: str = "neutral") -> QLabel:
    """Create a small status pill label ('neutral'/'success'/'warning'/'error')."""
    lbl = QLabel(text)
    lbl.setProperty("pill", kind)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return lbl


def set_pill(lbl: QLabel, text: str, kind: str):
    """Update a pill's text and kind, re-polishing so the new style applies."""
    lbl.setText(text)
    lbl.setProperty("pill", kind)
    lbl.style().unpolish(lbl)
    lbl.style().polish(lbl)


# -- containers ----------------------------------------------------------

class Card(QFrame):
    """Elevated surface panel with a vertical layout."""

    def __init__(self, parent=None, variant: str = "true", padding: int = SPACE["lg"]):
        super().__init__(parent)
        self.setProperty("card", variant)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(SPACE["md"])


# -- header --------------------------------------------------------------

class HeaderBar(QFrame):
    """Brand bar: maize rule, app title, subtitle, and a trailing menu button."""

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(72)

        row = QHBoxLayout(self)
        row.setContentsMargins(SPACE["lg"], SPACE["md"], SPACE["lg"], SPACE["md"])
        row.setSpacing(SPACE["md"])

        rule = QFrame()
        rule.setObjectName("HeaderRule")
        rule.setFixedWidth(4)
        row.addWidget(rule)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("HeaderTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("HeaderSubtitle")
        text_col.addWidget(title_label)
        text_col.addWidget(subtitle_label)
        row.addLayout(text_col)
        row.addStretch()

        self.menu_button = QPushButton("Settings  ▾")
        self.menu_button.setObjectName("HeaderButton")
        self.menu_button.setCursor(Qt.PointingHandCursor)
        row.addWidget(self.menu_button)


# -- disclosure ----------------------------------------------------------

class CollapsibleSection(QWidget):
    """
    A "› Title" toggle that shows or hides a content widget.

    Used to keep the log out of a new user's way while leaving it one click
    away for anyone who needs it.
    """

    toggled = Signal(bool)

    def __init__(self, title: str, content: QWidget, expanded: bool = False, parent=None):
        super().__init__(parent)
        self._title = title
        self._content = content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE["sm"])

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(SPACE["sm"])

        self.toggle = QPushButton()
        self.toggle.setObjectName("DisclosureToggle")
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(expanded)
        self.toggle.clicked.connect(self._on_toggle)
        self.toggle.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        header.addWidget(self.toggle)

        self.badge = pill("", "neutral")
        self.badge.hide()
        header.addWidget(self.badge)
        header.addStretch()

        self.trailing = QHBoxLayout()
        self.trailing.setContentsMargins(0, 0, 0, 0)
        self.trailing.setSpacing(SPACE["xs"])
        header.addLayout(self.trailing)

        layout.addLayout(header)
        layout.addWidget(content)

        self._sync()

    # -- state -----------------------------------------------------------
    def _on_toggle(self):
        self._sync()
        self.toggled.emit(self.toggle.isChecked())

    def _sync(self):
        expanded = self.toggle.isChecked()
        self.toggle.setText(f"{'▾' if expanded else '▸'}  {self._title}")
        self._content.setVisible(expanded)

    def set_expanded(self, expanded: bool):
        """Programmatically open or close the section."""
        if self.toggle.isChecked() != expanded:
            self.toggle.setChecked(expanded)
            self._sync()

    def is_expanded(self) -> bool:
        """True when the content widget is visible."""
        return self.toggle.isChecked()

    def set_badge(self, text: str, kind: str = "neutral"):
        """Show a small pill next to the title, or hide it when text is empty."""
        if not text:
            self.badge.hide()
            return
        set_pill(self.badge, text, kind)
        self.badge.show()

    def add_trailing(self, widget: QWidget):
        """Add a control to the right-hand side of the disclosure header."""
        self.trailing.addWidget(widget)


# -- icons ---------------------------------------------------------------

class DropIcon(QWidget):
    """Custom-painted 'drop files here' glyph: an arrow falling into a tray."""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self._size = size
        self._accent = False
        self.setFixedSize(QSize(size, size))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_accent(self, accent: bool):
        """Highlight the glyph (used while a drag hovers the zone)."""
        if accent != self._accent:
            self._accent = accent
            self.update()

    def paintEvent(self, event):
        t = tokens()
        color = QColor(t["accent"] if self._accent else t["text_muted"])

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(color)
        pen.setWidthF(max(2.0, self._size * 0.045))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)

        s = self._size
        cx = s / 2

        # Downward arrow.
        p.drawLine(QPointF(cx, s * 0.14), QPointF(cx, s * 0.56))
        p.drawLine(QPointF(cx - s * 0.15, s * 0.41), QPointF(cx, s * 0.57))
        p.drawLine(QPointF(cx + s * 0.15, s * 0.41), QPointF(cx, s * 0.57))

        # Tray the arrow falls into.
        p.drawLine(QPointF(s * 0.16, s * 0.62), QPointF(s * 0.16, s * 0.84))
        p.drawLine(QPointF(s * 0.16, s * 0.84), QPointF(s * 0.84, s * 0.84))
        p.drawLine(QPointF(s * 0.84, s * 0.84), QPointF(s * 0.84, s * 0.62))
        p.end()


class OutcomeIcon(QWidget):
    """
    Large run-outcome glyph inside a ring: a check (success), an exclamation
    (finished with issues), a cross (nothing produced), or a square (stopped).
    """

    SUCCESS, ISSUES, FAILURE, STOPPED = "success", "issues", "failure", "stopped"

    def __init__(self, size: int = 46, parent=None):
        super().__init__(parent)
        self._size = size
        self._state = self.SUCCESS
        self.setFixedSize(QSize(size, size))

    def set_state(self, state: str):
        """Set which outcome the icon depicts."""
        self._state = state
        self.update()

    def paintEvent(self, event):
        t = tokens()
        color = QColor(
            {
                self.SUCCESS: t["success"],
                self.ISSUES: t["warning"],
                self.FAILURE: t["error"],
                self.STOPPED: t["text_muted"],
            }[self._state]
        )

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(color)
        pen.setWidthF(max(2.0, self._size * 0.055))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)

        s = self._size
        inset = pen.widthF()
        p.drawEllipse(QPointF(s / 2, s / 2), s / 2 - inset, s / 2 - inset)

        if self._state == self.SUCCESS:
            p.drawLine(QPointF(s * 0.29, s * 0.52), QPointF(s * 0.44, s * 0.67))
            p.drawLine(QPointF(s * 0.44, s * 0.67), QPointF(s * 0.72, s * 0.35))
        elif self._state == self.ISSUES:
            p.drawLine(QPointF(s / 2, s * 0.28), QPointF(s / 2, s * 0.58))
            p.drawLine(QPointF(s / 2, s * 0.71), QPointF(s / 2, s * 0.72))
        elif self._state == self.FAILURE:
            p.drawLine(QPointF(s * 0.34, s * 0.34), QPointF(s * 0.66, s * 0.66))
            p.drawLine(QPointF(s * 0.66, s * 0.34), QPointF(s * 0.34, s * 0.66))
        else:  # STOPPED
            p.drawLine(QPointF(s * 0.41, s * 0.36), QPointF(s * 0.41, s * 0.64))
            p.drawLine(QPointF(s * 0.59, s * 0.36), QPointF(s * 0.59, s * 0.64))
        p.end()


class FileGlyph(QWidget):
    """Small painted page-with-folded-corner icon for file rows."""

    def __init__(self, size: int = 20, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        t = tokens()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(t["text_faint"]))
        pen.setWidthF(1.4)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)

        s = self._size
        fold = s * 0.3
        # Page outline with the top-right corner cut off.
        points = [
            QPointF(s * 0.18, s * 0.1),
            QPointF(s * 0.68, s * 0.1),
            QPointF(s * 0.82, s * 0.1 + fold),
            QPointF(s * 0.82, s * 0.9),
            QPointF(s * 0.18, s * 0.9),
        ]
        for i in range(len(points)):
            p.drawLine(points[i], points[(i + 1) % len(points)])
        # The fold.
        p.drawLine(QPointF(s * 0.68, s * 0.1), QPointF(s * 0.68, s * 0.1 + fold))
        p.drawLine(QPointF(s * 0.68, s * 0.1 + fold), QPointF(s * 0.82, s * 0.1 + fold))
        p.end()


class StatusGlyph(QWidget):
    """
    Per-file state indicator: a hollow dot (queued), a spinning arc (running),
    a check (done), or a cross (failed).
    """

    QUEUED, RUNNING, DONE, FAILED, SKIPPED = "queued", "running", "done", "failed", "skipped"

    def __init__(self, size: int = 18, parent=None):
        super().__init__(parent)
        self._size = size
        self._state = self.QUEUED
        self._angle = 0
        self.setFixedSize(QSize(size, size))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_state(self, state: str):
        """Set the indicator state (one of the class constants)."""
        self._state = state
        self.update()

    def advance(self):
        """Step the spinner animation; only repaints while running."""
        if self._state == self.RUNNING:
            self._angle = (self._angle + 30) % 360
            self.update()

    def paintEvent(self, event):
        t = tokens()
        colors = {
            self.QUEUED: t["text_faint"],
            self.RUNNING: t["focus"],
            self.DONE: t["success"],
            self.FAILED: t["error"],
            self.SKIPPED: t["warning"],
        }
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(colors[self._state]))
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)

        s = self._size
        r = s / 2 - 2

        if self._state == self.RUNNING:
            # 270-degree arc, rotated on each tick. Qt angles are 1/16 degree.
            p.drawArc(2, 2, int(r * 2), int(r * 2), -self._angle * 16, 270 * 16)
        elif self._state == self.DONE:
            p.drawLine(QPointF(s * 0.22, s * 0.52), QPointF(s * 0.42, s * 0.72))
            p.drawLine(QPointF(s * 0.42, s * 0.72), QPointF(s * 0.78, s * 0.28))
        elif self._state == self.FAILED:
            p.drawLine(QPointF(s * 0.28, s * 0.28), QPointF(s * 0.72, s * 0.72))
            p.drawLine(QPointF(s * 0.72, s * 0.28), QPointF(s * 0.28, s * 0.72))
        elif self._state == self.SKIPPED:
            p.drawEllipse(QPointF(s / 2, s / 2), r, r)
            p.drawLine(QPointF(s / 2, s * 0.28), QPointF(s / 2, s * 0.56))
            p.drawPoint(QPointF(s / 2, s * 0.72))
        else:
            p.drawEllipse(QPointF(s / 2, s / 2), r, r)
        p.end()
