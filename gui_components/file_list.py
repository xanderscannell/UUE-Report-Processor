"""
File Queue Manager Widget
===========================
Manages the list of PDF files queued for processing.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List
from .settings import DIMENSIONS


class FileListManager(tk.Frame):
    """
    Widget for managing the file processing queue.

    Features:
    - Display list of queued files
    - Remove individual files
    - Clear all files
    - Get list of files for processing
    """

    def __init__(self, parent):
        """
        Initialize the file list manager.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.files: List[Path] = []

        # Create UI components
        self._create_widgets()

    def _create_widgets(self):
        """Create the file list UI components."""
        # Header with count
        header_frame = tk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        self.count_label = tk.Label(
            header_frame,
            text="Files to Process (0):",
            font=("Arial", 10, "bold"),
        )
        self.count_label.pack(side=tk.LEFT)

        self.clear_button = tk.Button(
            header_frame,
            text="Clear All",
            command=self.clear_all,
            state=tk.DISABLED,
        )
        self.clear_button.pack(side=tk.RIGHT)

        # Listbox with scrollbar
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame,
            height=8,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Bind double-click to remove
        self.listbox.bind("<Double-Button-1>", lambda e: self.remove_selected())

        # Buttons frame
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))

        self.remove_button = tk.Button(
            buttons_frame,
            text="Remove Selected",
            command=self.remove_selected,
            state=tk.DISABLED,
        )
        self.remove_button.pack(side=tk.LEFT)

    def add_files(self, paths: List[Path]):
        """
        Add files to the queue (avoiding duplicates).

        Args:
            paths: List of Path objects to add
        """
        added_count = 0

        for path in paths:
            # Avoid duplicates
            if path not in self.files:
                self.files.append(path)
                self.listbox.insert(tk.END, str(path.name))
                added_count += 1

        # Update UI
        if added_count > 0:
            self._update_count()
            self._update_button_states()

    def remove_selected(self):
        """Remove the currently selected file from the queue."""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.listbox.delete(index)
            del self.files[index]
            self._update_count()
            self._update_button_states()

    def clear_all(self):
        """Clear all files from the queue."""
        self.listbox.delete(0, tk.END)
        self.files.clear()
        self._update_count()
        self._update_button_states()

    def get_files(self) -> List[Path]:
        """
        Get the list of queued files.

        Returns:
            List of Path objects
        """
        return self.files.copy()

    def has_files(self) -> bool:
        """
        Check if there are files in the queue.

        Returns:
            True if queue is not empty
        """
        return len(self.files) > 0

    def _update_count(self):
        """Update the file count label."""
        count = len(self.files)
        self.count_label.config(text=f"Files to Process ({count}):")

    def _update_button_states(self):
        """Update button enabled/disabled states."""
        has_files = self.has_files()
        self.clear_button.config(state=tk.NORMAL if has_files else tk.DISABLED)
        self.remove_button.config(state=tk.NORMAL if has_files else tk.DISABLED)
