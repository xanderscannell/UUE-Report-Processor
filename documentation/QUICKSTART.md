# Quick Start Guide
## Setup Report Processor

### Installation (5 minutes)

1. **Install Python** (if not already installed)
   - Download from https://python.org
   - Version 3.7 or higher required
   - ✓ Make sure to check "Add Python to PATH" during installation

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

1. ✓ Extracts events from Daily Setup Report PDFs
2. ✓ Filters events by location (UC, RUC, FCS Michigan, FCS 180, FCS Dining Rm D)
3. ✓ Creates two entries per event:
   - Setup Ready By time
   - Closing time
4. ✓ Sorts everything chronologically
5. ✓ Exports to Excel/CSV

### Output Format

| Event Name | Location | Activity | Time |
|------------|----------|----------|------|
| Book Club Meeting | UC 1227 | Setup Ready By | 11:30 AM |
| Book Club Meeting | UC 1227 | Closing | 2:00 PM |

See `example_output.xlsx` for a complete example!

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
- `requirements.txt` - Python dependencies
- `README.md` - Complete documentation
- `test_installation.py` - Test your setup
- `batch_process.bat` - Windows batch processor
- `batch_process.sh` - Mac/Linux batch processor
- `example_output.xlsx` - Sample output
- `example_output.csv` - Sample output

---

**Ready to go!** 🚀

For full documentation, see README.md
