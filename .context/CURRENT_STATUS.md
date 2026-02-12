# Project Status

**Last updated**: 2026-02-11

## Current Position

**Phase**: Release Preparation
**Subphase**: First portable release
**Progress**: Core features 100%, GUI complete, portable exe builds working

## Recently Completed

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

- [ ] Update README for first release
- [ ] Final exe rebuild with all latest changes

## Next Up

1. Rebuild exe with `pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py`
2. Copy `location_config.json` into `dist/SetupReportProcessor/`
3. Zip `SetupReportProcessor/` folder for distribution
4. Update README with usage instructions and release notes

## Active Files and Modules

```
setup_report_processor.py    [status: stable, v2 config, no blacklist]
gui_wrapper.py               [status: stable, icon support, desktop shortcut, layout fixed]
gui_components/              [status: stable, includes LocationEditor]
location_config.json         [status: stable, v2 format]
test_setup_report_processor.py [status: stable, 49/49 passing]
UUE.ico                      [status: new, app icon]
.gitignore                   [status: updated, *.spec excluded]
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
