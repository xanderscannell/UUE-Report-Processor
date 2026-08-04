# Project Status

**Last updated**: 2026-08-04

## Current Position

**Phase**: GUI Modernization
**Subphase**: Frontend overhaul — staged UI + custom design system (ADR-005, ADR-006)
**Progress**: Window restructured into empty → workspace → results stages with a
UM-Dearborn themed design system. All 49 tests pass; end-to-end GUI smoke test
passes (worker thread → per-file status → results screen); every screen reviewed
rendered in both light and dark. Docs are current. Pending: on-display
verification with a real PDF, and an exe rebuild.

See [CHECKPOINTS/2026-08-05-frontend-overhaul.md](CHECKPOINTS/2026-08-05-frontend-overhaul.md)
for the full session record, including the bugs found and how they were resolved.

## Recently Completed (2026-08-04 — changelog extracted)

- **`CHANGELOG.md` is now the release history**. The README's Version History
  section was migrated out verbatim and replaced with a link; the README keeps
  only a pointer and the current version number.
- Keep-awake and persistent preferences are recorded there as **v4.1.0**.
  Not yet tagged — `git tag v4.1.0` is still pending, and the changelog's
  `[4.1.0]` compare link resolves once it exists.
- v4.0.0 is dated 2026-08-04 in the changelog, matching its commit and tag; the
  README had it as 2026-08-05, which would have put v4.1.0 before it.

## Earlier Completed (2026-08-04 — persistent preferences)

- **Preferences now persist** (ADR-007): new `gui_components/preferences.py`
  writes `gui_preferences.json` beside the exe. Remembers the output folder,
  the Excel/CSV choice, and all three Settings toggles (open timeline when
  finished, keep computer awake, verbose logging).
- Saved on change rather than on exit, so a crash never costs a setting.
  `MainWindow._remember()` is the single write path; it no-ops when the value
  did not actually change.
- Defaults are not restated — `Preferences.defaults()` reads `GUI_DEFAULTS`.
- Degrades safely: missing/corrupt file → defaults + a logged warning; an
  `output_dir` whose parent is gone (unplugged drive, other machine) reverts to
  the default; an unwritable location returns False instead of raising.
- Only what the OS granted is remembered — a refused keep-awake persists as off.
- **Deliverable is unchanged**: the file is created on demand, so
  `build_release.bat` needs no edit. It is gitignored.
- **Verified**: 56/56 tests pass (7 new `TestPreferences` cases, no Qt needed);
  an offscreen two-window test confirms every preference survives a restart and
  that merely restoring state does not rewrite the file.

## Earlier Completed (2026-08-04 — keep-awake setting)

- **Keep computer awake**: new `gui_components/keep_awake.py` (`KeepAwake`) plus a
  checkable **Settings → Keep computer awake** item. Holds
  `ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED` via
  `SetThreadExecutionState` so the machine and the display stay on while the
  window is open — meant for leaving the timeline up on a screen.
- Released in a new `MainWindow.closeEvent`, so the machine can never be left
  unable to sleep after the app is gone.
- Off by default (`GUI_DEFAULTS["keep_awake"]`); in-memory only, like the other
  two preference toggles — it does not persist across launches.
- Windows-only: elsewhere the menu item is disabled with an explanatory tooltip
  rather than silently doing nothing. If the OS refuses the call, the menu item
  re-syncs to the real state and the user is told.
- **Verified**: read the flags back from the OS (0x80000003 while on, cleared on
  release and on window close); menu toggle drives it end to end; 49/49 tests pass.

## Earlier Completed (2026-08-05 — frontend overhaul)

- **Design system**: new `gui_components/style.py` — color tokens (light + dark),
  spacing/type scale, `build_stylesheet()`, `apply_theme()` (Fusion + app-owned
  palette). Michigan Blue brand surfaces, Maize reserved for the primary action.
- **Staged window**: `gui_wrapper.py` is a 3-stage `QStackedWidget` —
  hero drop target → file queue + output toggles + one CTA → results summary.
- **Shared primitives**: new `gui_components/widgets.py` (`Card`, `HeaderBar`,
  `CollapsibleSection`, `DropIcon`/`OutcomeIcon`/`StatusGlyph`/`FileGlyph`,
  `label()`/`pill()` helpers).
- **Results screen**: new `gui_components/result_panel.py` replaces the post-run
  `QMessageBox` — outcome icon, files/events/issues metrics, output location,
  and View Timeline / Open Output Folder / Process more.
- **File queue rewrite**: per-file cards with their own remove button and live
  status (queued / spinner / done / failed / skipped) plus a result detail.
- **Log demoted**: behind a persistent "Details" disclosure that badges
  warning/error counts and auto-expands when a run produces either.
- **Settings menu**: location whitelist, output folder, preferences, log file,
  and desktop shortcut moved out of the main surface into the header menu.
- **Location editor**: real checkboxes (with a generated tick glyph), a filter
  box, grayed-out disabled entries, and an enabled/total counter.
- **Timeline rewrite**: bars colored by building with a legend, fixed the clipped
  Y-axis location labels, auto-widening time axis, hover tooltips, "now" marker.
- **Building Colors setting** (ADR-006): new `building_config.py` +
  `building_editor.py`. Buildings are discovered from room-name prefixes in the
  enabled whitelist and processed reports, auto-assigned a validated palette slot,
  and persisted in `location_config.json` under an additive `buildings` key.
  Giving two prefixes the same color is how "UC and RUC are one building" is
  expressed — the legend merges same-colored entries. New campus buildings
  (CASL, ELB, …) now need no code change.
- **Worker signals**: `file_started` / `file_done` / `finished_all(cancelled, summary)`;
  progress now advances for skipped and failed files too (previously it did not).
- **Timeline-only runs**: unticking both Excel and CSV is a valid mode rather than
  a validation error — the CTA becomes "Preview N files" and the run writes
  nothing, not even the output folder. Verified end to end.
- **Processor**: `create_gantt_rows()` also emits `EventName` (tooltip source).
- **Verified**: 49/49 tests pass; GUI smoke test drives a real run to the results
  screen; light and dark renders reviewed for every stage.

## Earlier Completed (2026-06-23 — PySide6 migration)

- **GUI rewritten in PySide6**: `gui_wrapper.py` is now a `QMainWindow`; all
  `gui_components/` widgets reimplemented in Qt (drop_zone, file_list, location_editor,
  log_handler). Fixes high-DPI blurriness from tkinter.
- **Embedded Gantt chart**: new `gui_components/gantt_window.py` (pyqtgraph) replaces
  the external MATLAB `GanttChartApp`. Opens in a separate window via a "View Gantt"
  button; live red current-time line on a 60s `QTimer`; handles midnight-crossing bars;
  report selector when multiple PDFs are processed.
- **Background worker**: `gui_components/worker.py` — `ProcessorWorker(QThread)` with
  Qt signals (status/progress/gantt_ready/finished_all), replacing the Thread+queue model.
- **MATLAB code removed from processor**: deleted `save_to_matlab_csv()` and
  `_launch_matlab_app()`; removed `--matlab-*` CLI flags; renamed
  `create_matlab_event_rows()` → `create_gantt_rows()` (now the chart's data source).
- **Dependencies**: added `PySide6` + `pyqtgraph` to `requirements.txt`; dropped reliance
  on `tkinterdnd2` (Qt has native drag-and-drop).
- **Verified**: all 49 existing tests pass; offscreen GUI/Gantt smoke test passes.

## Earlier Completed

- **Location config v2 format**: Migrated from separate whitelist/blacklist arrays to single object array with `enabled` flags (`location_config.json`)
- **Removed blacklist concept**: Disabled whitelist items replace the old blacklist; simplified `_match_whitelist_location()` in processor
- **Location Editor GUI**: New `gui_components/location_editor.py` — modal dialog for add/remove/toggle locations, saves v2 JSON
- **Desktop shortcut button**: PowerShell-based `.lnk` creation with OneDrive Desktop path detection
- **Custom app icon**: `UUE.ico` — embedded in exe via PyInstaller `--icon`, used for window titlebar and desktop shortcut
- **Frozen exe support**: `BASE_DIR` using `sys.frozen` detection in both `setup_report_processor.py` and `gui_wrapper.py`
- **PyInstaller `--onedir` build**: Switched from `--onefile` (slow startup) to `--onedir` (instant startup)
- **Fixed all 49 tests**: Including 2 pre-existing setup time extraction test failures (leading whitespace vs `^` anchor)
- **GUI layout fixes**: Action buttons visible and properly ordered above Process Files button
- **v1 backward compatibility**: Processor can still load legacy v1 config files

## In Progress

- [ ] Verify the overhauled UI on a real (scaled) display with a real Daily Setup Report PDF
- [ ] Rebuild the portable exe with the new Qt/pyqtgraph deps
- [x] Refresh `documentation/README_GUI.md` and `QUICKSTART.md` for the staged UI
- [x] Update the top-level README for the staged UI, Settings menu, and timeline
- [x] Rewrite `.context/SETUP.md` (stale `requirements-gui.txt`, tkinterdnd2, `input/`)
- [x] Remove obsolete MATLAB artifacts (`GanttChartApp.mlapp`/`.txt`) and code references

## Next Up

1. Run `python gui_wrapper.py`, process a real PDF end to end, open **View Timeline**,
   and confirm crispness on a scaled display in both light and dark mode
2. Rebuild exe (Qt needs no special flags; PyInstaller ships PySide6/pyqtgraph hooks):
   `pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py`
   — confirm `UUE.ico` lands next to the exe (used for the window icon at runtime)
3. Copy `location_config.json` into `dist/SetupReportProcessor/`
4. Smoke-test the exe (window + timeline), then zip for distribution
5. Consider tests for GUI-side logic that now carries real behavior —
   `BuildingColors` assignment/persistence and dry-run gating are currently only
   covered by ad-hoc scripts, not the suite

## Active Files and Modules

```
setup_report_processor.py    [status: stable; create_gantt_rows now emits EventName]
gui_wrapper.py               [status: rewritten — 3-stage MainWindow + Settings menu]
gui_components/              [status: rewritten; +style.py, +widgets.py, +result_panel.py, +keep_awake.py, +preferences.py]
location_config.json         [status: stable, v2 format]
test_setup_report_processor.py [status: stable, 56/56 passing]
requirements.txt             [status: updated, +PySide6 +pyqtgraph]
UUE.ico                      [status: app icon — must ship beside exe for window icon]
build_release.bat            [status: new — builds + zips the portable release]
```

## Recent Decisions

- **2026-08-05**: Staged single-page GUI + app-owned light/dark theme (ADR-005)
- **2026-08-05**: Gantt bars colored by building, discovered from room-name
  prefixes and configured by the user, not hardcoded (ADR-006)
- **2026-08-05**: `location_config.json` gained an additive `buildings` key;
  still version 2, and the processor ignores it
- **2026-08-05**: Timeline is no longer a selectable "output" — it is always
  available after a run, so Process requires Excel or CSV
- **2026-02-11**: Switched to `--onedir` PyInstaller build to avoid slow `--onefile` startup extraction
- **2026-02-11**: Desktop shortcut uses exe's embedded icon (`$s.IconLocation = "$target,0"`) instead of requiring separate .ico in deliverable
- **2026-02-11**: Window icon uses `self.root.iconbitmap(sys.executable)` when frozen to read embedded icon
- **2026-02-11**: Location config v2 format — `[{"name": "...", "enabled": true/false}]` replaces separate whitelist/blacklist
- **2026-02-11**: OneDrive Desktop path resolved via `[Environment]::GetFolderPath('Desktop')` PowerShell call

## Build Instructions

```bash
# From project root with venv activated:
pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py
cp location_config.json dist/SetupReportProcessor/
# Zip dist/SetupReportProcessor/ for distribution
```

## Notes for Claude

- The PDF format has times appearing TWICE per line: `11:30 AM Setup Starts: 11:00 AM Event Name...`
- pdfplumber text extraction can produce unexpected layouts; always test regex changes against real PDFs
- `_match_whitelist_location()` uses longest-first `startswith` matching (no more blacklist check)
- Deliverable = `SetupReportProcessor.exe` + `location_config.json` + `_internal/` folder, all inside one zipped folder
- `BASE_DIR` = `Path(sys.executable).parent` when frozen, `Path(__file__).parent` otherwise
- GUI colors come from `gui_components/style.py` — never hard-code a hex in a
  widget, and never call `is_dark_mode()` from a widget (use `style.tokens()`)
- To review the UI without a real PDF: build a `MainWindow`, call
  `_on_files_added([Path(...)])` with any paths (they need not exist), drive
  `_show_running()` / `result_panel.set_results()`, and `widget.grab().save(...)`
