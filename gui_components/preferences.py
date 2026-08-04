"""
User Preferences
================
Remembers the choices made in the Settings menu and the Output card so they
survive a restart, in ``gui_preferences.json`` beside the executable.

Kept deliberately separate from ``location_config.json`` (see ADR-007): that
file is authored configuration that ships with the app and is hand-edited or
replaced wholesale, while this one is runtime UI state the app rewrites every
time a toggle moves.

Defaults live in ``settings.py`` — this module never restates them, it only
remembers departures from them. A missing or malformed file is not an error:
the app falls back to those defaults and carries on.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .settings import GUI_DEFAULTS

logger = logging.getLogger(__name__)

PREFS_FILENAME = "gui_preferences.json"
VERSION = 1

# Which preferences persist, and how each is coerced back from JSON.
BOOL_KEYS = (
    "excel_enabled",
    "csv_enabled",
    "gantt_autolaunch",
    "verbose_logging",
    "keep_awake",
)
PATH_KEYS = ("output_dir",)


class Preferences:
    """
    Persistent user preferences, loaded from and saved to JSON.

    Values are always readable — an unknown or unreadable key falls back to the
    shipped default rather than raising, so a hand-mangled file degrades to
    "first run" instead of breaking the app.

    Example:
        prefs = Preferences.load(path)
        if prefs.set("keep_awake", True):
            prefs.save(path)
    """

    def __init__(self, values: Optional[Dict[str, Any]] = None):
        self.values: Dict[str, Any] = self.defaults()
        if values:
            self.values.update(values)

    @staticmethod
    def defaults() -> Dict[str, Any]:
        """The shipped defaults, taken from ``GUI_DEFAULTS``."""
        values: Dict[str, Any] = {key: bool(GUI_DEFAULTS[key]) for key in BOOL_KEYS}
        values.update({key: Path(GUI_DEFAULTS[key]) for key in PATH_KEYS})
        return values

    # -- persistence -----------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> "Preferences":
        """
        Read saved preferences.

        Args:
            path: Full path to the preferences JSON file.

        Returns:
            A ``Preferences`` holding the saved values, falling back to the
            defaults for anything missing, malformed, or no longer usable.
        """
        if not path.exists():
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("preferences file is not a JSON object")
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f"Could not read preferences, using defaults: {e}")
            return cls()

        prefs = cls()
        for key in BOOL_KEYS:
            if key in data:
                prefs.values[key] = bool(data[key])
        for key in PATH_KEYS:
            if key in data:
                resolved = cls._sanitize_path(data[key], key)
                if resolved is not None:
                    prefs.values[key] = resolved
        logger.debug(f"Loaded preferences from: {path}")
        return prefs

    def save(self, path: Path) -> bool:
        """
        Write the current preferences.

        Args:
            path: Full path to the preferences JSON file.

        Returns:
            True on success. A failure is logged, never raised — being unable
            to remember a preference must not interrupt what the user is doing.
        """
        data: Dict[str, Any] = {
            "_comment": (
                "Interface preferences for Setup Report Processor, written by "
                "the app. Delete this file to return to defaults."
            ),
            "version": VERSION,
        }
        data.update({key: bool(self.values[key]) for key in BOOL_KEYS})
        data.update({key: str(self.values[key]) for key in PATH_KEYS})

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.debug(f"Saved preferences to: {path}")
            return True
        except OSError as e:
            logger.warning(f"Could not save preferences: {e}")
            return False

    # -- access ----------------------------------------------------------
    def get_bool(self, key: str) -> bool:
        """Value of a boolean preference, defaulting if it is somehow unset."""
        return bool(self.values.get(key, GUI_DEFAULTS.get(key, False)))

    def get_path(self, key: str) -> Path:
        """Value of a path preference, defaulting if it is somehow unset."""
        return Path(self.values.get(key, GUI_DEFAULTS[key]))

    def set(self, key: str, value: Any) -> bool:
        """
        Update a preference.

        Args:
            key: One of ``BOOL_KEYS`` or ``PATH_KEYS``.
            value: The new value; coerced to the key's type.

        Returns:
            True if this actually changed something, so the caller can skip a
            pointless write.
        """
        if key in BOOL_KEYS:
            new_value: Any = bool(value)
        elif key in PATH_KEYS:
            new_value = Path(value)
        else:
            logger.warning(f"Ignoring unknown preference: {key}")
            return False

        if self.values.get(key) == new_value:
            return False
        self.values[key] = new_value
        return True

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _sanitize_path(value: Any, key: str) -> Optional[Path]:
        """
        Vet a saved path.

        The folder itself need not exist yet — it is created when output is
        written — but its parent must, so a path left over from another machine
        or an unplugged drive falls back to the default instead of failing at
        the end of a run.
        """
        try:
            path = Path(str(value)).expanduser()
        except (TypeError, ValueError):
            logger.warning(f"Ignoring unusable saved {key}: {value!r}")
            return None
        if not path.exists() and not path.parent.exists():
            logger.warning(
                f"Saved {key} is no longer reachable ({path}); using the default."
            )
            return None
        return path
