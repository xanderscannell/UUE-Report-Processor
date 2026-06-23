# Setup Report Processor - GUI Edition

A drag-and-drop desktop interface (PySide6) for processing Daily Setup Report PDFs.

## Quick Start

### Portable app (Windows, recommended)

1. Extract `SetupReportProcessor.zip`
2. Double-click `SetupReportProcessor.exe`
3. Drag PDF files into the window
4. Choose output options (Excel / CSV / Gantt)
5. Click **Process Files**

### From source

- **Windows:** double-click [`gui_wrapper.bat`](../gui_wrapper.bat) (sets up a venv and installs dependencies on first run)
- **Linux/Mac:** run [`./gui_wrapper.sh`](../gui_wrapper.sh)
- **Any platform:** `python gui_wrapper.py` (after `pip install -r requirements.txt`)

Processed schedules are saved to the `output` folder by default.

---

## Features

- **Drag-and-drop interface** - drag PDF files into the window (native, no extra setup)
- **Batch processing** - queue and process multiple PDFs at once
- **Flexible output** - Excel, CSV, and/or an interactive Gantt chart
- **Embedded Gantt chart** - timeline of the day's events with a live current-time marker
- **Real-time feedback** - progress bar and live, color-coded status log
- **High-DPI crisp rendering** - sharp on scaled displays; follows the system light/dark theme
- **Location whitelist editor** - manage which venues are included, in-app

---

## Interface Guide

### 1. Drag-and-drop zone (top)
- Drag PDFs here, or click to browse
- Accepts multiple `.pdf` files at once

### 2. File queue
- Lists all queued PDFs
- **Remove Selected** removes one file; **Clear All** empties the queue
- Double-click a file to remove it

### 3. Output options
- **Excel (.xlsx)** - schedule spreadsheet (on by default)
- **CSV (.csv)** - schedule as CSV
- **Auto-launch Gantt Chart** - open the timeline chart automatically when processing finishes
- At least one output must be selected to process
- **Output Folder** - defaults to `./output/`; click **Browse...** to change (created automatically)
- **Location Whitelist...** - open the editor to manage included venues
- **Verbose Logging** - show detailed debug output in the status log

### 4. Process button
- **Process Files** starts processing; changes to **Cancel** while running
- Disabled when the queue is empty

### 5. Progress bar
- Overall progress and an "X/Y files" counter

### 6. Status log
- Real-time messages, color-coded and theme-aware (readable in light or dark mode):
  - default text color - information
  - amber - warnings
  - red - errors
- Auto-scrolls to the latest message

### 7. Action buttons
- **Open Output Folder** - open the output folder in your file manager
- **View Gantt** - open the Gantt chart (enabled once a file has been processed)
- **Clear Status** - clear the status log
- **View Log File** - open the detailed log file
- **Add Desktop Shortcut** - create a desktop shortcut to the app

---

## Gantt Chart

Open it with **View Gantt**, or enable **Auto-launch Gantt Chart** before processing.

- One horizontal bar per event, from setup time to closing time
- Time-of-day axis from 6 AM to midnight; events labeled by location
- The report date is shown as the chart title (e.g. "Tuesday, Jun 23 2026")
- A red vertical line marks the current time and refreshes every minute
- The view is fixed (no accidental panning or zooming)
- Process several PDFs at once to get a **Report** selector for switching between days

---

## Location Whitelist

Click **Location Whitelist...** to control which venues appear in the output:

- **Add** - create a new location entry
- **Toggle** - enable/disable a location without removing it (double-click also toggles)
- **Remove** - delete a location

Disabled locations are filtered out during processing. Changes are saved to
`location_config.json` and apply to newly processed files. No code editing required.

---

## Troubleshooting

**GUI won't launch**
- Ensure Python 3.10+ is installed and on your PATH (`python --version`)
- From source, try `python gui_wrapper.py` directly to see the error

**No events found**
- Enable **Verbose Logging** and process again, then check the status log
- A location may be disabled in the whitelist, or the PDF format may differ
- Click **View Log File** for full details

**Processing fails for a file**
- Check the status log for the specific error
- Verify the PDF isn't corrupted and opens in a PDF reader
- Try processing one file at a time with Verbose Logging on

**Output folder not found**
- Process at least one file first; the folder is created on first run

---

## Files Created

- `output/` - default output folder for schedules
- `setup_report_processor.log` - detailed processing log

All processing happens locally on your computer; no data is sent anywhere.

---

## FAQ

**Can I process multiple PDFs at once?**
Yes - drag several in, or Ctrl+Click multiple files when browsing.

**Can I get both Excel and CSV?**
Yes - check both. You can also add the Gantt chart, or pick any combination.

**Where are outputs saved?**
In `output/` by default; click **Browse...** to change.

**Can I customize which locations are included?**
Yes - use the **Location Whitelist...** editor (no code editing needed).

**Can I cancel processing?**
Yes - click **Cancel** (the Process button becomes Cancel while running).

---

## Dependencies

- pdfplumber, pandas, openpyxl (core processing)
- PySide6 (Qt desktop interface)
- pyqtgraph (Gantt chart rendering)

---

For command-line usage, see [README.md](../README.md).
