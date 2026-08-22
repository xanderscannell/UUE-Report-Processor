# Daily Setup Report Processor

A Python application that extracts event schedules from **Daily Setup Report PDFs** or the events database's **Daily Events Excel export** and generates chronologically sorted Excel/CSV outputs, with both CLI and GUI interfaces.

## Features

- **Two Event Sources**: Reads Daily Setup Report PDFs *or* Daily Events Excel exports — the type is detected from the file extension, and a single batch can mix both
- **Excel & CSV Output**: Generates professional schedule files
- **Interactive Gantt Chart**: Built-in timeline view of the day's events with a live current-time marker
- **Smart Location Filtering**: Configurable whitelist of venue locations
- **Chronological Sorting**: Automatically orders events by setup time
- **GUI Interface**: PySide6 desktop app — staged drag-and-drop workflow, live per-file
  status, results summary, custom light/dark theme, crisp on high-DPI/scaled displays
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

`gui_preferences.json` appears alongside these the first time you change a
setting — it remembers your output folder, chosen formats, and the Settings
menu toggles. Delete it to go back to defaults.

### First Launch

1. Extract the zip to any folder
2. Double-click `SetupReportProcessor.exe`
3. (Optional) Choose **Settings → Add desktop shortcut** for quick access

## GUI Usage

The window walks you through one step at a time — it starts as a drop target,
becomes a work queue once files are added, and ends on a summary of what was
produced.

1. **Add files**: Drop PDFs or Excel exports anywhere in the window, or click the drop zone to browse
2. **Choose output**: Toggle **Excel .xlsx** and/or **CSV .csv** — or leave both off
   for a timeline-only run (see below)
3. **Process**: Click **Process N files** — each file shows live status as it runs
4. **Finish**: The results screen reports files done, events found, and issues, with
   **View Timeline** and **Open Output Folder** right there

Anything that went wrong is summarized on a badge next to **Details** at the bottom
of the window; expand it for the full processing log.

### Timeline-only runs

If all you want is to look at the day's schedule, **untick both Excel and CSV**.
The button changes to **Preview N files** and the run produces no files at all —
not even an output folder. You still get the full results summary and the
**View Timeline** button.

Handy for checking a report before committing to a spreadsheet, or for glancing
at the day without leaving files behind.

### Event Timeline

Click **View Timeline** on the results screen to open the day's schedule as a Gantt chart:

- One horizontal bar per event, spanning setup time to closing time
- Bars are colored by building, with a legend; every bar is also labeled by
  location on the left. Colors are configurable — see **Building Colors** below
- Time-of-day axis covering 6 AM to midnight, widened automatically if events fall outside it
- A dashed line marks the current time, refreshing every minute
- Hover a bar for the event name, location, and exact times
- Process multiple reports to get a report selector for switching between days

To have it open automatically after every run, enable **Settings → Open timeline
when finished**.

### Settings menu

The **Settings** button in the header holds everything that isn't part of the
per-run workflow:

- **Location Whitelist…** — manage which venues are included
- **Building Colors…** — set the timeline color for each building
- **Output Folder…** — change where schedules are written
- **Open timeline when finished** / **Keep computer awake** / **Verbose logging** — preferences
- Preferences, the output folder, and the chosen formats are remembered between launches
- **Open log file** / **Add desktop shortcut**

### Location Whitelist

Open **Settings → Location Whitelist…** to manage which venue locations are included:

- **Check / uncheck** a location to include or exclude it without deleting it
- **Filter** the list by typing, useful once the list grows
- **Add location** / **Remove selected** to change the list itself

Unchecked locations are filtered out during processing. Changes are saved to
`location_config.json` when you click **Save changes**.

### Building Colors

Timeline bars are colored by the **building prefix** in the room name — `UC 1225`
is `UC`, `RUC 1171 (Lake Erie)` is `RUC`, `FCS 180` is `FCS`.

Open **Settings → Building Colors…** to change them. The list fills itself in: any
prefix that shows up in your whitelist or in a processed report is added
automatically with a color assigned, so a new campus building (CASL, ELB, …) works
with no update to the app. You can also rename a building to something friendlier
than its prefix — that name is what appears in the timeline legend.

**Two prefixes that mean the same building? Give them the same color.** `UC` and
`RUC` both refer to the Renick University Center — the building was renamed but
existing rooms kept their old names — so they ship sharing one color, and the
timeline shows them as a single legend entry. The same trick handles any future
rename.

Colors come from a fixed set chosen so bars stay distinguishable, including for
colorblind viewers, on both light and dark backgrounds. Options past the first
three are marked with `*`: once four or more buildings are on screen at once,
some pairs get hard to tell apart by color, and the location label on each bar is
what keeps them straight.

Assignments are saved to `location_config.json`, so a building keeps its color
from one report to the next.

## CLI Usage (Cross-Platform)

For automation, scripting, or non-Windows systems, use the command-line interface with Python:

```bash
# Process a PDF (generates Excel by default)
python setup_report_processor.py report.pdf

# Process a Daily Events Excel export — same options, same output
python setup_report_processor.py DailyEventsExcel.xlsx

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
                                  [--no-excel] [-v] report_file

positional arguments:
  report_file           Path to the report to process (.pdf or .xlsx)

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

1. **Pick a reader**: The file extension decides — `.pdf` uses the PDF parser,
   `.xlsx` uses the database export reader
2. **Read events**, which differs by source but produces the same records:
   - *PDF*: extracts text with pdfplumber, splits it into event blocks, and
     pulls out the event name, location, setup time, and closing time
   - *Excel*: reads one row per booking from each `Event List` sheet, taking the
     event name, `Location`, `Event Start`, and `Event End`
3. **Filter by Location**: Keeps only events at locations enabled in the whitelist
4. **Create Schedule**: Generates two rows per event (Setup Ready By + Closing)
5. **Sort Chronologically**: Orders all entries by time
6. **Export**: Saves to Excel and/or CSV, and/or displays the Gantt chart

> **A note on setup times.** The Excel export has no setup-start column, so for
> that source **Setup Ready By is the event's own start time**. A schedule built
> from an export therefore carries no setup lead time, and its Setup Ready By
> will be later than the same event's row from a PDF.

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
├── setup_report_processor.py     # Shared pipeline + PDF reader (CLI + library)
├── daily_events_excel.py         # Daily Events Excel export reader
├── gui_wrapper.py                # GUI application (PySide6)
├── gui_components/               # GUI component modules
│   ├── settings.py               #   GUI defaults and Gantt config
│   ├── preferences.py            #   Saved preferences (gui_preferences.json)
│   ├── keep_awake.py             #   Sleep/display inhibitor (Windows)
│   ├── theme.py                  #   Light/dark theme helpers
│   ├── drop_zone.py              #   Drag-and-drop zone
│   ├── file_list.py              #   File list manager
│   ├── log_handler.py            #   Log routing + display panel
│   ├── worker.py                 #   Background processing thread
│   ├── location_editor.py        #   Location whitelist editor
│   └── gantt_window.py           #   Embedded Gantt chart
├── location_config.json          # Location whitelist configuration
├── UUE.ico                       # Application icon
├── test_setup_report_processor.py # Test suite (87 tests)
├── requirements.txt              # Dependencies
├── build_release.bat             # Builds + zips the portable release
├── CHANGELOG.md                  # Release history
└── README.md                     # This file
```

## Dependencies

**Core**:
- pdfplumber (PDF text extraction)
- pandas (data manipulation)
- openpyxl (Excel export reading + file generation)

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
- For an Excel export, note it covers **all** campus locations, so most rows are
  expected to be filtered out. Add the rooms you want via
  **Settings → Location Whitelist…**

### An Excel export fails with "missing required column"
- The report definition changed. The reader needs `Event Start`, `Event End`,
  `Event Name` and `Location`; re-add whichever the message names
- Legacy `.xls` workbooks cannot be read — re-save the report as `.xlsx`

### Missing events in output
- Expand **Details** at the bottom of the window, or check the log file, for "Skipping event" or "not in whitelist" messages
- Open **Settings → Location Whitelist…** and verify the location is enabled

### Desktop shortcut opens wrong application
- Delete the old shortcut and recreate it from the GUI
- When running from Python (not the exe), the shortcut points to your Python interpreter

### Exe takes long to start
- Use the `--onedir` build (default) instead of `--onefile`
- `--onefile` extracts all dependencies on every launch, which is slow

## Version History

See [CHANGELOG.md](CHANGELOG.md) for the full release history.
The current release is **v4.2.0**.

## License

This script is provided as-is for internal use.
