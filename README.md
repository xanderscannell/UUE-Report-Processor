# Daily Setup Report Processor

A Python application that extracts event schedules from Daily Setup Report PDFs and generates chronologically sorted Excel/CSV outputs, with both CLI and GUI interfaces.

## Features

- **Automated PDF Processing**: Extracts event data from Daily Setup Report PDFs
- **Excel & CSV Output**: Generates professional schedule files
- **Smart Location Filtering**: Configurable whitelist of venue locations
- **Chronological Sorting**: Automatically orders events by setup time
- **GUI Interface**: Drag-and-drop desktop app with batch processing
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
2. **Select Output**: Choose Excel, CSV, or both
3. **Process**: Click **Process Files** to generate schedules
4. **View Output**: Click **Open Output Folder** to see results

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
6. **Export**: Saves to Excel and/or CSV

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
pip install -r requirements-gui.txt  # Optional: enhanced drag-and-drop

# Run tests
python -m pytest test_setup_report_processor.py -v

# Run the GUI
python gui_wrapper.py
```

### Building the Portable Exe

```bash
pip install pyinstaller
pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py
cp location_config.json dist/SetupReportProcessor/
```

Then zip the `dist/SetupReportProcessor/` folder for distribution.

## File Structure

```
.
├── setup_report_processor.py     # Core processor (CLI + library)
├── gui_wrapper.py                # GUI application
├── gui_components/               # GUI component modules
│   ├── settings.py               #   GUI defaults and colors
│   ├── drop_zone.py              #   Drag-and-drop zone
│   ├── file_list.py              #   File list manager
│   ├── log_handler.py            #   Log text handler
│   └── location_editor.py        #   Location whitelist editor
├── location_config.json          # Location whitelist configuration
├── UUE.ico                       # Application icon
├── test_setup_report_processor.py # Test suite (49 tests)
├── requirements.txt              # Core dependencies
├── requirements-gui.txt          # GUI-specific dependencies
└── README.md                     # This file
```

## Dependencies

**Core**:
- pdfplumber (PDF text extraction)
- pandas (data manipulation)
- openpyxl (Excel file generation)

**GUI** (optional):
- tkinterdnd2 (enhanced drag-and-drop)

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
