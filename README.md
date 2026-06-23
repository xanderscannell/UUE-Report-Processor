# Daily Setup Report Processor

A Python application that extracts event schedules from Daily Setup Report PDFs and generates chronologically sorted Excel/CSV outputs, with both CLI and GUI interfaces.

## Features

- **Automated PDF Processing**: Extracts event data from Daily Setup Report PDFs
- **Excel & CSV Output**: Generates professional schedule files
- **Interactive Gantt Chart**: Built-in timeline view of the day's events with a live current-time marker
- **Smart Location Filtering**: Configurable whitelist of venue locations
- **Chronological Sorting**: Automatically orders events by setup time
- **GUI Interface**: PySide6 desktop app — drag-and-drop, batch processing, crisp on high-DPI/scaled displays, follows system light/dark theme
- **Location Editor**: Built-in GUI for managing the location whitelist
- **Desktop Shortcut**: One-click shortcut creation from the app
- **Portable Distribution**: Runs as a standalone `.exe` with no Python required
- **Detailed Logging**: Complete audit trail of processing steps

## Portable App (Recommended — Windows Only)

Download the latest `SetupReportProcessor.zip`, extract it, and double-click `SetupReportProcessor.exe`. No installation required.

The folder contains:
```
SetupReportProcessor/
  SetupReportProcessor.exe    # Main application
  location_config.json        # Location whitelist (editable via GUI)
  _internal/                  # Application dependencies
```

### First Launch

1. Extract the zip to any folder
2. Double-click `SetupReportProcessor.exe`
3. (Optional) Click **Add Desktop Shortcut** for quick access

## GUI Usage

The GUI provides drag-and-drop PDF processing:

1. **Add Files**: Drag PDF files onto the drop zone, or click to browse
2. **Select Output**: Choose Excel, CSV, and/or **Auto-launch Gantt Chart** (at least one output is required)
3. **Process**: Click **Process Files** to generate schedules
4. **View Output**: Click **Open Output Folder** for the files, or **View Gantt** for the timeline chart

### Gantt Chart

Click **View Gantt** (or enable **Auto-launch Gantt Chart** before processing) to open the event timeline:

- One horizontal bar per event, spanning setup time to closing time
- Time-of-day axis from 6 AM to midnight; events labeled by location
- A live red line marks the current time, refreshing every minute
- Process multiple PDFs to get a report selector for switching between days

### Location Whitelist

Click **Location Whitelist...** to manage which venue locations are included in the output:

- **Add**: Create new location entries with custom names
- **Toggle**: Enable/disable locations without removing them
- **Remove**: Delete locations you no longer need

Disabled locations are filtered out during processing. Changes are saved to `location_config.json`.

## CLI Usage (Cross-Platform)

For automation, scripting, or non-Windows systems, use the command-line interface with Python:

```bash
# Process a PDF (generates Excel by default)
python setup_report_processor.py report.pdf

# Specify custom output name
python setup_report_processor.py report.pdf -o my_schedule.xlsx

# Generate both Excel and CSV
python setup_report_processor.py report.pdf --csv

# CSV only
python setup_report_processor.py report.pdf --csv --no-excel

# Verbose output (for debugging)
python setup_report_processor.py report.pdf --verbose
```

### Command-Line Options

```
usage: setup_report_processor.py [-h] [-o OUTPUT] [--excel] [--csv]
                                  [--no-excel] [-v] pdf_file

positional arguments:
  pdf_file              Path to the PDF file to process

optional arguments:
  -h, --help            Show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path (auto-generated if not specified)
  --excel               Generate Excel output (default: True)
  --csv                 Generate CSV output (default: False)
  --no-excel            Disable Excel output
  -v, --verbose         Enable verbose logging (DEBUG level)
```

## How It Works

1. **Extract Text**: Reads all text from the PDF using pdfplumber
2. **Parse Events**: Identifies event blocks and extracts event name, location, setup time, and closing time
3. **Filter by Location**: Keeps only events at locations enabled in the whitelist
4. **Create Schedule**: Generates two rows per event (Setup Ready By + Closing)
5. **Sort Chronologically**: Orders all entries by time
6. **Export**: Saves to Excel and/or CSV, and/or displays the Gantt chart

## Output Format

| Event Name | Location | Activity | Time |
|------------|----------|----------|------|
| Book Club January Meeting | UC 1227 | Setup Ready By | 11:30 AM |
| Book Club January Meeting | UC 1227 | Closing | 2:00 PM |
| Ratio Christi Event 1 | UC 1225 | Setup Ready By | 2:15 PM |

## Location Configuration

Locations are managed via `location_config.json` (or through the GUI editor):

```json
{
  "version": 2,
  "locations": [
    {"name": "UC 1225", "enabled": true},
    {"name": "UC Table-Info", "enabled": false}
  ]
}
```

- `enabled: true` — location is included in processing
- `enabled: false` — location is excluded (filtered out)

## Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd UUE

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest test_setup_report_processor.py -v

# Run the GUI
python gui_wrapper.py
```

### Building the Portable Exe

On Windows, run the build script:

```bat
build_release.bat /deps
```

This installs dependencies, runs PyInstaller, copies `location_config.json` and `UUE.ico` next to the exe, and produces `SetupReportProcessor.zip` ready for distribution. (Omit `/deps` to skip the dependency install on rebuilds.)

To build manually:

```bash
pip install pyinstaller
pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py
cp location_config.json UUE.ico dist/SetupReportProcessor/
```

Then zip the `dist/SetupReportProcessor/` folder for distribution.

## File Structure

```
.
├── setup_report_processor.py     # Core processor (CLI + library)
├── gui_wrapper.py                # GUI application (PySide6)
├── gui_components/               # GUI component modules
│   ├── settings.py               #   GUI defaults and Gantt config
│   ├── theme.py                  #   Light/dark theme helpers
│   ├── drop_zone.py              #   Drag-and-drop zone
│   ├── file_list.py              #   File list manager
│   ├── log_handler.py            #   Log routing + display panel
│   ├── worker.py                 #   Background processing thread
│   ├── location_editor.py        #   Location whitelist editor
│   └── gantt_window.py           #   Embedded Gantt chart
├── location_config.json          # Location whitelist configuration
├── UUE.ico                       # Application icon
├── test_setup_report_processor.py # Test suite (49 tests)
├── requirements.txt              # Dependencies
├── build_release.bat             # Builds + zips the portable release
└── README.md                     # This file
```

## Dependencies

**Core**:
- pdfplumber (PDF text extraction)
- pandas (data manipulation)
- openpyxl (Excel file generation)

**GUI**:
- PySide6 (Qt desktop interface)
- pyqtgraph (Gantt chart rendering)

**Build** (optional):
- PyInstaller (portable exe generation)

## Troubleshooting

### No valid events found
- Run with `--verbose` to see which events are being filtered and why
- Check the location whitelist — locations may be disabled
- The PDF format may have changed

### Missing events in output
- Check the log file for "Skipping event" or "not in whitelist" messages
- Open the Location Whitelist editor and verify the location is enabled

### Desktop shortcut opens wrong application
- Delete the old shortcut and recreate it from the GUI
- When running from Python (not the exe), the shortcut points to your Python interpreter

### Exe takes long to start
- Use the `--onedir` build (default) instead of `--onefile`
- `--onefile` extracts all dependencies on every launch, which is slow

## Version History

- **v3.0.0** (2026-06-23): PySide6 rewrite + embedded Gantt chart
  - Migrated the GUI from tkinter to PySide6 — crisp high-DPI rendering, native drag-and-drop, and automatic light/dark theme support
  - Replaced the external MATLAB Gantt app with a built-in pyqtgraph chart (live current-time marker), opened via **View Gantt** or auto-launched on completion
  - Added the **Auto-launch Gantt Chart** output option; at least one output (Excel/CSV/Gantt) is now required to process
  - Removed the MATLAB CSV output and the `--matlab-*` CLI flags
  - Added `build_release.bat` for one-step portable-release builds
- **v2.0.0** (2026-02-11): GUI Release
  - Desktop GUI with drag-and-drop file processing
  - Location whitelist editor (add/remove/toggle locations)
  - Portable `.exe` distribution via PyInstaller
  - Desktop shortcut creation with custom icon
  - Location config v2 format (replaces separate whitelist/blacklist)
  - 49 passing tests
- **v1.0.0** (2026-01-07): Initial production release
  - PDF text extraction
  - Location-based filtering
  - Chronological sorting
  - Excel/CSV export
  - Comprehensive logging

## License

This script is provided as-is for internal use.
