# Changelog

All notable changes to the UUE Report Processor are recorded here.

Versions follow [semantic versioning](https://semver.org/): the major number
moves when the interface or the deliverable changes shape, the minor when
features are added compatibly.

## [4.2.0] - 2026-08-22: Read event data straight from the database export

- **New second event source.** The app now reads the events database's **Daily Events Excel export** (`.xlsx`) as well as Daily Setup Report PDFs. No more depending on PDF layout for the daily run
- The file type is detected from its extension — there is no mode to switch. Drop a PDF, an export, or a mix of both into the same batch and each is read the right way
- Everything after that is unchanged: the same location whitelist, the same Setup Ready By / Closing rows, the same sorting, the same Excel/CSV output, and the same timeline
- The CLI's file argument is now `report_file` and takes either type: `python setup_report_processor.py DailyEventsExcel.xlsx`
- Output files are still named from the report's own date, read from the export's Parameter Summary sheet (falling back to the sheet title, then its Day column)
- A multi-day export is read whole — every `Event List` sheet, not just the first
- If the report definition changes and a needed column disappears, the file fails with a message naming the missing column instead of failing obscurely
- **Note**: the export has no setup-start column, so for Excel sources **Setup Ready By is the event's own start time**. Schedules built from an export carry no setup lead time
- **Note**: the export covers all campus locations, so it contains many rooms the PDF never did (Fieldhouse, parking lots). They are filtered out until enabled in **Settings → Location Whitelist…**
- Test suite grew from 56 to 87 tests

## [4.1.0] - 2026-08-04: Keep awake + persistent preferences

- New **Settings → Keep computer awake** toggle — stops the computer sleeping and the display turning off while the window is open, for leaving the event timeline up on a screen. Windows only; released automatically when the app closes
- Interface preferences now survive a restart, saved in `gui_preferences.json` beside the app: the output folder, the Excel/CSV choice, and all three Settings toggles (open timeline when finished, keep computer awake, verbose logging)
- Preferences are written the moment they change, so a crash never costs a setting. Delete `gui_preferences.json` to return everything to its defaults
- A saved output folder that is no longer reachable (an unplugged drive, a different machine) falls back to the default instead of failing at the end of a run
- Test suite grew from 49 to 56 tests

## [4.0.0] - 2026-08-04: Frontend overhaul

- Staged window — an inviting drop target when empty, a file queue with live per-file status while working, and a results summary when a run finishes
- Custom UM-Dearborn light/dark theme; the maize accent is reserved for the primary action
- Results screen (files processed, events found, issues, where output went) replaces the post-run alert box
- Processing log moved behind a **Details** disclosure that badges warning/error counts and opens itself when a run produces either
- One-time setup moved into a **Settings** menu in the header
- New **Building Colors** setting — timeline colors per building, auto-discovered from room-name prefixes; give two prefixes the same color to mark them as one building (`UC`/`RUC`)
- Timeline: colored by building with a legend, hover tooltips, auto-widening time axis, and fixed clipped location labels
- Location editor gained real checkboxes and a filter box
- Files can be dropped anywhere in the window
- The timeline is no longer a selectable output — it is always available after a run. Unticking both Excel and CSV is a timeline-only run that writes nothing to disk
- Fixed: progress did not advance for skipped or failed files

## [3.0.0] - 2026-06-23: PySide6 rewrite + embedded Gantt chart

- Migrated the GUI from tkinter to PySide6 — crisp high-DPI rendering, native drag-and-drop, and automatic light/dark theme support
- Replaced the external MATLAB Gantt app with a built-in pyqtgraph chart (live current-time marker), opened via **View Gantt** or auto-launched on completion
- Added the **Auto-launch Gantt Chart** output option; at least one output (Excel/CSV/Gantt) is now required to process
- Removed the MATLAB CSV output and the `--matlab-*` CLI flags
- Added `build_release.bat` for one-step portable-release builds

## [2.0.0] - 2026-02-11: GUI release

- Desktop GUI with drag-and-drop file processing
- Location whitelist editor (add/remove/toggle locations)
- Portable `.exe` distribution via PyInstaller
- Desktop shortcut creation with custom icon
- Location config v2 format (replaces separate whitelist/blacklist)
- 49 passing tests

## [1.0.0] - 2026-01-07: Initial production release

- PDF text extraction
- Location-based filtering
- Chronological sorting
- Excel/CSV export
- Comprehensive logging

[4.1.0]: https://github.com/xanderscannell/UUE-Report-Processor/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/xanderscannell/UUE-Report-Processor/compare/v3.0.0...v4.0.0
[3.0.0]: https://github.com/xanderscannell/UUE-Report-Processor/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/xanderscannell/UUE-Report-Processor/compare/1d960f9...v2.0.0
[1.0.0]: https://github.com/xanderscannell/UUE-Report-Processor/commit/1d960f9
