"""
Drag-and-Drop Widget
=====================
Custom tkinter widget for accepting PDF file drops.
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Callable, List
from .settings import COLORS, DIMENSIONS


class DragDropZone(tk.Frame):
    """
    Drag-and-drop zone for PDF files.

    Features:
    - Visual feedback on hover
    - Click to browse fallback
    - PDF file validation
    - Callback when files are added
    """

    def __init__(self, parent, on_files_added: Callable[[List[Path]], None]):
        """
        Initialize the drag-and-drop zone.

        Args:
            parent: Parent widget
            on_files_added: Callback function when files are added
        """
        super().__init__(parent, relief=tk.RAISED, borderwidth=2)
        self.on_files_added = on_files_added

        # Configure appearance
        self.config(
            bg=COLORS["drop_zone_normal"],
            height=DIMENSIONS["drop_zone_height"],
            width=DIMENSIONS["drop_zone_width"],
        )

        # Create label
        self.label = tk.Label(
            self,
            text="\U0001F4C4 Drag & Drop PDF Files Here\n\nor Click to Browse",
            bg=COLORS["drop_zone_normal"],
            font=("Arial", 12),
            fg="#757575",
        )
        self.label.pack(expand=True)

        # Bind events
        self.bind("<Button-1>", self.on_click_browse)
        self.label.bind("<Button-1>", self.on_click_browse)

        # Try to enable drag-and-drop (optional feature)
        self._setup_drag_and_drop()

    def _setup_drag_and_drop(self):
        """Set up drag-and-drop support (if tkinterdnd2 is available)."""
        try:
            # Try to import tkinterdnd2
            from tkinterdnd2 import DND_FILES

            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self.on_drop)

            # Update hover effects
            self.dnd_bind("<<DragEnter>>", lambda e: self._set_hover(True))
            self.dnd_bind("<<DragLeave>>", lambda e: self._set_hover(False))

        except ImportError:
            # tkinterdnd2 not available - fallback to click-to-browse only
            pass

    def on_drop(self, event):
        """
        Handle file drop event.

        Args:
            event: Drop event containing file paths
        """
        # Reset hover state
        self._set_hover(False)

        # Parse dropped files
        files = self.tk.splitlist(event.data)
        pdf_files = self.validate_files(files)

        # Notify callback
        if pdf_files:
            self.on_files_added(pdf_files)

    def on_click_browse(self, event=None):
        """
        Handle click event - open file dialog.

        Args:
            event: Click event (optional)
        """
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

        if files:
            pdf_files = self.validate_files(files)
            if pdf_files:
                self.on_files_added(pdf_files)

    def validate_files(self, file_paths: List[str]) -> List[Path]:
        """
        Validate and filter PDF files.

        Args:
            file_paths: List of file path strings

        Returns:
            List of Path objects for valid PDF files
        """
        pdf_files = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.suffix.lower() == ".pdf":
                pdf_files.append(path)

        return pdf_files

    def _set_hover(self, is_hovering: bool):
        """
        Update visual state for hover.

        Args:
            is_hovering: True if hovering, False otherwise
        """
        color = COLORS["drop_zone_hover"] if is_hovering else COLORS["drop_zone_normal"]
        self.config(bg=color)
        self.label.config(bg=color)
