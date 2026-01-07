# Setup Report Processor - GUI Edition

Easy-to-use drag-and-drop desktop interface for processing Daily Setup Report PDFs.

## Quick Start

### Windows
1. Double-click [`gui_wrapper.bat`](gui_wrapper.bat)
2. Wait for automatic setup (first time only)
3. Drag PDF files into the window
4. Choose output options (Excel/CSV)
5. Click "Process Files"

### Linux/Mac
1. Open terminal in this folder
2. Run: `./gui_wrapper.sh`
3. Drag PDF files into the window
4. Choose output options (Excel/CSV)
5. Click "Process Files"

**That's it!** Your processed schedules will be saved to the `output` folder.

---

## Features

✨ **Drag-and-Drop Interface** - Just drag PDF files into the window
📁 **Batch Processing** - Process multiple PDFs at once
📊 **Flexible Output** - Choose Excel, CSV, or both
⚡ **Real-Time Feedback** - Watch processing progress live
📝 **Detailed Logging** - See exactly what's happening
🎯 **Easy Access** - Quick buttons to open output folder

---

## Interface Guide

### 1. Drag-and-Drop Zone (Top)
- **Drag PDFs here** or **click to browse**
- Accepts multiple files at once
- Only accepts .pdf files

### 2. File Queue List
- Shows all queued PDF files
- **Remove Selected** - Remove one file
- **Clear All** - Empty the queue
- Double-click a file to remove it

### 3. Output Options

**Output Formats:**
- ☑ **Excel (.xlsx)** - Default, creates Excel spreadsheet
- ☐ **CSV (.csv)** - Optional, creates CSV file
- You can enable both to get both formats

**Output Folder:**
- Default: `./output/` (in the current folder)
- Click **Browse...** to choose a different location
- Folder is created automatically if it doesn't exist

**Verbose Logging:**
- ☐ Normal - Shows main steps only
- ☑ Verbose - Shows detailed debug information

### 4. Process Button
- Click **▶ Process Files** to start
- Changes to **⏹ Cancel** while processing
- Disabled when no files are queued

### 5. Progress Bar
- Shows overall progress
- Displays "X/Y files processed"

### 6. Status Log
- Real-time processing messages
- Color-coded:
  - **Black** - Information
  - **Orange** - Warnings
  - **Red** - Errors
- Auto-scrolls to latest messages

### 7. Action Buttons

- **📂 Open Output Folder** - Opens file explorer to output folder
- **Clear Status** - Clears the status log
- **View Log File** - Opens the detailed log file in text editor

---

## Example Workflow

1. **Launch the GUI**
   ```
   Double-click: gui_wrapper.bat (Windows)
   OR run: ./gui_wrapper.sh (Linux/Mac)
   ```

2. **Add Files**
   - Drag `DailySetupReport__19_.pdf` into the drop zone
   - Or click the drop zone and browse to your PDF

3. **Configure Output**
   - Keep Excel ☑ (default)
   - Optional: Enable CSV ☑
   - Optional: Click Browse to change output folder

4. **Process**
   - Click "▶ Process Files"
   - Watch the progress bar and status log
   - Wait for "Processing Complete" message

5. **View Results**
   - Click "📂 Open Output Folder"
   - Find `DailySetupReport__19__schedule.xlsx`
   - Open in Excel and review your schedule

---

## Troubleshooting

### GUI Won't Launch

**Problem**: Double-clicking the script does nothing or shows an error.

**Solutions**:
- Ensure Python 3.10+ is installed: `python --version`
- On Windows: Make sure Python is in your PATH
- On Linux/Mac: Try `python3 gui_wrapper.py` directly

### Drag-and-Drop Doesn't Work

**Problem**: Files don't get added when dragged.

**Solution**:
- Click the drop zone instead to browse for files
- This is normal if tkinterdnd2 didn't install
- Functionality is identical, just uses file dialog instead

### No Events Found

**Problem**: Processing succeeds but output is empty.

**Possible Causes**:
- PDF has different format than expected
- All events are filtered out by location rules
- PDF is corrupted or not a Daily Setup Report

**Solutions**:
1. Enable "Verbose Logging" and process again
2. Check the status log for details
3. Click "View Log File" for full details
4. Verify the PDF opens correctly in a PDF reader

### Processing Fails

**Problem**: "Error processing [filename]" appears.

**Solutions**:
1. Check the status log for specific error message
2. Verify the PDF file isn't corrupted
3. Try processing one file at a time
4. Enable Verbose Logging for more details
5. View the log file for stack traces

### Output Folder Not Found

**Problem**: "Folder does not exist yet" when clicking "Open Output Folder".

**Solution**:
- Process at least one file first
- The folder is created automatically on first processing

---

## Command-Line Alternative

If you prefer the command-line interface or need automation, you can still use:

```bash
python setup_report_processor.py your_report.pdf
```

See [README.md](README.md) for full CLI documentation.

---

## Customizing Location Filters

To modify which locations are included/excluded in the output:

1. Open [`setup_report_processor.py`](setup_report_processor.py#L38-L52) in a text editor
2. Edit these sections:
   ```python
   VALID_LOCATION_PREFIXES = [
       "UC ",
       "RUC ",
       "FCS Michigan",
       "FCS 180",
       "FCS Dining Rm D"
   ]

   EXCLUDED_LOCATIONS = [
       "UC Table-Bake/Day Sale",
       "UC Table-Info",
       ...
   ]
   ```
3. Save the file
4. Restart the GUI

Changes apply to both GUI and CLI versions.

---

## Batch Processing Tips

### Processing Multiple Files at Once

1. Select all your PDFs in file explorer
2. Drag them all into the GUI drop zone
3. They'll all be queued
4. Click "Process Files" once
5. All files will be processed sequentially

### Organizing Output Files

**Option 1: Separate folders per batch**
- Create a folder: `output_january/`
- Browse to it before processing
- Process all January reports
- Repeat for February, etc.

**Option 2: Date-stamped folders**
- Create folder: `output_2026-01-07/`
- Process that day's reports
- Easy to find later by date

### Regular Processing Workflow

For daily/weekly processing:

1. Create a shortcut to `gui_wrapper.bat` on your desktop
2. Double-click to launch
3. Drag new PDFs
4. Process
5. Done!

Total time: ~30 seconds per batch

---

## Technical Details

### Requirements
- Python 3.10 or higher
- Windows, macOS, or Linux
- ~50MB disk space for dependencies

### Dependencies
- All dependencies from CLI version (pdfplumber, pandas, openpyxl)
- Optional: tkinterdnd2 for enhanced drag-and-drop

### Files Created
- `output/` - Default output folder for schedules
- `setup_report_processor.log` - Detailed processing log
- `.setup_report_processor_gui.json` - Saved preferences (in home folder)

### What Gets Processed
From each PDF, the tool extracts:
- Event names
- Locations (filtered by UC/RUC/FCS prefixes)
- Setup Ready By times
- Closing times (event end)

Then creates:
- 2 rows per event (Setup Ready By + Closing)
- Chronologically sorted schedule
- Excel and/or CSV output

---

## Keyboard Shortcuts

- **Double-click file** in list → Remove from queue
- **Click drop zone** → Browse for files
- **Close window** → Exit application

---

## Performance

**Processing Speed** (approximate):
- Small PDFs (1-10 pages): < 1 second
- Medium PDFs (10-50 pages): 1-5 seconds
- Large PDFs (50+ pages): 5-15 seconds

**Batch Processing**:
- 10 PDFs: ~10-20 seconds total
- 50 PDFs: ~1-2 minutes total

Times may vary based on your computer's performance.

---

## Comparison: GUI vs CLI

| Feature | GUI | CLI |
|---------|-----|-----|
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Drag-and-drop | ✅ Yes | ❌ No |
| Visual feedback | ✅ Real-time | ⚠️ Text only |
| Batch processing | ✅ Easy | ✅ Script needed |
| Automation | ❌ Manual | ✅ Scriptable |
| Speed | Same | Same |
| Output quality | Same | Same |

**Use GUI when**: You want ease of use and visual feedback
**Use CLI when**: You need automation or scripting

---

## Support

### Getting Help

1. **Check the status log** in the GUI for error messages
2. **View the log file** by clicking "View Log File" button
3. **Run with verbose logging** enabled for detailed info
4. **Check [README.md](README.md)** for general documentation

### Reporting Issues

If you encounter a bug:

1. Enable "Verbose Logging"
2. Reproduce the issue
3. Click "View Log File"
4. Save the relevant error messages
5. Report the issue with the log excerpt

---

## FAQ

**Q: Can I process multiple PDFs at once?**
A: Yes! Drag multiple PDFs into the drop zone, or Ctrl+Click multiple files when browsing.

**Q: Where are the output files saved?**
A: By default in the `output/` folder. Click "Browse..." to change the location.

**Q: Can I choose both Excel and CSV?**
A: Yes! Check both boxes to get both formats for each PDF.

**Q: Does this replace the command-line version?**
A: No, both work equally well. Use whichever you prefer.

**Q: Can I customize which locations are included?**
A: Yes, edit the location filters in [setup_report_processor.py](setup_report_processor.py#L38-L52).

**Q: Is my data safe?**
A: Yes, all processing happens locally on your computer. No data is sent anywhere.

**Q: Can I cancel processing?**
A: Yes, click the "⏹ Cancel" button that appears while processing.

---

## Version History

### v1.1.0 (Current)
- Initial GUI release
- Drag-and-drop interface
- Batch processing
- Real-time progress tracking
- Integrated logging display

---

**Happy Scheduling! 📅**

*For command-line usage, see [README.md](README.md)*
