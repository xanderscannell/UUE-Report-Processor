"""
Building Color Configuration
============================
Maps room-name prefixes (``UC 1225`` → ``UC``) to a color used on the event
timeline, persisted in ``location_config.json`` under a ``buildings`` key.

Two design points matter here:

**Buildings are discovered, not hardcoded.** Any prefix that turns up in the
location whitelist or in a processed report gets an entry automatically, so a
new campus building needs no code change.

**Colors are palette slots, not free hex.** Each slot carries a light-surface
and a dark-surface step, so a building keeps its identity when the theme flips,
and every offered color is one that has been checked for colorblind separation
and contrast against the chart surface. Auto-assignment walks the slots in a
fixed order and is then *persisted* — a building must not change color from one
report to the next.

Two prefixes that name the same physical building (``UC`` and ``RUC`` — the
University Center was renamed the Renick University Center, but existing rooms
kept their old names) are handled by simply giving them the same color. The
timeline merges same-colored buildings into one legend entry.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Validated categorical slots: (name, light step, dark step).
PALETTE: List[Tuple[str, str, str]] = [
    ("Blue", "#2a78d6", "#3987e5"),
    ("Orange", "#eb6834", "#d95926"),
    ("Aqua", "#1baf7a", "#199e70"),
    ("Yellow", "#eda100", "#c98500"),
    ("Magenta", "#e87ba4", "#d55181"),
    ("Green", "#008300", "#008300"),
    ("Violet", "#4a3aa7", "#9085e9"),
    ("Red", "#e34948", "#e66767"),
]

# Slot used for anything unassigned; deliberately neutral so it never reads as
# one more category.
NEUTRAL = ("Gray", "#8a8f98", "#8a8f98")
NEUTRAL_SLOT = -1

# The first three slots stay mutually distinguishable under every colorblind
# simulation at once. Past that, the Y-axis location labels carry identity.
SAFE_SLOT_COUNT = 3

# Shipped defaults. UC and RUC share slot 0 because they are one building.
DEFAULT_BUILDINGS: Dict[str, dict] = {
    "UC": {"label": "Renick University Center", "color": 0},
    "RUC": {"label": "Renick University Center", "color": 0},
    "FCS": {"label": "Fairlane Center South", "color": 1},
}


def prefix_of(location: str) -> str:
    """
    Return the building prefix of a location, e.g. ``'RUC 1171 (Lake Erie)'``
    → ``'RUC'``. Returns an empty string when there is nothing to read.
    """
    return (location or "").strip().split(" ")[0].upper()


def discover_prefixes(locations: Iterable[str]) -> List[str]:
    """Return the distinct, sorted building prefixes found in some locations."""
    found = {p for p in (prefix_of(loc) for loc in locations) if p}
    return sorted(found)


class BuildingColors:
    """Building prefix → label and color slot, loaded from and saved to JSON."""

    def __init__(self, entries: Optional[Dict[str, dict]] = None):
        self.entries: Dict[str, dict] = entries if entries is not None else {}

    @classmethod
    def defaults(cls) -> "BuildingColors":
        """The shipped assignments, for use when no config has been read."""
        return cls({k: v.copy() for k, v in DEFAULT_BUILDINGS.items()})

    # -- persistence -----------------------------------------------------
    @classmethod
    def load(cls, config_path: Path) -> "BuildingColors":
        """
        Read the ``buildings`` block from the location config.

        Falls back to the shipped defaults when the file is missing, malformed,
        or predates this setting.
        """
        if not config_path.exists():
            return cls.defaults()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("buildings")
            if not isinstance(raw, dict) or not raw:
                return cls.defaults()

            entries = {}
            for prefix, value in raw.items():
                if not isinstance(value, dict):
                    continue
                entries[str(prefix).upper()] = {
                    "label": str(value.get("label", prefix)),
                    "color": cls._sanitize_slot(value.get("color")),
                }
            return cls(entries)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
            logger.warning(f"Could not read building colors, using defaults: {e}")
            return cls.defaults()

    def save(self, config_path: Path) -> bool:
        """
        Write the ``buildings`` block back, preserving everything else in the
        file. Returns True on success.
        """
        data = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not read config before saving buildings: {e}")
                return False

        data.setdefault(
            "_comment",
            "Location configuration for Setup Report Processor. "
            "Use the GUI editor to manage locations.",
        )
        data.setdefault("version", 2)
        data.setdefault("locations", [])
        data["buildings"] = self.entries

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved building colors to: {config_path}")
            return True
        except OSError as e:
            logger.error(f"Could not save building colors: {e}")
            return False

    # -- discovery -------------------------------------------------------
    def ensure(self, prefixes: Iterable[str]) -> bool:
        """
        Add an entry for every prefix not already known, assigning each the
        lowest color slot not yet in use (wrapping once every slot is taken).

        Accepts either bare prefixes or full location strings — ``prefix_of``
        is idempotent, so callers need not normalize first.

        Returns True if anything was added, so the caller can persist.
        """
        added = False
        for prefix in sorted({prefix_of(p) for p in prefixes if p}):
            if prefix in self.entries:
                continue
            self.entries[prefix] = {
                "label": DEFAULT_BUILDINGS.get(prefix, {}).get("label", prefix),
                "color": DEFAULT_BUILDINGS.get(prefix, {}).get(
                    "color", self._next_free_slot()
                ),
            }
            added = True
        return added

    def _next_free_slot(self) -> int:
        used = {e.get("color") for e in self.entries.values()}
        for slot in range(len(PALETTE)):
            if slot not in used:
                return slot
        # Every slot is spoken for; reuse from the top rather than inventing a
        # color that has not been checked.
        return len(self.entries) % len(PALETTE)

    # -- lookups ---------------------------------------------------------
    def slot(self, prefix: str) -> int:
        """Color slot for a prefix, or NEUTRAL_SLOT when it is unknown."""
        entry = self.entries.get((prefix or "").upper())
        return self._sanitize_slot(entry.get("color")) if entry else NEUTRAL_SLOT

    def color(self, prefix: str, dark: bool = False) -> str:
        """Hex color for a prefix on the given surface."""
        return self.slot_color(self.slot(prefix), dark)

    def label(self, prefix: str) -> str:
        """Friendly building name for a prefix, defaulting to the prefix."""
        entry = self.entries.get((prefix or "").upper())
        label = (entry or {}).get("label", "").strip()
        return label or (prefix.upper() if prefix else "Other")

    def legend(self, prefixes: Iterable[str], dark: bool = False) -> List[Tuple[str, str]]:
        """
        Build legend entries as (color, label) pairs for the given prefixes.

        Prefixes sharing a color collapse into one entry — which is how "UC and
        RUC are the same building" ends up reading correctly without any
        aliasing concept. Labels that differ are joined.
        """
        by_slot: Dict[int, List[str]] = {}
        for prefix in prefixes:
            if not prefix:
                continue
            by_slot.setdefault(self.slot(prefix), []).append(self.label(prefix))

        entries = []
        for slot in sorted(by_slot, key=lambda s: (s < 0, s)):
            names = list(dict.fromkeys(by_slot[slot]))  # de-dupe, keep order
            entries.append((self.slot_color(slot, dark), " / ".join(names)))
        return entries

    # -- palette helpers -------------------------------------------------
    @staticmethod
    def slot_color(slot: int, dark: bool = False) -> str:
        """Hex for a palette slot on the light or dark chart surface."""
        if slot is None or slot < 0 or slot >= len(PALETTE):
            return NEUTRAL[2] if dark else NEUTRAL[1]
        return PALETTE[slot][2] if dark else PALETTE[slot][1]

    @staticmethod
    def slot_name(slot: int) -> str:
        """Human-readable name of a palette slot."""
        if slot is None or slot < 0 or slot >= len(PALETTE):
            return NEUTRAL[0]
        return PALETTE[slot][0]

    @staticmethod
    def _sanitize_slot(value) -> int:
        try:
            slot = int(value)
        except (TypeError, ValueError):
            return NEUTRAL_SLOT
        return slot if -1 <= slot < len(PALETTE) else NEUTRAL_SLOT
