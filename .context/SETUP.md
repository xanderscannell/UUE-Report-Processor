# Development Environment Setup

## Prerequisites

- Python 3.7+ (3.13 used in development)
- pip (comes with Python)
- Git

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd UUE

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Install GUI dependencies (optional)
pip install -r requirements-gui.txt
```

## Verify Installation

```bash
python test_installation.py
```

Expected output:
```
[OK] pdfplumber installed
[OK] pandas installed
[OK] openpyxl installed
[OK] pytest installed
```

## Running Locally

```bash
# CLI - process a single PDF
python setup_report_processor.py input/DailySetupReport.pdf

# CLI - with options
python setup_report_processor.py input/DailySetupReport.pdf --csv --verbose

# GUI - via batch file (Windows)
gui_wrapper.bat

# GUI - directly
python gui_wrapper.py
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

## Directory Structure

- `input/` — place PDF files here for processing
- `output/` — GUI saves output files here
- CLI saves output files to the current working directory

## Common Issues

### pdfplumber not found
**Fix**: Make sure you activated the virtual environment (`venv\Scripts\activate` on Windows) and ran `pip install -r requirements.txt`

### pytest not found
**Fix**: Install with `pip install pytest` or run via `python -m pytest`

### GUI drag-and-drop not working
**Fix**: Install tkinterdnd2 with `pip install tkinterdnd2`. The GUI will fall back to click-to-browse if this package is not available.
