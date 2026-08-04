# Setup Report Processor - GUI Edition

A drag-and-drop desktop interface (PySide6) for processing Daily Setup Report PDFs.

## Quick Start

### Portable app (Windows, recommended)

1. Extract `SetupReportProcessor.zip`
2. Double-click `SetupReportProcessor.exe`
3. Drop PDF files anywhere in the window
4. Pick **Excel** and/or **CSV** — or neither, for a timeline-only run
5. Click **Process N files**

### From source

- **Windows:** double-click [`gui_wrapper.bat`](../gui_wrapper.bat) (sets up a venv and installs dependencies on first run)
- **Linux/Mac:** run [`./gui_wrapper.sh`](../gui_wrapper.sh)
- **Any platform:** `python gui_wrapper.py` (after `pip install -r requirements.txt`)

Processed schedules are saved to the `output` folder by default.

---

## Features

- **Drag-and-drop** — drop PDFs anywhere in the window (native, no extra setup)
- **Batch processing** — queue multiple PDFs; each shows live status as it runs
- **Flexible output** — Excel, CSV, both, or neither
- **Event timeline** — the day's schedule as a Gantt chart, colored by building
- **Results summary** — files processed, events found, issues, and where output went
- **High-DPI crisp rendering** — sharp on scaled displays, with a light and dark theme
- **Configurable** — location whitelist and building colors, both editable in-app

---

## The window, step by step

The window changes with what you're doing — you only ever see what's relevant now.

### 1. Empty — nothing queued yet

A large drop target plus a three-step summary of what the app does. Drop PDFs on
it, or click anywhere in the box to browse.

### 2. Workspace — files queued

- **Add more PDFs** — a slim drop strip at the top; you can also drop anywhere in the window
- **Queue** — one card per file, showing its name and folder. Each has its own **✕**
  to remove it; **Clear all** empties the queue. While processing, each card shows a
  status dot (queued → spinner → check / cross) and its result, e.g. "31 events"
- **Output** — **Excel .xlsx** and **CSV .csv** toggles, plus the destination folder
  (click it to change)
- **Process N files** — the single primary action. While running it becomes a
  progress bar with an X/Y counter and **Cancel**

### 3. Results — the run finished

- Outcome headline and icon (all done / finished with issues / nothing produced / stopped)
- Three metrics: **files done**, **events found**, **issues**
- Where the output went
- **View Timeline** and **Open Output Folder**, plus **← Process more files**

### Details (always available)

At the bottom of every screen. Collapsed by default; expand it for the full
processing log, color-coded by level. If a run produces warnings or errors, a badge
appears on the header and the section opens itself.

### Settings menu (header, top right)

- **Location Whitelist…** — which venues are included
- **Building Colors…** — timeline color per building
- **Output Folder…** — where schedules are written
- **Open timeline when finished** — open the chart automatically after each run
- **Keep computer awake** — stop the computer sleeping and the display turning
  off while this window is open, for leaving the timeline up on a screen. It
  turns itself off when you close the app, and it is Windows-only
- **Verbose logging** — detailed debug output in the log

These preferences, the output folder, and the Excel/CSV choice are remembered
between launches in `gui_preferences.json`, saved next to the app. Delete that
file to return everything to its defaults.
- **Open log file** / **Add desktop shortcut**
- **About**

---

## Timeline-only runs

If you just want to look at the day, **untick both Excel and CSV**. The button
changes to **Preview N files**, and the run writes nothing at all — not even an
output folder. You still get the results summary and **View Timeline**.

Useful for checking a report before committing to a spreadsheet.

---

## Event Timeline

Open it with **View Timeline** on the results screen, or turn on
**Settings → Open timeline when finished**.

- One horizontal bar per event, from setup time to closing time
- Bars are colored by building, with a legend; each is also labeled by location
- Time-of-day axis covering 6 AM to midnight, widened automatically if events
  fall outside it
- A dashed line marks the current time and refreshes every minute
- Hover a bar for the event name, location, and exact times
- The view is fixed (no accidental panning or zooming)
- Process several PDFs at once to get a **Report** selector for switching between days

---

## Location Whitelist

**Settings → Location Whitelist…** controls which venues appear in the output:

- **Check / uncheck** to include or exclude a location without deleting it
- **Filter** box to search a long list
- **Add location** / **Remove selected** to change the list itself

Unchecked locations are filtered out during processing. Click **Save changes** to
write them to `location_config.json`; they apply to files processed from then on.

---

## Building Colors

**Settings → Building Colors…** sets the timeline color for each building.

Buildings are identified by the prefix in the room name — `UC 1225` is `UC`,
`FCS 180` is `FCS`. The list fills itself in: any prefix appearing in your
whitelist or in a processed report is added automatically with a color assigned,
so a new campus building needs no update to the app. You can also give a building
a friendlier name than its prefix; that name appears in the timeline legend.

**Two prefixes for the same building? Give them the same color.** `UC` and `RUC`
both mean the Renick University Center — the building was renamed but existing
rooms kept their old names — so they ship sharing a color and appear as one legend
entry.

Colors come from a fixed set chosen to stay distinguishable, including for
colorblind viewers, on both light and dark backgrounds. Options past the first
three are marked `*`: with four or more buildings on screen at once some pairs get
hard to tell apart, and the per-bar location labels are what keep them straight.

---

## Troubleshooting

**GUI won't launch**
- Ensure Python 3.9+ is installed and on your PATH (`python --version`)
- From source, try `python gui_wrapper.py` directly to see the error

**No events found**
- Expand **Details** to see why events were skipped
- A location may be unchecked in the whitelist, or the PDF format may differ
- Turn on **Settings → Verbose logging** and process again for more detail

**Processing fails for a file**
- The file's card shows the reason; **Details** has the full error
- Verify the PDF isn't corrupted and opens in a PDF reader

**A building's bars are gray on the timeline**
- Its room-name prefix has no color yet — open **Settings → Building Colors…**,
  where it will already be listed, and pick one

**Output folder not found**
- Process at least one file with Excel or CSV ticked; the folder is created then.
  A timeline-only run deliberately creates nothing

---

## Files Created

- `output/` — default output folder for schedules
- `location_config.json` — location whitelist and building colors
- `setup_report_processor.log` — detailed processing log

All processing happens locally on your computer; no data is sent anywhere.

---

## FAQ

**Can I process multiple PDFs at once?**
Yes — drop several in, or Ctrl+Click multiple files when browsing.

**Can I get both Excel and CSV?**
Yes — turn on both. Turning off both gives you a timeline-only run.

**Do I have to create a spreadsheet just to see the timeline?**
No. Untick both formats and click **Preview N files**.

**Where are outputs saved?**
In `output/` by default; click the folder name in the Output panel to change it.

**Can I customize which locations are included?**
Yes — **Settings → Location Whitelist…**, no code editing needed.

**Can I cancel processing?**
Yes — **Cancel** appears beside the progress bar while a run is going. It stops
after the file currently being read.

---

## Dependencies

- pdfplumber, pandas, openpyxl (core processing)
- PySide6 (Qt desktop interface)
- pyqtgraph (timeline chart rendering)

---

For command-line usage, see [README.md](../README.md).
