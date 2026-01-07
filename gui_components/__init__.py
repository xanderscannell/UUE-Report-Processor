"""
GUI Components for Setup Report Processor
==========================================
Modular components for the drag-and-drop desktop interface.
"""

from .settings import GUI_DEFAULTS, COLORS
from .log_handler import TextHandler
from .drop_zone import DragDropZone
from .file_list import FileListManager

__all__ = [
    "GUI_DEFAULTS",
    "COLORS",
    "TextHandler",
    "DragDropZone",
    "FileListManager",
]
