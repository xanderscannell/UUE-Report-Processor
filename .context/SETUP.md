# Development Environment Setup

## Prerequisites

- Python 3.9+ (3.13 used in development) — required by PySide6
- pip (comes with Python)
- Git

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd UUE-Report-Processor

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install all dependencies (processor, GUI, and test tooling)
pip install -r requirements.txt
```

`requirements.txt` is the only requirements file — GUI dependencies (PySide6,
pyqtgraph) are in it alongside the processor's.

## Verify Installation

```bash
python test_installation.py
```

Expected output:
```
[OK] pdfplumber installed
[OK] pandas installed
[OK] openpyxl installed
[OK] PySide6 installed
[OK] pyqtgraph installed
[OK] pytest installed
```

## Running Locally

```bash
# GUI - via batch file (Windows; creates the venv on first run)
gui_wrapper.bat

# GUI - directly, with the venv activated
python gui_wrapper.py

# CLI - process a single PDF
python setup_report_processor.py DailySetupReport.pdf

# CLI - with options
python setup_report_processor.py DailySetupReport.pdf --csv --verbose
```

## Running Tests

```bash
# All tests
python -m pytest test_setup_report_processor.py -v

# Specific test class
python -m pytest test_setup_report_processor.py::TestTimeParser -v

# With coverage
python -m pytest test_setup_report_processor.py --cov=setup_report_processor --cov-report=html
```

## Reviewing the GUI without a real PDF

The UI can be driven headlessly to check a visual change. Queued file paths do
not need to exist:

```python
from PySide6.QtWidgets import QApplication
from gui_components import apply_theme
import gui_wrapper, sys
from pathlib import Path

app = QApplication(sys.argv)
apply_theme(app)                      # pass dark=True/False to force a scheme
w = gui_wrapper.MainWindow()
w.show(); app.processEvents()

w._on_files_added([Path("Daily Setup Report 06-23-26.pdf")])   # workspace stage
w._show_running(True)                                          # progress stage
w.grab().save("shot.png")
```

`ResultPanel.set_results({...})` plus `w._set_stage(2)` renders the results
stage. Note that Qt's `offscreen` platform plugin has no font directory on
Windows and renders text as boxes — grab from a normally shown window instead.

## Files and Directories

- `output/` — GUI saves output files here by default (configurable in the app)
- `location_config.json` — location whitelist and building colors, both managed
  from the GUI's Settings menu
- CLI saves output files to the current working directory

## Common Issues

### pdfplumber not found
**Fix**: Make sure you activated the virtual environment (`venv\Scripts\activate` on Windows) and ran `pip install -r requirements.txt`

### pytest not found
**Fix**: Install with `pip install pytest` or run via `python -m pytest`

### GUI colors look half light, half dark
**Fix**: A custom-painted widget is reading the OS scheme instead of the app's.
Widgets must take colors from `style.tokens()`, which returns the scheme
`apply_theme()` actually applied — never from `is_dark_mode()` directly.

### A building shows up gray on the timeline
**Fix**: Its room-name prefix has no color assigned yet. Open
Settings → Building Colors…; the prefix is added automatically and can be given
a color there. See ADR-006.
