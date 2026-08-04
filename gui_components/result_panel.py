"""
Results Screen
==============
Shown after a processing run finishes.

Replaces the old "modal message box, then go find your files yourself" ending
with a summary the user can act on: what was produced, where it went, and the
two things they most likely want next (open the folder, or see the timeline).
"""

from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .style import SPACE, tokens
from .widgets import Card, OutcomeIcon, label


class StatTile(QFrame):
    """A single metric: a large number over a small caption."""

    def __init__(self, value: str, caption: str, parent=None):
        super().__init__(parent)
        self.setProperty("card", "sunken")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["md"], SPACE["md"], SPACE["md"], SPACE["md"])
        layout.setSpacing(0)

        self.value_label = label(value, "metric")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.caption_label = label(caption, "eyebrow")
        self.caption_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str, caption: str = None, color: str = None):
        """Update the metric, and optionally its caption and number color."""
        self.value_label.setText(value)
        if caption is not None:
            self.caption_label.setText(caption)
        if color:
            self.value_label.setStyleSheet(f"color: {color};")


class ResultPanel(QWidget):
    """Post-run summary with follow-up actions."""

    open_folder_requested = Signal()
    open_gantt_requested = Signal()
    process_more_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(SPACE["md"])
        outer.addStretch()

        card = Card(padding=SPACE["xl"])
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # Headline
        head = QHBoxLayout()
        head.setSpacing(SPACE["md"])
        head.addStretch()
        self.icon = OutcomeIcon(46)
        head.addWidget(self.icon)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title = label("All done", "display")
        self.subtitle = label("", "subtitle")
        title_col.addWidget(self.title)
        title_col.addWidget(self.subtitle)
        head.addLayout(title_col)
        head.addStretch()
        card.body.addLayout(head)

        # Metrics
        stats = QHBoxLayout()
        stats.setSpacing(SPACE["md"])
        self.files_tile = StatTile("0", "FILES")
        self.events_tile = StatTile("0", "EVENTS")
        self.issues_tile = StatTile("0", "ISSUES")
        for tile in (self.files_tile, self.events_tile, self.issues_tile):
            stats.addWidget(tile, stretch=1)
        card.body.addLayout(stats)

        # Where the output went
        self.location_label = label("", "muted")
        self.location_label.setAlignment(Qt.AlignCenter)
        self.location_label.setWordWrap(True)
        card.body.addWidget(self.location_label)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(SPACE["sm"])
        actions.addStretch()

        self.gantt_button = QPushButton("View Timeline")
        self.gantt_button.setProperty("variant", "primary")
        self.gantt_button.setCursor(Qt.PointingHandCursor)
        self.gantt_button.clicked.connect(self.open_gantt_requested)

        self.folder_button = QPushButton("Open Output Folder")
        self.folder_button.setProperty("variant", "secondary")
        self.folder_button.setCursor(Qt.PointingHandCursor)
        self.folder_button.clicked.connect(self.open_folder_requested)

        actions.addWidget(self.gantt_button)
        actions.addWidget(self.folder_button)
        actions.addStretch()
        card.body.addLayout(actions)

        more = QHBoxLayout()
        more.addStretch()
        self.more_button = QPushButton("← Process more files")
        self.more_button.setProperty("variant", "ghost")
        self.more_button.setCursor(Qt.PointingHandCursor)
        self.more_button.clicked.connect(self.process_more_requested)
        more.addWidget(self.more_button)
        more.addStretch()
        card.body.addLayout(more)

        outer.addWidget(card)
        outer.addStretch()

    # -- data ------------------------------------------------------------
    def set_results(self, summary: Dict):
        """
        Populate the panel from a run summary.

        Args:
            summary: keys ``ok``, ``failed``, ``empty``, ``events``,
                ``output_dir``, ``formats``, ``cancelled``, ``has_gantt``.
        """
        t = tokens()
        ok = summary.get("ok", 0)
        failed = summary.get("failed", 0)
        empty = summary.get("empty", 0)
        issues = failed + empty
        cancelled = summary.get("cancelled", False)
        formats = summary.get("formats") or []
        # No format selected: the run built the timeline and wrote nothing.
        dry_run = not formats and ok > 0 and not cancelled

        total = ok + issues
        if cancelled:
            self.title.setText("Stopped")
            self.subtitle.setText("Processing was cancelled before it finished.")
            self.icon.set_state(OutcomeIcon.STOPPED)
        elif not ok:
            self.title.setText("Nothing was produced")
            self.subtitle.setText(
                "No schedules were generated — open Details to see why."
            )
            self.icon.set_state(OutcomeIcon.FAILURE)
        elif issues:
            self.title.setText("Finished with issues")
            self.subtitle.setText(
                f"{ok} of {total} files could be read."
                if dry_run
                else f"{ok} of {total} files produced a schedule."
            )
            self.icon.set_state(OutcomeIcon.ISSUES)
        else:
            self.title.setText("All done")
            self.subtitle.setText(
                f"{ok} file{'' if ok == 1 else 's'} read — timeline only, nothing saved."
                if dry_run
                else f"{ok} file{'' if ok == 1 else 's'} processed successfully."
            )
            self.icon.set_state(OutcomeIcon.SUCCESS)

        self.files_tile.set_value(str(ok), "FILES DONE", t["text"])
        self.events_tile.set_value(str(summary.get("events", 0)), "EVENTS FOUND", t["text"])
        self.issues_tile.set_value(
            str(issues), "ISSUES", t["warning"] if issues else t["text_faint"]
        )

        output_dir = summary.get("output_dir")
        if formats and output_dir:
            self.location_label.setText(
                f"{' + '.join(formats)} saved to  {Path(output_dir).resolve()}"
            )
            self.location_label.show()
            self.folder_button.show()
        elif dry_run:
            self.location_label.setText(
                "No spreadsheet was created. Tick Excel or CSV before processing "
                "if you want files."
            )
            self.location_label.show()
            self.folder_button.hide()
        else:
            self.location_label.hide()
            self.folder_button.hide()

        self.gantt_button.setVisible(summary.get("has_gantt", False))
