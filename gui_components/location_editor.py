"""
Location Whitelist Editor Dialog
=================================
Modal dialog for managing the location whitelist configuration (PySide6).
Saves changes to location_config.json in v2 format.

Enabled/disabled state is a real checkbox rather than a "[x]" text prefix plus
a Toggle button, and a filter box keeps a long venue list usable.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .style import SPACE, tokens
from .widgets import label

logger = logging.getLogger(__name__)

# Default fallback locations (mirrors setup_report_processor.DEFAULT_LOCATION_CONFIG)
_DEFAULT_LOCATIONS = [
    {"name": "UC 1225", "enabled": True},
    {"name": "UC 1227", "enabled": True},
    {"name": "UC 2190", "enabled": True},
    {"name": "UC Stage", "enabled": True},
    {"name": "UC Kochoff Hall", "enabled": True},
    {"name": "UC Kochoff Hall A", "enabled": True},
    {"name": "UC Kochoff Hall B", "enabled": True},
    {"name": "UC Kochoff Hall C", "enabled": True},
    {"name": "UC Lounge", "enabled": True},
    {"name": "RUC 1150 (Victors Den)", "enabled": True},
    {"name": "RUC 1171 (Lake Erie)", "enabled": True},
    {"name": "RUC 1172 (Lake Huron)", "enabled": True},
    {"name": "RUC 1173 (Lake Michigan)", "enabled": True},
    {"name": "RUC 1174 (Lake Superior)", "enabled": True},
    {"name": "RUC 1175 (Lake Ontario)", "enabled": True},
    {"name": "FCS 180", "enabled": True},
    {"name": "FCS Dining Rm D", "enabled": True},
    {"name": "FCS Michigan East", "enabled": True},
]


class LocationEditor(QDialog):
    """Modal dialog for adding, removing, and enabling whitelist locations."""

    def __init__(self, config_path: Path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.locations: List[Dict[str, Any]] = []
        self._filter = ""

        self.setWindowTitle("Location Whitelist")
        self.resize(520, 580)
        self.setModal(True)

        self._load_config()
        self._build_ui()
        self._refresh_list()

    # -- config I/O ------------------------------------------------------
    def _load_config(self):
        """Load locations from the config file, with v1 migration support."""
        if not self.config_path.exists():
            self.locations = [loc.copy() for loc in _DEFAULT_LOCATIONS]
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            version = config_data.get("version", 1)
            if version >= 2:
                self.locations = config_data.get("locations", [])
            else:
                locations_dict = config_data.get("locations", {})
                whitelist = locations_dict.get("whitelist", [])
                blacklist = locations_dict.get("blacklist", [])
                self.locations = [{"name": n, "enabled": True} for n in whitelist]
                self.locations += [{"name": n, "enabled": False} for n in blacklist]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Error reading config: {e}")
            self.locations = [loc.copy() for loc in _DEFAULT_LOCATIONS]

    def _save_config(self) -> bool:
        """Save locations to the config file in v2 format."""
        config_data = {
            "_comment": "Location configuration for Setup Report Processor. "
                        "Use the GUI editor to manage locations.",
            "version": 2,
            "locations": self.locations,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Saved location config to: {self.config_path}")
            return True
        except PermissionError:
            QMessageBox.critical(
                self, "Save Failed",
                f"Cannot write to:\n{self.config_path}\n\nCheck file permissions.",
            )
            return False
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Error saving config:\n{e}")
            return False

    # -- UI --------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        layout.setSpacing(SPACE["md"])

        layout.addWidget(label("Location whitelist", "title"))
        intro = label(
            "Only checked locations are included in the generated schedules. "
            "Unchecking keeps a location on file without using it.",
            "muted",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter locations…")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_edit)

        self.list_widget = QListWidget()
        self.list_widget.setProperty("variant", "plain")
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, stretch=1)

        actions = QHBoxLayout()
        actions.setSpacing(SPACE["sm"])
        add_btn = QPushButton("Add location")
        add_btn.setProperty("variant", "quiet")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_location)
        remove_btn = QPushButton("Remove selected")
        remove_btn.setProperty("variant", "quiet")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(self._remove_selected)
        actions.addWidget(add_btn)
        actions.addWidget(remove_btn)
        actions.addStretch()
        self.summary_label = label("", "faint")
        actions.addWidget(self.summary_label)
        layout.addLayout(actions)

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

    def _refresh_list(self):
        """Rebuild the visible rows from ``self.locations`` and the filter."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        needle = self._filter.lower()
        for index, loc in enumerate(self.locations):
            if needle and needle not in loc.get("name", "").lower():
                continue
            enabled = loc.get("enabled", True)
            item = QListWidgetItem(loc.get("name", ""))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
            item.setData(Qt.UserRole, index)
            # Second cue beyond the checkbox: disabled entries read as inactive.
            if not enabled:
                item.setForeground(QBrush(QColor(tokens()["text_faint"])))
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._refresh_summary()

    def _refresh_summary(self):
        total = len(self.locations)
        enabled = sum(1 for loc in self.locations if loc.get("enabled", True))
        self.summary_label.setText(f"{enabled} of {total} enabled")

    # -- actions ---------------------------------------------------------
    def _on_filter_changed(self, text: str):
        self._filter = text.strip()
        self._refresh_list()

    def _on_item_changed(self, item: QListWidgetItem):
        index = item.data(Qt.UserRole)
        if index is None or index >= len(self.locations):
            return
        self.locations[index]["enabled"] = item.checkState() == Qt.Checked
        self._refresh_summary()

    def _add_location(self):
        name, ok = QInputDialog.getText(
            self, "Add Location",
            "Location name (matched against the start of the PDF's location text):",
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if any(loc["name"].lower() == name.lower() for loc in self.locations):
            QMessageBox.warning(self, "Already Listed", f"'{name}' is already in the list.")
            return
        self.locations.append({"name": name, "enabled": True})
        self.filter_edit.clear()   # make sure the new entry is visible
        self._refresh_list()
        self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def _remove_selected(self):
        indices = sorted(
            (item.data(Qt.UserRole) for item in self.list_widget.selectedItems()),
            reverse=True,
        )
        if not indices:
            QMessageBox.information(
                self, "Nothing Selected", "Select one or more locations to remove."
            )
            return
        for index in indices:
            del self.locations[index]
        self._refresh_list()

    def _on_save(self):
        if self._save_config():
            self.accept()
