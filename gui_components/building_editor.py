"""
Building Colors Dialog
======================
Assigns a timeline color to each building found in the location whitelist and
in processed reports.

The building list populates itself — every room-name prefix that turns up gets
a row — so a new campus building needs no code change. Giving two prefixes the
same color is how "these are the same building" is expressed (UC and RUC, for
instance); the timeline then shows them as a single legend entry.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .building_config import (
    NEUTRAL_SLOT,
    PALETTE,
    SAFE_SLOT_COUNT,
    BuildingColors,
    discover_prefixes,
)
from .style import SPACE, active_dark
from .widgets import Card, label

logger = logging.getLogger(__name__)


def _swatch_icon(color: str, size: int = 14) -> QIcon:
    """A rounded color chip for use inside a combo box entry."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(0, 0, size, size, 4, 4)
    painter.end()
    return QIcon(pixmap)


class BuildingRow(QWidget):
    """One building: color picker, prefix badge, and an editable label."""

    def __init__(self, prefix: str, entry: dict, dark: bool, parent=None):
        super().__init__(parent)
        self.prefix = prefix

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE["sm"])

        self.color_combo = QComboBox()
        self.color_combo.setIconSize(QSize(14, 14))
        self.color_combo.setFixedWidth(150)
        for slot, (name, light, dark_hex) in enumerate(PALETTE):
            suffix = "" if slot < SAFE_SLOT_COUNT else " *"
            self.color_combo.addItem(
                _swatch_icon(dark_hex if dark else light), f"{name}{suffix}", slot
            )
        self.color_combo.addItem(
            _swatch_icon(BuildingColors.slot_color(NEUTRAL_SLOT, dark)),
            "Gray (no color)", NEUTRAL_SLOT,
        )
        index = self.color_combo.findData(BuildingColors._sanitize_slot(entry.get("color")))
        self.color_combo.setCurrentIndex(max(0, index))
        row.addWidget(self.color_combo)

        badge = label(prefix, "eyebrow")
        badge.setFixedWidth(52)
        badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(badge)

        self.label_edit = QLineEdit(entry.get("label", prefix))
        self.label_edit.setPlaceholderText("Building name")
        row.addWidget(self.label_edit, stretch=1)

    def value(self) -> dict:
        """Current label and color slot for this row."""
        return {
            "label": self.label_edit.text().strip() or self.prefix,
            "color": self.color_combo.currentData(),
        }


class BuildingColorEditor(QDialog):
    """Modal dialog for assigning timeline colors to buildings."""

    def __init__(self, config_path: Path, extra_prefixes: Iterable[str] = (), parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.colors = BuildingColors.load(config_path)
        self.rows: List[BuildingRow] = []

        self.setWindowTitle("Building Colors")
        self.resize(600, 520)
        self.setModal(True)

        # Populate from the whitelist plus anything seen in processed reports.
        self.colors.ensure(self._whitelist_prefixes())
        self.colors.ensure(extra_prefixes)

        self._build_ui()

    # -- discovery -------------------------------------------------------
    def _whitelist_prefixes(self) -> List[str]:
        """
        Building prefixes present in the *enabled* location whitelist.

        Only enabled entries count, because disabled ones are frequently
        non-venues ("Special", "Notice") that would otherwise clutter this list
        and consume palette colors. A building disabled after being colored
        keeps its saved entry either way.
        """
        if not self.config_path.exists():
            return []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read locations for building discovery: {e}")
            return []

        locations = data.get("locations", [])
        if isinstance(locations, dict):   # v1 legacy format
            names = list(locations.get("whitelist", []))
        else:
            names = [
                loc.get("name", "")
                for loc in locations
                if isinstance(loc, dict) and loc.get("enabled", True)
            ]
        return discover_prefixes(names)

    # -- UI --------------------------------------------------------------
    def _build_ui(self):
        dark = active_dark()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        layout.setSpacing(SPACE["md"])

        layout.addWidget(label("Building colors", "title"))
        intro = label(
            "Timeline events are colored by the building prefix in their room name. "
            "New buildings are added here automatically the first time they appear.\n\n"
            "Give two prefixes the same color when they are the same building — UC and "
            "RUC both mean the Renick University Center — and the timeline will show "
            "them as one entry.",
            "muted",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = Card(padding=SPACE["md"])
        holder.body.setSpacing(SPACE["sm"])

        for prefix in sorted(self.colors.entries):
            row = BuildingRow(prefix, self.colors.entries[prefix], dark)
            self.rows.append(row)
            holder.body.addWidget(row)
        holder.body.addStretch()

        scroll.setWidget(holder)
        layout.addWidget(scroll, stretch=1)

        note = label(
            f"* Beyond the first {SAFE_SLOT_COUNT} colors, some pairs become hard to "
            "tell apart with color vision deficiency. Every bar is still labeled by "
            "location on the timeline.",
            "faint",
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        bottom = QHBoxLayout()
        bottom.setSpacing(SPACE["sm"])
        bottom.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save changes")
        save_btn.setProperty("variant", "secondary")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        bottom.addWidget(cancel_btn)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)

    # -- actions ---------------------------------------------------------
    def _on_save(self):
        updated: Dict[str, dict] = {row.prefix: row.value() for row in self.rows}
        self.colors.entries.update(updated)
        if self.colors.save(self.config_path):
            self.accept()
        else:
            QMessageBox.critical(
                self, "Save Failed",
                f"Could not write to:\n{self.config_path}\n\nCheck file permissions.",
            )
