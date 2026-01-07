# Testing Guide

Quick guide for testing the improved Setup Report Processor.

---

## Pre-Testing Setup

### 1. Install Dependencies (if needed)
```bash
# Install all dependencies including test tools
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
python test_installation.py
```

Expected output:
```
[OK] pdfplumber installed
[OK] pandas installed
[OK] openpyxl installed
[OK] pytest installed
[SUCCESS] All tests passed!
```

---

## Running Unit Tests

### Basic Test Run
```bash
# Run all tests with verbose output
pytest test_setup_report_processor.py -v
```

Expected: All tests should pass ✓

### Test with Coverage
```bash
# Generate coverage report
pytest test_setup_report_processor.py --cov=setup_report_processor --cov-report=term-missing

# Generate HTML coverage report
pytest test_setup_report_processor.py --cov=setup_report_processor --cov-report=html
# Then open: htmlcov/index.html
```

### Run Specific Test Classes
```bash
# Test only time parsing
pytest test_setup_report_processor.py::TestTimeParser -v

# Test only location validation
pytest test_setup_report_processor.py::TestLocationValidation -v

# Test only initialization
pytest test_setup_report_processor.py::TestInitialization -v
```

### Run Specific Test Methods
```bash
# Test a single method
pytest test_setup_report_processor.py::TestTimeParser::test_parse_standard_time_format -v
```

---

## Testing the Main Script

### 1. Test with Valid PDF
```bash
# Basic processing (assuming you have a PDF)
python setup_report_processor.py DailySetupReport__19_.pdf

# With verbose logging (see enhanced details)
python setup_report_processor.py DailySetupReport__19_.pdf --verbose

# Generate both Excel and CSV
python setup_report_processor.py DailySetupReport__19_.pdf --csv
```

**What to verify**:
- ✓ Processing completes without errors
- ✓ Excel file is generated
- ✓ Data looks correct (compare with previous version)
- ✓ Log file contains detailed information

### 2. Test File Validation (New Feature)
```bash
# Should fail with clear error message
python setup_report_processor.py README.md
```

Expected output:
```
ERROR: Expected PDF file, got: .md
```

### 3. Test with Non-Existent File
```bash
python setup_report_processor.py nonexistent.pdf
```

Expected output:
```
ERROR: PDF file not found: nonexistent.pdf
```

---

## Comparing Outputs

### Check Output Format Hasn't Changed
```bash
# Process the same PDF you used before
python setup_report_processor.py your_report.pdf -o new_output.xlsx

# Compare with previous output
# Open both in Excel and verify:
# 1. Same number of rows
# 2. Same column structure
# 3. Same data values
# 4. Same chronological ordering
```

### Check Log File
```bash
# View the log file
cat setup_report_processor.log
# or on Windows:
type setup_report_processor.log

# Look for enhanced logging messages like:
# "Found X rows with invalid times:"
# "  - Event: 'EventName', Activity: Setup Ready By, Time: '...'"
```

---

## Performance Testing

### Test Processing Speed
```bash
# Time the processing (Linux/Mac)
time python setup_report_processor.py your_report.pdf

# Time the processing (Windows PowerShell)
Measure-Command { python setup_report_processor.py your_report.pdf }
```

**Expected performance** (compared to previous version):
- Small PDFs: No noticeable difference
- Large PDFs: ~20% faster due to memory optimization

---

## Edge Case Testing

### Test Empty/Malformed PDFs
```bash
# Create a test PDF or use one with unusual formatting
python setup_report_processor.py edge_case.pdf --verbose
```

Check that:
- ✓ Script doesn't crash
- ✓ Error messages are helpful
- ✓ Log file shows what went wrong

---

## Regression Testing Checklist

Compare outputs with the previous version:

- [ ] Same number of events extracted
- [ ] Same event names (no extra/missing characters)
- [ ] Same locations (properly cleaned)
- [ ] Same times (correctly parsed)
- [ ] Chronological order maintained
- [ ] Excel format unchanged
- [ ] CSV format unchanged
- [ ] Log file created
- [ ] No crashes or unexpected errors

---

## Testing New Features

### 1. Enhanced Logging
```bash
# Run with verbose mode
python setup_report_processor.py your_report.pdf --verbose

# Check log file for detailed messages
cat setup_report_processor.log
```

**Look for**:
- Detailed event parsing logs
- Specific information about skipped events
- Clear error messages with context

### 2. Better Error Messages
```bash
# Test file validation
python setup_report_processor.py not_a_pdf.txt

# Should see: "Expected PDF file, got: .txt"
```

### 3. Improved Performance
```bash
# Process a large PDF and note the time
# Compare with previous version if possible
```

---

## Automated Testing Script

Create a quick test script:

**test_all.sh** (Linux/Mac):
```bash
#!/bin/bash
echo "Running installation test..."
python test_installation.py || exit 1

echo ""
echo "Running unit tests..."
pytest test_setup_report_processor.py -v || exit 1

echo ""
echo "Testing with sample PDF..."
python setup_report_processor.py DailySetupReport__19_.pdf || exit 1

echo ""
echo "All tests passed!"
```

**test_all.bat** (Windows):
```batch
@echo off
echo Running installation test...
python test_installation.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo Running unit tests...
pytest test_setup_report_processor.py -v
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo Testing with sample PDF...
python setup_report_processor.py DailySetupReport__19_.pdf
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo All tests passed!
```

---

## Troubleshooting Test Failures

### If pytest is not found:
```bash
pip install pytest pytest-cov
```

### If tests fail:
1. Check Python version (should be 3.10+)
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check that you're in the correct directory
4. Run with verbose output: `pytest -v -s`

### If processing fails:
1. Run with `--verbose` flag
2. Check the log file: `setup_report_processor.log`
3. Verify PDF is not corrupted
4. Test with a simple/small PDF first

---

## Success Criteria

The improvements are successful if:

✅ All unit tests pass
✅ Installation test passes
✅ Processing produces same output as before
✅ Performance is same or better
✅ Error messages are clearer
✅ Log file has more details
✅ No new bugs introduced

---

## Quick Test Commands

```bash
# Complete test suite (run this before deploying)
python test_installation.py && \
pytest test_setup_report_processor.py -v && \
python setup_report_processor.py your_report.pdf --verbose

# Or just the essentials
pytest test_setup_report_processor.py -v
python setup_report_processor.py your_report.pdf
```

---

## Next Steps After Testing

Once all tests pass:

1. ✅ Archive old version as backup
2. ✅ Deploy new version
3. ✅ Update documentation if needed
4. ✅ Commit changes to git
5. ✅ Create a release tag (e.g., v1.1.0)

---

*Last updated: 2026-01-07*
