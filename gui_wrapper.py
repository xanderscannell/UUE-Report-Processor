#!/usr/bin/env python3
"""
Setup Report Processor - GUI Wrapper
=====================================
Drag-and-drop desktop interface for processing Daily Setup Report PDFs.

Features:
- Drag-and-drop PDF files
- Batch processing
- Excel and/or CSV output
- Real-time progress tracking
- Live logging display
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import threading
import queue
import logging
import os
import sys
import subprocess

# Import GUI components
from gui_components import GUI_DEFAULTS, COLORS, TextHandler, DragDropZone, FileListManager

# Import the processor
from setup_report_processor import SetupReportProcessor


class ProcessorWorker(threading.Thread):
    """Background worker thread for processing PDF files."""

    def __init__(self, files, options, update_queue):
        """
        Initialize the worker thread.

        Args:
            files: List of Path objects to process
            options: Dict with processing options (excel_enabled, csv_enabled, output_dir, verbose)
            update_queue: Queue for sending updates to main thread
        """
        super().__init__(daemon=True)
        self.files = files
        self.options = options
        self.update_queue = update_queue
        self.cancelled = False

    def run(self):
        """Process all files in the queue."""
        total_files = len(self.files)

        for i, pdf_path in enumerate(self.files):
            if self.cancelled:
                self.update_queue.put(("status", "Processing cancelled by user"))
                break

            # Send status update
            self.update_queue.put(("status", f"Processing {pdf_path.name}..."))

            try:
                # Create processor
                processor = SetupReportProcessor(str(pdf_path))

                # Process the PDF
                df = processor.process()

                # Check if any events were found
                if len(df) == 0:
                    self.update_queue.put(
                        ("warning", f"No valid events found in {pdf_path.name}")
                    )
                    continue

                # Save outputs based on options
                output_dir = self.options["output_dir"]
                output_dir.mkdir(parents=True, exist_ok=True)

                if self.options["excel_enabled"]:
                    excel_path = output_dir / f"{processor.get_output_basename()}_schedule.xlsx"
                    processor.save_to_excel(df, str(excel_path))

                if self.options["csv_enabled"]:
                    csv_path = output_dir / f"{processor.get_output_basename()}_schedule.csv"
                    processor.save_to_csv(df, str(csv_path))

                if self.options["matlab_csv_enabled"]:
                    matlab_path = output_dir / f"{processor.get_output_basename()}_matlab.csv"
                    auto_launch = self.options.get("matlab_autolaunch", False)

                    # Find .mlapp file
                    mlapp_path = pdf_path.parent / "GanttChartApp.mlapp"
                    if not mlapp_path.exists():
                        mlapp_path = None

                    processor.save_to_matlab_csv(
                        output_path=str(matlab_path),
                        auto_launch=auto_launch,
                        mlapp_path=str(mlapp_path) if mlapp_path else None
                    )

                # Send progress update
                progress = ((i + 1) / total_files) * 100
                self.update_queue.put(("progress", (progress, i + 1, total_files)))

                # Send success message
                self.update_queue.put(
                    ("success", f"Successfully processed {pdf_path.name}")
                )

            except FileNotFoundError as e:
                self.update_queue.put(("error", f"File not found: {pdf_path.name}"))
            except ValueError as e:
                self.update_queue.put(("error", f"Invalid file: {pdf_path.name} - {str(e)}"))
            except Exception as e:
                self.update_queue.put(
                    ("error", f"Error processing {pdf_path.name}: {str(e)}")
                )

        # Send completion signal
        if not self.cancelled:
            self.update_queue.put(("complete", None))

    def cancel(self):
        """Cancel the processing."""
        self.cancelled = True


class SetupReportProcessorGUI:
    """Main GUI application for Setup Report Processor."""

    def __init__(self):
        """Initialize the GUI application."""
        # Try to use tkinterdnd2 for better drag-and-drop
        try:
            from tkinterdnd2 import TkinterDnD
            self.root = TkinterDnD.Tk()
        except ImportError:
            # Fall back to standard Tk
            self.root = tk.Tk()

        self.root.title(GUI_DEFAULTS["window_title"])
        self.root.geometry(GUI_DEFAULTS["window_size"])
        self.root.resizable(True, True)

        # Processing state
        self.worker = None
        self.update_queue = queue.Queue()
        self.processing = False

        # Create UI
        self._create_widgets()
        self._setup_logging()

        # Start queue polling
        self._poll_queue()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Drag-and-drop zone
        self.drop_zone = DragDropZone(main_frame, self._on_files_added)
        self.drop_zone.pack(pady=(0, 10))

        # File list manager
        self.file_list = FileListManager(main_frame)
        self.file_list.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        # Output options frame
        self._create_output_options(main_frame)

        # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="▶ Process Files",
            command=self._start_processing,
            state=tk.DISABLED,
        )
        self.process_button.pack(pady=10)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(progress_frame, text="Progress:").pack(anchor=tk.W)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W)

        # Status log
        self._create_status_log(main_frame)

        # Action buttons
        self._create_action_buttons(main_frame)

    def _create_output_options(self, parent):
        """Create the output options panel."""
        options_frame = ttk.LabelFrame(parent, text="Output Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Excel/CSV checkboxes
        formats_frame = ttk.Frame(options_frame)
        formats_frame.pack(fill=tk.X, pady=(0, 10))

        self.excel_var = tk.BooleanVar(value=GUI_DEFAULTS["excel_enabled"])
        self.csv_var = tk.BooleanVar(value=GUI_DEFAULTS["csv_enabled"])
        self.matlab_csv_var = tk.BooleanVar(value=GUI_DEFAULTS["matlab_csv_enabled"])
        self.matlab_autolaunch_var = tk.BooleanVar(value=GUI_DEFAULTS["matlab_autolaunch"])

        ttk.Checkbutton(
            formats_frame,
            text="Excel (.xlsx)",
            variable=self.excel_var,
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(
            formats_frame,
            text="CSV (.csv)",
            variable=self.csv_var,
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(
            formats_frame,
            text="MATLAB CSV",
            variable=self.matlab_csv_var,
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(
            formats_frame,
            text="Auto-launch MATLAB",
            variable=self.matlab_autolaunch_var,
        ).pack(side=tk.LEFT)

        # Output folder selection
        folder_frame = ttk.Frame(options_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(folder_frame, text="Output Folder:").pack(side=tk.LEFT)

        self.output_dir_var = tk.StringVar(value=str(GUI_DEFAULTS["output_dir"]))
        output_entry = ttk.Entry(
            folder_frame,
            textvariable=self.output_dir_var,
            width=40,
        )
        output_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        ttk.Button(
            folder_frame,
            text="Browse...",
            command=self._browse_output_folder,
        ).pack(side=tk.LEFT)

        # Verbose logging toggle
        self.verbose_var = tk.BooleanVar(value=GUI_DEFAULTS["verbose_logging"])
        ttk.Checkbutton(
            options_frame,
            text="Verbose Logging",
            variable=self.verbose_var,
            command=self._toggle_verbose,
        ).pack(anchor=tk.W)

    def _create_status_log(self, parent):
        """Create the status log display."""
        log_frame = ttk.LabelFrame(parent, text="Status Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.status_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            state="disabled",
            wrap=tk.WORD,
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def _create_action_buttons(self, parent):
        """Create the action buttons row."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(
            buttons_frame,
            text="📂 Open Output Folder",
            command=self._open_output_folder,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="Clear Status",
            command=self._clear_status,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="View Log File",
            command=self._view_log_file,
        ).pack(side=tk.LEFT, padx=5)

    def _setup_logging(self):
        """Set up logging to redirect to GUI."""
        # Create text handler for GUI
        self.text_handler = TextHandler(
            self.status_text,
            max_lines=GUI_DEFAULTS["max_log_lines"],
        )
        self.text_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(message)s")
        )

        # Attach to the processor logger
        processor_logger = logging.getLogger("setup_report_processor")
        processor_logger.addHandler(self.text_handler)

        # Set initial level
        self._toggle_verbose()

    def _on_files_added(self, paths):
        """
        Handle files being added to the queue.

        Args:
            paths: List of Path objects
        """
        self.file_list.add_files(paths)
        self._update_process_button()

    def _update_process_button(self):
        """Update the process button state."""
        if self.file_list.has_files() and not self.processing:
            self.process_button.config(state=tk.NORMAL)
        else:
            self.process_button.config(state=tk.DISABLED)

    def _browse_output_folder(self):
        """Open folder browser for output directory."""
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_dir_var.get(),
        )
        if folder:
            self.output_dir_var.set(folder)

    def _toggle_verbose(self):
        """Toggle verbose logging level."""
        logger = logging.getLogger("setup_report_processor")
        if self.verbose_var.get():
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def _start_processing(self):
        """Start processing the queued files."""
        # Validate options
        if not self.excel_var.get() and not self.csv_var.get() and not self.matlab_csv_var.get():
            messagebox.showwarning(
                "No Output Format",
                "Please select at least one output format (Excel, CSV, or MATLAB CSV).",
            )
            return

        # Get files
        files = self.file_list.get_files()
        if not files:
            return

        # Prepare options
        options = {
            "excel_enabled": self.excel_var.get(),
            "csv_enabled": self.csv_var.get(),
            "matlab_csv_enabled": self.matlab_csv_var.get(),
            "matlab_autolaunch": self.matlab_autolaunch_var.get(),
            "output_dir": Path(self.output_dir_var.get()),
            "verbose": self.verbose_var.get(),
        }

        # Update UI state
        self.processing = True
        self.process_button.config(text="⏹ Cancel", command=self._cancel_processing)
        self.progress_var.set(0)
        self.progress_label.config(text="Starting...")

        # Clear old messages
        self.text_handler.clear()

        # Start worker thread
        self.worker = ProcessorWorker(files, options, self.update_queue)
        self.worker.start()

    def _cancel_processing(self):
        """Cancel the current processing."""
        if self.worker:
            self.worker.cancel()
            self.processing = False
            self._reset_ui()

    def _poll_queue(self):
        """Poll the update queue for messages from worker thread."""
        try:
            while True:
                msg_type, msg_data = self.update_queue.get_nowait()

                if msg_type == "status":
                    self.progress_label.config(text=msg_data)

                elif msg_type == "progress":
                    progress, current, total = msg_data
                    self.progress_var.set(progress)
                    self.progress_label.config(
                        text=f"Processing... ({current}/{total} files)"
                    )

                elif msg_type == "success":
                    logging.info(msg_data)

                elif msg_type == "warning":
                    logging.warning(msg_data)

                elif msg_type == "error":
                    logging.error(msg_data)

                elif msg_type == "complete":
                    self._on_processing_complete()

        except queue.Empty:
            pass

        # Schedule next poll
        self.root.after(GUI_DEFAULTS["poll_interval_ms"], self._poll_queue)

    def _on_processing_complete(self):
        """Handle processing completion."""
        self.processing = False
        self._reset_ui()

        messagebox.showinfo(
            "Processing Complete",
            f"Successfully processed {len(self.file_list.get_files())} file(s).\n\n"
            f"Output saved to: {self.output_dir_var.get()}",
        )

    def _reset_ui(self):
        """Reset UI to ready state."""
        self.process_button.config(text="▶ Process Files", command=self._start_processing)
        self.progress_label.config(text="Ready")
        self._update_process_button()

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = Path(self.output_dir_var.get())

        if not output_dir.exists():
            messagebox.showwarning(
                "Folder Not Found",
                f"Output folder does not exist yet:\n{output_dir}",
            )
            return

        # Open folder in OS file explorer
        if sys.platform == "win32":
            os.startfile(output_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(output_dir)])
        else:
            subprocess.run(["xdg-open", str(output_dir)])

    def _clear_status(self):
        """Clear the status log."""
        self.text_handler.clear()

    def _view_log_file(self):
        """Open the log file in default text editor."""
        log_file = Path("setup_report_processor.log")

        if not log_file.exists():
            messagebox.showinfo(
                "No Log File",
                "Log file does not exist yet. Process some files first.",
            )
            return

        # Open file in default text editor
        if sys.platform == "win32":
            os.startfile(log_file)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(log_file)])
        else:
            subprocess.run(["xdg-open", str(log_file)])

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    app = SetupReportProcessorGUI()
    app.run()


if __name__ == "__main__":
    main()
