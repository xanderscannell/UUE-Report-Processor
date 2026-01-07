# Daily Setup Report Processor

A production-ready Python script for extracting event schedules from Daily Setup Report PDFs and generating chronologically sorted Excel/CSV schedules.

## Features

✨ **Automated PDF Processing**: Extracts event data from complex PDF reports  
📊 **Excel & CSV Output**: Generates professional schedule files  
🔍 **Smart Filtering**: Filters events by location with configurable rules  
⏰ **Chronological Sorting**: Automatically orders events by time  
📝 **Detailed Logging**: Complete audit trail of processing steps  
🛡️ **Error Handling**: Robust error handling with helpful messages  

## Quick Start

### 1. Installation

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

```bash
# Process a PDF (generates Excel by default)
python setup_report_processor.py DailySetupReport__19_.pdf

# Specify custom output name
python setup_report_processor.py report.pdf -o my_schedule.xlsx

# Generate both Excel and CSV
python setup_report_processor.py report.pdf --csv

# Verbose output (for debugging)
python setup_report_processor.py report.pdf --verbose
```

## How It Works

The script performs the following steps:

1. **Extract Text**: Reads all text from the PDF using pdfplumber
2. **Parse Events**: Identifies event blocks and extracts:
   - Event name
   - Location
   - Setup Ready By time
   - Closing time (event end time)
3. **Filter by Location**: Keeps only events at these locations:
   - UC (University Center)
   - RUC (Renovated University Center)
   - FCS Michigan Room
   - FCS 180
   - FCS Dining Rm D
4. **Create Schedule**: Generates two rows per event:
   - One for "Setup Ready By" time
   - One for "Closing" time
5. **Sort Chronologically**: Orders all entries by time
6. **Export**: Saves to Excel and/or CSV

## Output Format

The generated schedule has 4 columns:

| Event Name | Location | Activity | Time |
|------------|----------|----------|------|
| Book Club January Meeting | UC 1227 Conference | Setup Ready By | 11:30 AM |
| Book Club January Meeting | UC 1227 Conference | Closing | 2:00 PM |
| Ratio Christi Event 1 | UC 1225 Cluster | Setup Ready By | 2:15 PM |
| ... | ... | ... | ... |

## Command-Line Options

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

## Examples

### Example 1: Basic Processing
```bash
python setup_report_processor.py DailySetupReport__19_.pdf
```
Output: `DailySetupReport__19__schedule.xlsx`

### Example 2: Custom Output Name
```bash
python setup_report_processor.py report.pdf -o weekly_schedule.xlsx
```
Output: `weekly_schedule.xlsx`

### Example 3: Generate Both Formats
```bash
python setup_report_processor.py report.pdf --csv
```
Output: 
- `report_schedule.xlsx`
- `report_schedule.csv`

### Example 4: CSV Only
```bash
python setup_report_processor.py report.pdf --csv --no-excel
```
Output: `report_schedule.csv`

### Example 5: Verbose Mode (Debugging)
```bash
python setup_report_processor.py report.pdf --verbose
```
Shows detailed processing information and saves detailed logs.

## Logging

The script creates a log file `setup_report_processor.log` containing:
- Timestamp of each operation
- Number of events found
- Warnings about skipped events
- Error messages (if any)

Example log output:
```
2026-01-07 14:30:15 - INFO - Initialized processor for: DailySetupReport__19_.pdf
2026-01-07 14:30:15 - INFO - Extracting text from PDF...
2026-01-07 14:30:16 - INFO - Successfully extracted 12450 characters from PDF
2026-01-07 14:30:16 - INFO - Parsing events from text...
2026-01-07 14:30:16 - INFO - Found 15 total events in PDF
2026-01-07 14:30:16 - DEBUG - Skipping event 'M. Hockey Practice' - location 'FH Ice Arena' does not match criteria
...
```

## Customizing Location Filters

To modify which locations are included/excluded, edit the script's class variables:

```python
class SetupReportProcessor:
    # Add or remove location prefixes
    VALID_LOCATION_PREFIXES = [
        "UC ",
        "RUC ",
        "FCS Michigan",
        "FCS 180",
        "FCS Dining Rm D"
    ]
    
    # Add or remove excluded locations
    EXCLUDED_LOCATIONS = [
        "UC Table-Bake/Day Sale",
        "UC Table-Info",
    ]
```

## Troubleshooting

### Issue: "PDF file not found"
**Solution**: Check that the PDF path is correct and the file exists.

### Issue: "No valid events found"
**Possible causes**:
- PDF format has changed
- All events are filtered out by location rules
- PDF is empty or corrupted

**Solution**: Run with `--verbose` flag to see detailed processing logs.

### Issue: Excel file won't open
**Possible causes**:
- File is still being written
- Insufficient disk space
- File already open in Excel

**Solution**: Close Excel, ensure disk space, and try again.

### Issue: Missing events in output
**Possible causes**:
- Events don't match location filters
- Event format is non-standard

**Solution**: Check log file for "Skipping event" messages. The log shows why events were excluded.

## Requirements

- Python 3.7 or higher
- Operating System: Windows, macOS, or Linux
- ~50MB disk space for dependencies

## Dependencies

- **pdfplumber**: PDF text extraction
- **pandas**: Data manipulation
- **openpyxl**: Excel file generation

See `requirements.txt` for specific versions.

## File Structure

```
.
├── setup_report_processor.py    # Main script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── setup_report_processor.log   # Generated log file
```

## Advanced Usage

### Batch Processing Multiple PDFs

Create a simple bash script (Linux/Mac) or batch file (Windows):

**Linux/Mac** (`process_all.sh`):
```bash
#!/bin/bash
for pdf in *.pdf; do
    echo "Processing $pdf..."
    python setup_report_processor.py "$pdf"
done
```

**Windows** (`process_all.bat`):
```batch
@echo off
for %%f in (*.pdf) do (
    echo Processing %%f...
    python setup_report_processor.py "%%f"
)
```

### Integration with Other Scripts

```python
from setup_report_processor import SetupReportProcessor

# Process PDF
processor = SetupReportProcessor('report.pdf')
df = processor.process()

# Now you can manipulate the DataFrame
print(df.head())
df.to_json('output.json', orient='records')
```

## Performance

- **Small PDFs** (1-10 pages): < 1 second
- **Medium PDFs** (10-50 pages): 1-5 seconds
- **Large PDFs** (50+ pages): 5-15 seconds

## License

This script is provided as-is for internal use.

## Support

For issues or questions:
1. Check the log file: `setup_report_processor.log`
2. Run with `--verbose` flag for detailed output
3. Review this README for common solutions

## Version History

- **v1.0.0** (2026-01-07): Initial production release
  - PDF text extraction
  - Location-based filtering
  - Chronological sorting
  - Excel/CSV export
  - Comprehensive logging

---

**Happy Scheduling! 📅**
