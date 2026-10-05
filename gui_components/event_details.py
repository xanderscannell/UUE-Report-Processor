"""
Event Details Popup
===================
Opened by clicking a bar on the timeline. The bar and its hover card show the
name, room and times; this shows everything else the source carried for that
event (the row's ``Details``, see ``create_gantt_rows``).

What is in ``Details`` is decided by each reader's allowlist, so no contact
details ever reach this dialog (ADR-013).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from .style import SPACE
from .widgets import Card, label

# Wide enough for a reference number on one line, narrow enough that long room
# instructions wrap into a readable column.
DIALOG_WIDTH = 460


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
        # Wrapped labels report a size hint taller than they need, and the
        # layout spreads the excess into gaps; size to the content instead.
        self.setFixedHeight(self.layout().totalHeightForWidth(DIALOG_WIDTH))

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

        details = row.get("Details") or {}
        if details:
            card = Card(padding=SPACE["md"])
            form = QFormLayout()
            form.setHorizontalSpacing(SPACE["md"])
            form.setVerticalSpacing(SPACE["sm"])
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
            for key, value in details.items():
                text = label(value, "body")
                text.setWordWrap(True)
                # Selectable, so a reference number can be copied into 25Live.
                text.setTextInteractionFlags(Qt.TextSelectableByMouse)
                form.addRow(label(key, "muted"), text)
            card.body.addLayout(form)
            layout.addWidget(card)
        else:
            note = label("This report carries no further details for this event.", "faint")
            note.setWordWrap(True)
            layout.addWidget(note)

        bottom = QHBoxLayout()
        bottom.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setProperty("variant", "secondary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)
