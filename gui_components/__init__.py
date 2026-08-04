"""
GUI Components for Setup Report Processor (PySide6)
==================================================
Modular components for the drag-and-drop desktop interface.
"""

from .settings import GUI_DEFAULTS, GANTT, DIMENSIONS
from .style import RADIUS, SPACE, TYPE, apply_theme, tokens
from .theme import is_dark_mode
from .widgets import (
    Card,
    CollapsibleSection,
    HeaderBar,
    OutcomeIcon,
    StatusGlyph,
    label,
    pill,
    set_pill,
)
from .building_config import BuildingColors, prefix_of
from .building_editor import BuildingColorEditor
from .keep_awake import KeepAwake
from .preferences import PREFS_FILENAME, Preferences
from .log_handler import QtLogHandler, LogPanel
from .drop_zone import DragDropZone
from .file_list import FileListManager
from .location_editor import LocationEditor
from .result_panel import ResultPanel
from .worker import ProcessorWorker
from .gantt_window import GanttWindow

__all__ = [
    "GUI_DEFAULTS",
    "GANTT",
    "DIMENSIONS",
    "RADIUS",
    "SPACE",
    "TYPE",
    "apply_theme",
    "tokens",
    "is_dark_mode",
    "Card",
    "CollapsibleSection",
    "HeaderBar",
    "OutcomeIcon",
    "StatusGlyph",
    "label",
    "pill",
    "set_pill",
    "BuildingColors",
    "BuildingColorEditor",
    "prefix_of",
    "KeepAwake",
    "PREFS_FILENAME",
    "Preferences",
    "QtLogHandler",
    "LogPanel",
    "DragDropZone",
    "FileListManager",
    "LocationEditor",
    "ResultPanel",
    "ProcessorWorker",
    "GanttWindow",
]
