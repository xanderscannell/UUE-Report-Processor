"""
Location Whitelist Editor Dialog
=================================
Modal dialog for managing the location whitelist configuration (PySide6).
Saves changes to location_config.json in v2 format.
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
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

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
    """Modal dialog for adding, removing, and toggling whitelist locations."""

    def __init__(self, config_path: Path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.locations: List[Dict[str, Any]] = []

        self.setWindowTitle("Edit Location Whitelist")
        self.resize(500, 500)
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

        header = QLabel(
            "Manage location whitelist. Enabled locations are included in output.\n"
            "Double-click an item to toggle it."
        )
        header.setStyleSheet("color: #555555;")
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setStyleSheet("font-family: Consolas, monospace;")
        self.list_widget.itemDoubleClicked.connect(
            lambda _: self._toggle_selected()
        )
        layout.addWidget(self.list_widget)

        actions = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._add_location)
        remove_btn = QPushButton("- Remove")
        remove_btn.clicked.connect(self._remove_selected)
        toggle_btn = QPushButton("Toggle")
        toggle_btn.clicked.connect(self._toggle_selected)
        actions.addWidget(add_btn)
        actions.addWidget(remove_btn)
        actions.addWidget(toggle_btn)
        actions.addStretch()
        layout.addLayout(actions)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(save_btn)
        bottom.addWidget(cancel_btn)
        layout.addLayout(bottom)

    def _refresh_list(self):
        selected = {i.row() for i in self.list_widget.selectedIndexes()}
        self.list_widget.clear()
        for i, loc in enumerate(self.locations):
            enabled = loc.get("enabled", True)
            prefix = "[x]" if enabled else "[ ]"
            item = QListWidgetItem(f"  {prefix}  {loc['name']}")
            if not enabled:
                item.setForeground(QBrush(QColor("#999999")))
            self.list_widget.addItem(item)
            if i in selected:
                item.setSelected(True)

    # -- actions ---------------------------------------------------------
    def _add_location(self):
        name, ok = QInputDialog.getText(self, "Add Location", "Enter location name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if any(loc["name"].lower() == name.lower() for loc in self.locations):
            QMessageBox.warning(self, "Duplicate", f"'{name}' already exists in the list.")
            return
        self.locations.append({"name": name, "enabled": True})
        self._refresh_list()
        self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def _remove_selected(self):
        rows = sorted((i.row() for i in self.list_widget.selectedIndexes()), reverse=True)
        for row in rows:
            del self.locations[row]
        self._refresh_list()

    def _toggle_selected(self):
        for index in self.list_widget.selectedIndexes():
            loc = self.locations[index.row()]
            loc["enabled"] = not loc.get("enabled", True)
        self._refresh_list()

    def _on_save(self):
        if self._save_config():
            self.accept()
