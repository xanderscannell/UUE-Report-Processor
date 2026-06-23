# Project Status

**Last updated**: 2026-06-23

## Current Position

**Phase**: GUI Modernization
**Subphase**: tkinter → PySide6 migration + MATLAB Gantt replacement (ADR-004)
**Progress**: GUI rewritten in PySide6; embedded pyqtgraph Gantt replaces MATLAB;
all 49 tests pass; headless smoke test passes. Pending: on-display verification + exe rebuild.

## Recently Completed (2026-06-23 — PySide6 migration)

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

- [ ] Verify the PySide6 app on a real (scaled) display — confirm crispness and Gantt visuals
- [ ] Rebuild the portable exe with the new Qt/pyqtgraph deps
- [ ] Update README + GUI docs for the PySide6 UI and embedded Gantt
- [x] Remove obsolete MATLAB artifacts (`GanttChartApp.mlapp`/`.txt`) and code references

## Next Up

1. Run `python gui_wrapper.py`, process a real PDF, open "View Gantt", check DPI crispness
2. Rebuild exe (Qt needs no special flags; PyInstaller ships PySide6/pyqtgraph hooks):
   `pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py`
   — confirm `UUE.ico` lands next to the exe (used for the window icon at runtime)
3. Copy `location_config.json` into `dist/SetupReportProcessor/`
4. Smoke-test the exe (window + Gantt), then zip for distribution
5. Update README/documentation for the new UI

## Active Files and Modules

```
setup_report_processor.py    [status: stable, MATLAB code removed, create_gantt_rows]
gui_wrapper.py               [status: rewritten in PySide6 (MainWindow)]
gui_components/              [status: rewritten in PySide6; +worker.py, +gantt_window.py]
location_config.json         [status: stable, v2 format]
test_setup_report_processor.py [status: stable, 49/49 passing]
requirements.txt             [status: updated, +PySide6 +pyqtgraph]
UUE.ico                      [status: app icon — must ship beside exe for window icon]
build_release.bat            [status: new — builds + zips the portable release]
```

## Recent Decisions

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
