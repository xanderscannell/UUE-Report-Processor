"""
Event Details Popup
===================
Opened by clicking a bar on the timeline. The bar and its hover card show the
name, room and times; this shows everything else the source carried for that
event: the row's ``Details`` and, for 25Live, its ``Resources`` (see
``create_gantt_rows``).

What is in either is decided by each reader's allowlist, so no contact details
ever reach this dialog (ADR-013).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .style import SPACE
from .widgets import Card, label

# Wide enough for a reference number on one line, narrow enough that long room
# instructions wrap into a readable column.
DIALOG_WIDTH = 460

# A big event's resource list can run long; past this share of the screen the
# body scrolls instead of the dialog growing off the bottom.
MAX_SCREEN_SHARE = 0.85


def _value(text: str, role: str = "body"):
    """A wrapped, selectable label, so a reference can be copied into 25Live."""
    widget = label(text, role)
    widget.setWordWrap(True)
    widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return widget


class EventDetailsDialog(QDialog):
    """Shows one timeline event's full details."""

    def __init__(self, row: dict, times: str, date: str, parent=None):
        """
        Args:
            row: The gantt row behind the clicked bar
            times: The bar's formatted time range, as printed on the bar
            date: The event's day, already formatted for reading
        """
        super().__init__(parent)
        name = row.get("EventName") or "Event"
        self.setWindowTitle(name)
        self.setFixedWidth(DIALOG_WIDTH)
        self._build_ui(name, row, times, date)
        self._fit_height()

    def _build_ui(self, name: str, row: dict, times: str, date: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        layout.setSpacing(SPACE["md"])

        heading = QVBoxLayout()
        heading.setSpacing(SPACE["xs"])
        title = label(name, "title")
        title.setWordWrap(True)
        heading.addWidget(title)
        summary = " · ".join(part for part in (row.get("Location"), date, times) if part)
        sub = label(summary, "muted")
        sub.setWordWrap(True)
        heading.addWidget(sub)
        layout.addLayout(heading)

        # Everything between the heading and Close scrolls as one body.
        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(SPACE["md"])

        details = row.get("Details") or {}
        resources = row.get("Resources") or []
        if details:
            card = Card(padding=SPACE["md"])
            form = QFormLayout()
            form.setHorizontalSpacing(SPACE["md"])
            form.setVerticalSpacing(SPACE["sm"])
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
            for key, value in details.items():
                form.addRow(label(key, "muted"), _value(value))
            card.body.addLayout(form)
            self._body_layout.addWidget(card)
        if resources:
            self._body_layout.addWidget(self._resources_card(resources))
        if not details and not resources:
            note = label("This report carries no further details for this event.", "faint")
            note.setWordWrap(True)
            self._body_layout.addWidget(note)

        self._scroll = QScrollArea()
        self._scroll.setWidget(body)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self._scroll)

        bottom = QHBoxLayout()
        bottom.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setProperty("variant", "secondary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    @staticmethod
    def _resources_card(resources: list) -> Card:
        """One entry per resource: quantity and name, then its instructions."""
        card = Card(padding=SPACE["md"])
        card.body.setSpacing(SPACE["sm"])
        card.body.addWidget(label("RESOURCES", "eyebrow"))
        for resource in resources:
            entry = QVBoxLayout()
            entry.setSpacing(0)
            quantity = resource.get("quantity")
            entry.addWidget(_value(
                f"{quantity} × {resource['name']}" if quantity else resource["name"]
            ))
            if resource.get("instructions"):
                entry.addWidget(_value(resource["instructions"], "muted"))
            card.body.addLayout(entry)
        return card

    def _fit_height(self):
        """
        Size to the content, scrolling the body past MAX_SCREEN_SHARE.

        Wrapped labels report a size hint taller than they need, and the layout
        spreads the excess into gaps, so heights come from heightForWidth.
        """
        margins = self.layout().contentsMargins()
        inner = DIALOG_WIDTH - margins.left() - margins.right()
        screen = (self.parent().screen() if self.parent() else None) \
            or QGuiApplication.primaryScreen()
        limit = int(screen.availableGeometry().height() * MAX_SCREEN_SHARE)

        body = self._body_layout.totalHeightForWidth(inner)
        self._scroll.setFixedHeight(body)
        chrome = self.layout().totalHeightForWidth(DIALOG_WIDTH) - body
        if body + chrome > limit:
            # Too tall for the screen: the body keeps its natural height and
            # scrolls inside whatever the heading and Close leave free.
            self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self._scroll.setFixedHeight(max(limit - chrome, 0))
        self.setFixedHeight(self.layout().totalHeightForWidth(DIALOG_WIDTH))
