"""
Location Whitelist Editor Dialog
=================================
Modal dialog for managing the location whitelist configuration.
"""

import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .settings import COLORS

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


class LocationEditor(tk.Toplevel):
    """
    Modal dialog for editing the location whitelist.

    Allows adding, removing, and toggling locations on/off.
    Saves changes to location_config.json in v2 format.
    """

    def __init__(self, parent, config_path: Path):
        """
        Initialize the location editor dialog.

        Args:
            parent: Parent window
            config_path: Path to location_config.json
        """
        super().__init__(parent)
        self.config_path = config_path
        self.locations: List[Dict[str, Any]] = []
        self.saved = False

        # Window setup
        self.title("Edit Location Whitelist")
        self.geometry("500x500")
        self.resizable(True, True)
        self.transient(parent)

        # Load config
        self._load_config()

        # Build UI
        self._create_widgets()
        self._refresh_list()

        # Make modal
        self.grab_set()

    def show(self) -> bool:
        """
        Show the editor and wait for it to close.

        Returns:
            True if the user saved changes, False if cancelled.
        """
        self.wait_window()
        return self.saved

    def _load_config(self):
        """Load locations from the config file, with v1 migration support."""
        if not self.config_path.exists():
            self.locations = [loc.copy() for loc in _DEFAULT_LOCATIONS]
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            version = config_data.get("version", 1)

            if version >= 2:
                self.locations = config_data.get("locations", [])
            else:
                # Migrate v1 format
                locations_dict = config_data.get("locations", {})
                whitelist = locations_dict.get("whitelist", [])
                blacklist = locations_dict.get("blacklist", [])
                self.locations = []
                for name in whitelist:
                    self.locations.append({"name": name, "enabled": True})
                for name in blacklist:
                    self.locations.append({"name": name, "enabled": False})

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Error reading config: {e}")
            self.locations = [loc.copy() for loc in _DEFAULT_LOCATIONS]

    def _save_config(self) -> bool:
        """
        Save locations to the config file in v2 format.

        Returns:
            True if saved successfully, False on error.
        """
        config_data = {
            "_comment": "Location configuration for Setup Report Processor. Use the GUI editor to manage locations.",
            "version": 2,
            "locations": self.locations,
        }

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Saved location config to: {self.config_path}")
            return True
        except PermissionError:
            messagebox.showerror(
                "Save Failed",
                f"Cannot write to:\n{self.config_path}\n\nCheck file permissions.",
                parent=self,
            )
            return False
        except Exception as e:
            messagebox.showerror(
                "Save Failed",
                f"Error saving config:\n{e}",
                parent=self,
            )
            return False

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main = tk.Frame(self, padx=10, pady=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(
            main,
            text="Manage location whitelist. Enabled locations will be included in output.",
            font=("Arial", 9),
            fg="#555555",
        ).pack(anchor=tk.W, pady=(0, 8))

        # Listbox with scrollbar
        list_frame = tk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("Consolas", 10),
            activestyle="none",
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Double-click to toggle
        self.listbox.bind("<Double-Button-1>", lambda e: self._toggle_selected())

        # Action buttons row
        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Button(btn_frame, text="+ Add", width=10, command=self._add_location).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_frame, text="- Remove", width=10, command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_frame, text="Toggle", width=10, command=self._toggle_selected).pack(side=tk.LEFT)

        # Save / Cancel row
        bottom_frame = tk.Frame(main)
        bottom_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(bottom_frame, text="Cancel", width=10, command=self._on_cancel).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(bottom_frame, text="Save", width=10, command=self._on_save).pack(side=tk.RIGHT)

    def _refresh_list(self):
        """Refresh the listbox display from self.locations."""
        # Remember selection
        selected_indices = set(self.listbox.curselection())

        self.listbox.delete(0, tk.END)
        for i, loc in enumerate(self.locations):
            prefix = "[x]" if loc.get("enabled", True) else "[ ]"
            self.listbox.insert(tk.END, f"  {prefix}  {loc['name']}")

            # Color disabled items gray
            if not loc.get("enabled", True):
                self.listbox.itemconfig(i, fg="#999999")

        # Restore selection
        for idx in selected_indices:
            if idx < self.listbox.size():
                self.listbox.selection_set(idx)

    def _add_location(self):
        """Prompt user for a new location name and add it."""
        name = simpledialog.askstring(
            "Add Location",
            "Enter location name:",
            parent=self,
        )
        if not name or not name.strip():
            return

        name = name.strip()

        # Check for duplicates
        for loc in self.locations:
            if loc["name"].lower() == name.lower():
                messagebox.showwarning(
                    "Duplicate",
                    f"'{name}' already exists in the list.",
                    parent=self,
                )
                return

        self.locations.append({"name": name, "enabled": True})
        self._refresh_list()

        # Select the newly added item
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(tk.END)
        self.listbox.see(tk.END)

    def _remove_selected(self):
        """Remove selected locations from the list."""
        selected = sorted(self.listbox.curselection(), reverse=True)
        if not selected:
            return

        for idx in selected:
            del self.locations[idx]

        self._refresh_list()

    def _toggle_selected(self):
        """Toggle the enabled state of selected locations."""
        selected = self.listbox.curselection()
        if not selected:
            return

        for idx in selected:
            self.locations[idx]["enabled"] = not self.locations[idx].get("enabled", True)

        self._refresh_list()

    def _on_save(self):
        """Handle Save button click."""
        if self._save_config():
            self.saved = True
            self.destroy()

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.saved = False
        self.destroy()
