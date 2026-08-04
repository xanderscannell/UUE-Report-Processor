# Quick Start Guide
## Setup Report Processor

### Installation (5 minutes)

> Just want the app? Grab `SetupReportProcessor.zip`, extract, and double-click
> the `.exe` — no Python needed. See [README_GUI.md](README_GUI.md).
> The steps below are for running from source or using the command line.

1. **Install Python** (if not already installed)
   - Download from https://python.org
   - Version 3.9 or higher required (PySide6 needs it)
   - Make sure to check "Add Python to PATH" during installation

2. **Set up the project**
   ```bash
   # Create and activate virtual environment (recommended)
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Mac/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Test installation**
   ```bash
   python test_installation.py
   ```

### Basic Usage

**Launch the desktop app:**
```bash
# Windows:
gui_wrapper.bat

# Any platform, with the venv activated:
python gui_wrapper.py
```
Drop PDFs in, pick Excel and/or CSV, click Process. Full walkthrough in
[README_GUI.md](README_GUI.md).

**Process a single PDF:**
```bash
python setup_report_processor.py your_report.pdf
```
This generates: `your_report_schedule.xlsx`

**Process with custom name:**
```bash
python setup_report_processor.py report.pdf -o weekly_schedule.xlsx
```

**Generate both Excel and CSV:**
```bash
python setup_report_processor.py report.pdf --csv
```

**Process all PDFs in a folder:**
```bash
# Windows:
batch_process.bat

# Mac/Linux:
./batch_process.sh
```

### What it Does

1. Extracts events from Daily Setup Report PDFs
2. Filters events by location, using the whitelist in `location_config.json`
   (editable in the app under Settings → Location Whitelist…)
3. Creates two entries per event:
   - Setup Ready By time
   - Closing time
4. Sorts everything chronologically
5. Exports to Excel/CSV

### Output Format

| Event Name | Location | Activity | Time |
|------------|----------|----------|------|
| Book Club Meeting | UC 1227 | Setup Ready By | 11:30 AM |
| Book Club Meeting | UC 1227 | Closing | 2:00 PM |

### Troubleshooting

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**No output files generated:**
- Check that PDF path is correct
- Run with `--verbose` flag for details
- Check `setup_report_processor.log`

**Need help?**
- Read the full `README.md`
- Check the log file: `setup_report_processor.log`

### Files Included

- `setup_report_processor.py` - Main script
- `gui_wrapper.py` / `gui_wrapper.bat` - Desktop app and its launcher
- `location_config.json` - Location whitelist and building colors
- `requirements.txt` - Python dependencies
- `README.md` - Complete documentation
- `documentation/README_GUI.md` - Desktop app guide
- `test_installation.py` - Test your setup
- `batch_process.bat` - Windows batch processor
- `batch_process.sh` - Mac/Linux batch processor

---

**Ready to go!**

For full documentation, see README.md
