"""
GUI Components for Setup Report Processor (PySide6)
==================================================
Modular components for the drag-and-drop desktop interface.
"""

from .settings import GUI_DEFAULTS, GANTT, DIMENSIONS
from .log_handler import QtLogHandler, LogPanel
from .drop_zone import DragDropZone
from .file_list import FileListManager
from .location_editor import LocationEditor
from .worker import ProcessorWorker
from .gantt_window import GanttWindow

__all__ = [
    "GUI_DEFAULTS",
    "GANTT",
    "DIMENSIONS",
    "QtLogHandler",
    "LogPanel",
    "DragDropZone",
    "FileListManager",
    "LocationEditor",
    "ProcessorWorker",
    "GanttWindow",
]
