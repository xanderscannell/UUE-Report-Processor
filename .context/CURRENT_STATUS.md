# Project Status

**Last updated**: 2026-08-22

## Current Position

**Phase**: Multi-day timeline (ADR-011), on the legibility work of ADR-009/010
**Subphase**: Built and verified against the real weekend exports; awaiting an on-display check
**Progress**: The app now reads the events database's `Daily Events - Excel`
export alongside Daily Setup Report PDFs, dispatched by file extension. 87/87
tests pass, including all 56 pre-existing ones **unedited**. Docs and ADR-008
are current. Pending: a real-export soak beyond the single sample, an
on-display GUI check, and the exe rebuild that was already outstanding.

## Recently Completed (2026-08-22 — hover card survives a resting pointer)

- **The hover card was still vanishing after about a second**, but only with a
  real pointer, which is why every synthetic test passed. Roughly 700ms after
  the mouse comes to rest Qt runs its own help pass: it sends `QEvent.ToolTip`
  to the widget underneath, `QGraphicsView` forwards that to the scene as a
  help event, the scene finds no item carrying a `toolTip()`, and calls
  `QToolTip.showText(pos, "")` — which clears whatever is on screen, including
  a card Qt did not put there.
- **Fix**: consume `QEvent.ToolTip` in the plot viewport's event filter. We own
  the tooltip for that widget, so the automatic pass has nothing to add.
- **Lesson for the harness**: `sigMouseMoved` driven synthetically never starts
  Qt's tooltip wake-up timer, so no amount of synthetic hovering could reproduce
  this. Diagnosing it took parking the *real* pointer with `QCursor.setPos`
  (restoring it afterwards). The regression check now sends the `QEvent.ToolTip`
  directly and allows 0.8s for the 300ms hide timer — verified to fail without
  the fix and pass with it. Hover checks 8 → 9.

## Earlier Completed (2026-08-22 — multi-day timeline)

- **A weekend now reads as one chart** (ADR-011). The database exports one day
  per file, so several files stack into one timeline, oldest on top, separated
  by a rule, sharing one time-of-day axis.
- **Events carry their own date.** `create_gantt_rows` emits a `Date` key; the
  Excel reader resolves it per row from the `Event Start` cell (a full datetime
  in real exports), falling back to the `Day` column then the sheet title. The
  PDF path falls back to the processor single `report_date`.
- **Datasets are keyed by date, not by file.** `_on_gantt_ready` splits rows
  with `group_rows_by_day`, so one export holding two sheets lands as two
  blocks exactly like two files — and the order files are dropped in does not
  matter. A repeated date replaces (right for a re-pull) but now logs a warning.
- **The selector became a Day filter** with an "All days" entry, default when
  more than one day is loaded. Only an *explicit* choice survives new data
  (`_chosen_day`, set from a signal that repopulation blocks) — otherwise a
  second file arriving mid-run leaves you pinned to day one.
- **The clock crosses only its own day** (`_place_clock`). This also fixed the
  past-midnight case: between midnight and the start of the axis the marker
  rides *yesterday* block on the extension past 24:00 — the schedule actually
  running — rather than the small hours of today, which the axis never shows.
- **Verified against the two real exports** (`DailyEventsExcel.xlsx` = Sat Aug
  22, `(2).xlsx` = Sun Aug 23): 27 checks covering block bounds, ordering,
  filtering, live arrival of a second day, and five clock placements around
  midnight via a patched clock. Unit tests 87 → 98.
- **Known gaps**: the X axis is the union across days, so one overnight event
  extends the axis for every day; the results screen still counts files, not
  days; two sources covering the same date replace rather than merge.

## Earlier Completed (2026-08-22 — date on the Y axis)

- **The Y axis names the day, not the room** (ADR-010). ADR-009 put the room on
  the bar, which made the per-event axis labels a second copy of the same fact
  — and an expensive one, since `left_axis_width` reserved 190px for them.
- **One tick per date group.** `_render` builds `self._date_groups` as
  `[(label, first_row, last_row)]` — one entry today, because one report is one
  day. A second day is a second entry, not a rewrite.
- **The label is pinned to the middle of the *visible* part of its block**
  (`_place_date_ticks`, called from `_update_y_window` so it re-runs on every
  scroll and resize). Pinned to the true center, scrolling a long day scrolls
  that day's own label off the chart.
- **`left_axis_width` 190 → 104** — what `'Tue, Jun 23'` needs. The reclaimed
  86px goes straight into bar width, so more bars fit their text.
- **The room outranks the times inside the bar when only one fits.** The second
  line needs vertical space a busy day does not have, so with the axis no
  longer carrying the room it would otherwise have appeared nowhere. Two lines:
  times right, room below. One line: room right, times give way. Spilled labels
  carry the room too, joined to the name with a middot.
- **Multi-day is now an axis-free change**: give the gantt rows a date and build
  `_date_groups` per day. Verified by driving `_place_date_ticks` with two
  simulated blocks — both labels appear, each pinned to its own visible portion,
  and a block scrolled fully out drops its label.
- **Known gap**: exact times now appear only on two-line bars, which need a
  light day for the height. A compact range (`9:00–11:30 AM`, one meridiem when
  both ends share it) would make them fit far more often.

## Earlier Completed (2026-08-22 — in-bar timeline labels)

- **Bars carry their own labels** (ADR-009). New `gui_components/gantt_labels.py`
  paints the event name, room, and time range onto each bar. The event name used
  to exist nowhere on the canvas — only in the hover tooltip.
- **A `GraphicsObject` painting in device pixels**, not `pg.TextItem`.
  `BarGraphItem` cannot draw text and a `TextItem` cannot measure its own bar,
  so it cannot elide. Mapping the corners through `painter.transform()` and then
  drawing under an identity transform gives fixed-size type *and* the bar's true
  pixel box, so the layout re-fits on every resize with no extra plumbing.
- **A degradation ladder keyed on measured width**: name + times + room on two
  lines → name + times → name elided → the name drawn *outside* the bar in
  `text_muted` when the bar is under ~9 average characters wide. The spill rung
  is what makes it work on a real day; it is safe because there is exactly one
  event per row, so the space beside a bar is always free.
- **The name never yields characters to the times** — times are drawn only when
  the full unelided name fits beside them. The room's second line is
  all-or-nothing, because an elided room reads as a bug when the whole string is
  on the Y axis a few inches to the left.
- **Row-height floor + vertical scrollbar** (`_update_y_window`). Rows used to
  divide the viewport however many events there were — 40 events in a 640px
  window left each bar ~9px tall, too short to label. The floor comes from the
  label font's own metrics (`min_row_height`), not a hardcoded pixel count, so
  it holds at any display scaling. A day that fits behaves exactly as before and
  the scrollbar stays hidden. The wheel scrolls (pan/zoom were already off).
- **`ink_on(fill)` in `style.py`** picks each label's ink by WCAG contrast ratio
  between two tokens the system already had. Measured across every palette slot
  in both its light and dark step: worst case `#2a78d6` at **4.4:1**, rest ≥5:1.
- **`bar_height` 0.62 → 0.78** — bars carry text now, so the row space is better
  spent on the bar than on the gap.
- **The "now" caption was dropped.** With every row carrying text the
  `InfiniteLine` label had nowhere to sit without covering an event; the red
  dashed rule against an hour-labeled axis carries it alone.
- **The hover tooltip stays**, covering very short events and long room names
  that the 190px Y-axis gutter still hard-clips. It now reads the same
  pre-formatted `times` string the bar does, so the two cannot disagree.
- **The hover card is now held open** for as long as the cursor is on the bar.
  Qt's own expire timer was pulling it after ~3.5s (measured, not assumed —
  the default is text-length-derived, not the 10s the docs imply). Passing
  `msecShowTime` to `showText` overrides it; hiding is driven by `_on_hover`
  for a move onto another bar or into empty space, and by a `QEvent.Leave`
  case in `eventFilter` for a cursor that leaves the plot without a final move
  event landing off a bar.
- **The card follows the cursor.** Qt treats a repeat `showText` with unchanged
  text as a no-op, so it used to sit wherever it first appeared. Passing a
  one-pixel `rect` at the cursor makes Qt's own `tipChanged()` true on the next
  move, which is what repositions it — and Qt's `placeTip` keeps it clear of
  screen edges for free. The anchor is the *event's* mapped position, not
  `QCursor.pos()`, so the card cannot drift from the bar it describes.
- **Verified against all eight paths** — appears, follows along one bar, keeps
  its text on the same bar, holds past 6s idle, swaps between bars, both hide
  routes, and re-show. Note for future GUI probes: `sigMouseMoved` fires from
  the *real* pointer whenever `processEvents()` runs, so a test window that
  opens under the cursor will corrupt every reading. Disconnect the signal and
  drive `_on_hover` synthetically.
- **Verified by rendering**, not just by tests: offscreen grabs (via
  `WA_DontShowOnScreen`, so real fonts are used) of a light day, a 34-event day,
  a 620px-wide window, the scrolled-to-bottom state, and dark mode. Report
  switching, an empty report, a theme flip, and a building recolor were each
  driven through their real code paths. 87/87 tests still pass.

## Earlier Completed (2026-08-22 — Daily Events Excel source)

- **New reader** `daily_events_excel.py` (`DailyEventsExcelProcessor`) reads the
  export's `Parameter Summary` (report date) and `Event List <date>` sheets.
  One row per booking, which is already how the PDF path models an
  event-in-a-room, so an event in two rooms correctly yields two records.
- **Shared base class** (ADR-008): `SetupReportProcessor` was split into
  `EventScheduleProcessor` (config, whitelist, time parsing, schedule rows,
  sorting, output, Gantt feed) plus one subclass per format. A subclass supplies
  only `_validate_suffix()`, `extract_report_date()` and `_collect_events()`.
- **The refactor was verified structurally, not just by tests**: the PDF methods
  were sliced across verbatim and an AST comparison confirms 18 method bodies
  are byte-identical. Only `__init__`, `process()` and `get_output_basename()`
  changed, all deliberately.
- **Extension dispatch**: `create_processor()` + `SUPPORTED_SUFFIXES` in
  `setup_report_processor.py` are the one place that says what the app accepts;
  the CLI, `worker.py` and `drop_zone.py` all read it. No mode switch, no new
  stage, no new persisted preference — a mixed PDF + xlsx batch just works.
- **`Setup Ready By` = `Event Start`** for the Excel source. The export has no
  setup-start column and this is the PDF parser's own third fallback, so nothing
  is invented — but xlsx schedules carry **no setup lead time**. If the report
  builder can emit a reservation/setup start, it is a one-line change in
  `_parse_event_row()`.
- **One whitelist for both sources.** The export's `Location Search` is
  `All Locations`, so it carries rooms the PDF never had (`FH Gym`,
  `Pk Lot E3/E4`, `FH Ice Arena`); they are excluded until enabled in the
  Locations editor.
- **Robustness**: every `Event List` sheet is read (a multi-day export is not
  truncated to its first day); a missing required column raises `ValueError`
  naming it, which the worker now surfaces on the file card instead of the old
  fixed "not a readable PDF" text; `.xls` gets a pointed re-save message.
- **Two non-obvious details worth remembering**:
  - The reader logs to `setup_report_processor.daily_events_excel`, a *child* of
    the logger `gui_wrapper.py` attaches its panel handler to. A plain
    `getLogger(__name__)` would propagate to the root logger instead and its
    EXCLUDED lines would never reach the log panel.
  - `daily_events_excel` is imported *inside* `create_processor()`; it imports
    the base class from `setup_report_processor`, so a module-level import
    would be circular.
- **Times stay strings** (`"9:00 AM"`), built by hand rather than with
  `strftime` (`%I`/`%p` are locale-dependent). This reuses `parse_time()` and
  `convert_to_24hour()` unchanged, midnight-crossing included.
- **Tests**: 56 → 87. New `TestExcelTimeFormatting`, `TestDailyEventsExcel` and
  `TestProcessorFactory`. Fixtures build their own workbooks in `tmp_path` —
  `.gitignore` ignores `*.xlsx`, so a test reading the sample file would pass
  locally and fail on a clean clone.
- **Verified end to end**: `python setup_report_processor.py DailyEventsExcel.xlsx`
  yields 2 events → 4 rows (FSL Retreat in `UC 1225` and `UC Kochoff Hall C`,
  9:00 AM / 3:30 PM), basename `08-22-26` from the Parameter Summary, with the
  four non-whitelisted rooms logged as excluded.

## Earlier Completed (2026-08-04 — changelog extracted)

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

- [ ] Run the Excel path against more real exports (multi-day, and a day whose
      events actually land in whitelisted rooms) — the sample only exercises two
- [ ] Confirm the PDF path is byte-identical on a **real** PDF; no PDF is
      checked in, so this was verified structurally and by the suite, not by a
      real end-to-end diff
- [ ] Verify the overhauled UI on a real (scaled) display, dropping a PDF and an
      export in one batch — now also: confirm the in-bar labels and the timeline
      scrollbar on a real busy day
- [ ] Rebuild the portable exe with the new Qt/pyqtgraph deps
- [x] Refresh `documentation/README_GUI.md` and `QUICKSTART.md` for the staged UI
- [x] Update the top-level README for the staged UI, Settings menu, and timeline
- [x] Rewrite `.context/SETUP.md` (stale `requirements-gui.txt`, tkinterdnd2, `input/`)
- [x] Remove obsolete MATLAB artifacts (`GanttChartApp.mlapp`/`.txt`) and code references

## Next Up

1. Run `python gui_wrapper.py`, process a real PDF **and** a real Excel export in
   one batch, open **View Timeline**, and confirm crispness on a scaled display
   in both light and dark mode. Check the in-bar labels specifically: real event
   names are longer than the test fixtures, so watch where the ladder lands and
   whether `MIN_NAME_CHARS` (9) is the right spill threshold in practice
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
setup_report_processor.py    [status: split into EventScheduleProcessor + SetupReportProcessor; +create_processor]
daily_events_excel.py        [status: new — Daily Events Excel export reader]
gui_wrapper.py               [status: 3-stage MainWindow + Settings menu; copy now source-neutral]
gui_components/              [status: worker dispatches via create_processor; drop_zone reads SUPPORTED_SUFFIXES]
gui_components/gantt_labels.py [status: new — in-bar label painter, device-pixel layout]
gui_components/gantt_window.py [status: bars labeled; row floor + vertical scroll]
location_config.json         [status: stable, v2 format]
test_setup_report_processor.py [status: stable, 87/87 passing]
requirements.txt             [status: updated, +PySide6 +pyqtgraph]
UUE.ico                      [status: app icon — must ship beside exe for window icon]
build_release.bat            [status: new — builds + zips the portable release]
```

## Recent Decisions

- **2026-08-22**: Multiple days stack on one timeline, keyed by the date the
  events carry rather than by the file they came from (ADR-011)
- **2026-08-22**: The Gantt Y axis names the day, grouped so a second day is a
  second entry rather than an axis rewrite (ADR-010)
- **2026-08-22**: Inside a bar the room outranks the time range when only one
  fits — the X axis already places the event, nothing else names the room
- **2026-08-22**: Timeline bars carry their own labels, with a font-derived row
  floor and scrolling instead of unbounded row compression (ADR-009)
- **2026-08-22**: The Gantt hover card is held open via `showText`'s
  `msecShowTime`, follows the cursor via a one-pixel `rect` that forces Qt's
  `tipChanged()`, and is hidden by our own hit-testing rather than by Qt's
  expire timer — it is a fallback for what a bar could not print, so it has to
  last as long as the cursor is on the bar
- **2026-08-22**: Label ink is derived from the bar fill by WCAG contrast
  (`ink_on`), because the building palette spans too wide a luminance range for
  any single label color
- **2026-08-22**: Second event source via a shared base class and extension
  dispatch, not a parallel script (ADR-008)
- **2026-08-22**: Excel `Setup Ready By` comes from `Event Start`; the whitelist
  filters both sources identically
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

- **Two sources now.** `create_processor()` picks by extension; `SUPPORTED_SUFFIXES`
  beside it is the only list of accepted types. Adding a third source is a
  subclass with three methods, not a fork
- The Excel export has no setup-start column — `Setup Ready By` is the event's
  own start time, so those schedules carry no setup lead time
- The Excel reader must log to a **child** of the `setup_report_processor`
  logger, or its lines never reach the GUI log panel
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
