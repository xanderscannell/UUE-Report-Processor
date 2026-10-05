"""
25Live Day Picker
=================
Small modal dialog for choosing which days to pull from 25Live. A range is
offered because a weekend stacks into one timeline (ADR-011).
"""

from datetime import date, timedelta
from typing import List

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from .style import SPACE
from .widgets import label


class LiveDayDialog(QDialog):
    """Modal dialog that picks a first and last day to pull from 25Live."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pull from 25Live")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        layout.setSpacing(SPACE["md"])

        layout.addWidget(label("Pull from 25Live", "title"))
        intro = label(
            "Reads the bookings 25Live shows publicly, so no sign-in is needed. "
            "Each day is added to the queue like a report file.",
            "muted",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        today = QDate.currentDate()
        self.first = QDateEdit(today)
        self.last = QDateEdit(today)
        for edit in (self.first, self.last):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("ddd MMM d, yyyy")
        # Moving the first day past the last drags the last day along.
        self.last.setMinimumDate(today)
        self.first.dateChanged.connect(self.last.setMinimumDate)

        form = QFormLayout()
        form.setSpacing(SPACE["sm"])
        form.addRow("From", self.first)
        form.addRow("To", self.last)
        layout.addLayout(form)

        bottom = QHBoxLayout()
        bottom.setSpacing(SPACE["sm"])
        bottom.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        add_btn = QPushButton("Add to queue")
        add_btn.setProperty("variant", "secondary")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setDefault(True)
        add_btn.clicked.connect(self.accept)
        bottom.addWidget(cancel_btn)
        bottom.addWidget(add_btn)
        layout.addLayout(bottom)

    def days(self) -> List[date]:
        """Every day from the first to the last, inclusive."""
        first, last = self.first.date().toPython(), self.last.date().toPython()
        return [first + timedelta(days=n) for n in range((last - first).days + 1)]
