# Architecture Decision Records

---

## ADR-001: pdfplumber for PDF text extraction

**Date**: 2025 (project inception)
**Status**: Accepted

**Context**:
Need to extract structured text from Daily Setup Report PDFs with tabular layout.

**Decision**:
Use pdfplumber for PDF text extraction.

**Rationale**:
- Layout-aware text extraction preserves table structure
- Better handling of multi-column PDFs than PyPDF2
- Active maintenance and good documentation

**Consequences**:
- (+) Reliable extraction of tabular PDF data
- (-) Extracted text format is dependent on PDF layout; changes in PDF generation can break parsing

**Alternatives considered**:
- PyPDF2: Less accurate for tabular layouts
- tabula-py: Java dependency, overkill for text-only extraction

**Relevant code**: `setup_report_processor.py:110-133`

---

## ADR-002: Whitelist/Blacklist location filtering

**Date**: 2025 (project inception)
**Status**: Accepted

**Context**:
PDFs contain events in many locations, but only certain building/room prefixes are relevant to the schedule output.

**Decision**:
Use a prefix-based whitelist (`VALID_LOCATION_PREFIXES`) combined with a substring-based blacklist (`EXCLUDED_LOCATIONS`) as class-level constants.

**Rationale**:
- Simple to understand and maintain
- Blacklist catches specific exceptions within whitelisted prefixes (e.g., "UC Table-Bake/Day Sale" within "UC " prefix)
- Class constants are easy to find and edit

**Consequences**:
- (+) Clear, readable filtering logic
- (-) Requires code changes to modify filters; no external config file yet

**Alternatives considered**:
- External config file (YAML/JSON): More flexible, but adds complexity; deferred to Phase 4
- Database-driven rules: Overkill for this use case

**Relevant code**: `setup_report_processor.py:38-53, 455-475`

---

## ADR-003: Negative lookbehind for event block splitting

**Date**: 2026-02-04
**Status**: Accepted

**Context**:
The regex `(?=\d{1,2}:\d{2} [AP]M Setup Starts:)` used to split PDF text into event blocks was incorrectly splitting "11:30 AM Setup Starts:" into two blocks. The regex engine found a valid match starting at the first "1" in "11", producing blocks starting with "1:30 AM Setup Starts:" instead of "11:30 AM Setup Starts:".

**Decision**:
Add a negative lookbehind `(?<!\d)` to the split pattern: `(?=(?<!\d)\d{1,2}:\d{2} [AP]M Setup Starts:)`. This ensures the match only occurs when there is no digit immediately preceding the time.

**Rationale**:
- Prevents the regex engine from matching at a position inside a two-digit hour
- Minimal change with no impact on single-digit hour parsing
- No false positives: there is never a legitimate case where a digit should precede the time in this context

**Consequences**:
- (+) All 11:XX and 12:XX times now parse correctly
- (+) Single-digit hours (1:00-9:00) unaffected
- (-) None identified

**Alternatives considered**:
- Word boundary `\b`: Also works but less explicit about the intent
- Anchoring to start-of-line: Would break if pdfplumber doesn't always produce clean line breaks

**Relevant code**: `setup_report_processor.py:280`

---

## ADR-004: Migrate GUI to PySide6 and replace MATLAB Gantt with embedded pyqtgraph

**Date**: 2026-06-23
**Status**: Accepted

**Context**:
The Gantt chart display was an external MATLAB App (`GanttChartApp.mlapp`), launched via `matlab -r`
with the CSV passed through the `GANTT_CSV_PATH` environment variable. This required every user to
install and license MATLAB separately — a heavy external dependency that defeats the point of the
portable-exe distribution. Separately, the tkinter GUI renders blurry on high-DPI / scaled Windows
displays because tkinter registers as DPI-unaware and the OS bitmap-stretches the window.

**Decision**:
- Rewrite the GUI layer from tkinter to **PySide6** (Qt for Python, LGPL).
- Replace the external MATLAB app with an **embedded pyqtgraph Gantt chart**, opened in a separate
  window via a "View Gantt" button.
- Remove the MATLAB CSV output and launch code entirely. Keep the row-shaping helper
  (Location, StartTime 24h, EndTime 24h) renamed to `create_gantt_rows()` as the chart's data source.
- In-place replacement (no parallel tkinter build retained).

**Rationale**:
- **PySide6**: true per-monitor high-DPI with vector text — fixes the blur at the framework level.
  LGPL allows shipping in the closed-source portable exe. Native DnD removes the `tkinterdnd2` dependency.
- **pyqtgraph**: fast, DPI-crisp, ideal for redrawing the live current-time line every 60s (QTimer),
  a direct port of the MATLAB timer behavior.
- The core engine (`setup_report_processor.py`) is pure logic and is untouched except for removing the
  MATLAB output path — keeps the migration bounded to the UI layer.

**Consequences**:
- (+) No external MATLAB dependency; chart lives inside the app
- (+) Crisp rendering on scaled displays
- (+) Drops `tkinterdnd2`; adds `PySide6` + `pyqtgraph`
- (-) Larger exe (~40–70 MB) carrying Qt; PyInstaller build flags change
- (-) Full UI-layer rewrite; no working build during the in-place migration

**Alternatives considered**:
- Keep tkinter + `SetProcessDpiAwareness` DPI fix: band-aid; Tk text still not vector-crisp
- CustomTkinter: better look, still Tk rendering underneath
- Matplotlib (QtAgg) for the chart: viable, closest port of MATLAB drawing, but pyqtgraph is lighter
  and better at the live-updating time line
- Plotly/Flet: browser/heavier; rejected for an in-app live ops view

**Mobile note**: A future mobile app is treated as a separate effort (likely Flutter or a FastAPI
backend + native front-end), not served by this Qt desktop work.

**Relevant code**: `gui_wrapper.py`, `gui_components/`, `setup_report_processor.py` (MATLAB code removed)

---

## ADR-005: Staged single-page GUI with a custom theme

**Date**: 2026-08-05
**Status**: Accepted

**Context**:
The PySide6 GUI from ADR-004 was functional but read as a flat stack of controls:
drop zone, file list, options group, five equal-weight buttons, progress, and a
large always-visible log. Nothing signaled where to start, the primary action
looked identical to one-time setup actions like "Add Desktop Shortcut", and the
log dominated the window. New users could not tell what to do without being told.

**Decision**:
Restructure the window into three stages driven by a `QStackedWidget` — empty,
workspace, results — and ship a custom design system (`gui_components/style.py`)
rather than inheriting raw Qt defaults.

- Stage 1 (empty): hero drop target plus a three-step "how it works" strip
- Stage 2 (workspace): compact "add more" strip, per-file queue cards with live
  status, output format toggles, and one primary call to action
- Stage 3 (results): outcome icon, metrics (files / events / issues), where the
  output went, and the two likely next actions
- The processing log moved behind a persistent "Details" disclosure that badges
  warning/error counts and auto-expands when a run produces either
- One-time setup (location whitelist, output folder, desktop shortcut, log file,
  preferences) moved into a Settings menu in the header
- `apply_theme()` sets the Fusion base style plus app-owned light/dark palettes
  built on UM-Dearborn Michigan Blue and Maize; Maize is reserved for the single
  primary action so it is never ambiguous

**Rationale**:
- Staging removes the "which of these fifteen controls do I touch?" problem
  without hiding anything a returning user needs
- Owning the palette means the app looks identical on every machine, and the
  accent can carry meaning (primary action only) rather than being decorative
- A results screen replaces a modal alert that told the user nothing actionable

**Consequences**:
- (+) The next step is always the most visually prominent thing on screen
- (+) Errors surface via a badge instead of being buried in a wall of log text
- (-) More styling code to maintain; custom-painted widgets must read the active
  scheme from `style.tokens()` rather than asking the OS, or a forced light/dark
  run paints half the UI from the wrong palette
- Behavior change: the timeline is no longer a selectable "output" — it is always
  available after a run. Deselecting both file formats is therefore not an error
  but a **timeline-only run**: the button reads "Preview N files", nothing is
  written, and the output folder is not even created. This preserves what the old
  "Gantt only" output option allowed, without the third checkbox

**Alternatives considered**:
- Two-pane workspace (sidebar + results): denser and more app-like, but better
  for power users than the newcomers this change targets
- Restyle only, same layout: smallest diff, but leaves the core complaint intact

**Relevant code**: `gui_components/style.py`, `gui_components/widgets.py`,
`gui_components/result_panel.py`, `gui_wrapper.py`

---

## ADR-006: Color Gantt bars by building, configured by the user

**Date**: 2026-08-05
**Status**: Accepted

**Context**:
The Gantt chart cycled a ten-color qualitative palette across event bars by list
position. Color therefore encoded nothing — each bar already carries its own
location label on the Y axis — and the same venue changed color between reports.

**Decision**:
Color bars by the building the event is in, derived from the room-name prefix
(`UC 1225` → `UC`). Buildings are **discovered, not hardcoded**, and their colors
are **user configuration**, edited in Settings → Building Colors… and persisted
in `location_config.json` under an additive `buildings` key.

- A prefix appearing in the enabled whitelist or in a processed report gets an
  entry automatically, assigned the lowest unused palette slot
- Assignments are persisted on creation, so a building never changes color
  between reports (color follows the entity, never its rank)
- Colors are stored as **palette slot indices**, not free hex, so each keeps a
  light-surface and dark-surface step and every offered color has been checked
  for colorblind separation and surface contrast
- Buildings sharing a color collapse into **one legend entry**

**`UC` and `RUC` are the same building** — the University Center was renamed the
Renick University Center, but existing room records kept their old `UC` prefixes,
so both stay in active use. Rather than a hardcoded alias, this is expressed by
giving both prefixes the same color (shipped that way in `DEFAULT_BUILDINGS`),
which is also how a user resolves any future rename without a code change.

**Rationale**:
- A new campus building (CASL, ELB, …) needs no code change — the earlier
  hardcoded prefix map would have dropped it into gray "Other"
- Same-color-means-same-building is a simpler user model than an alias concept,
  and it makes the legend merge fall out for free
- Slot indices keep the theme-aware and accessibility guarantees that free-form
  hex (or the originally suggested random color) would have thrown away

**Consequences**:
- (+) Buildings are self-maintaining; renames are a user setting, not a release
- (-) Only the first 3 slots stay mutually distinguishable under every colorblind
  simulation at once (`SAFE_SLOT_COUNT`). Past that the dialog marks slots with
  `*` and leans on the Y-axis location labels, which every bar always has
- (-) Colors are restricted to the 8 validated slots plus neutral gray; there is
  no arbitrary color picker
- `create_gantt_rows()` now also emits `EventName`, used for the hover tooltip

**Alternatives considered**:
- Hardcoded prefix → building map in `settings.py`: what this replaced; every new
  building required a code edit and a rebuilt exe
- Random auto-assigned colors (as first proposed): removes the manual step but
  regularly produces pairs a colorblind viewer cannot separate, or a color that
  disappears against the chart surface

**Relevant code**: `gui_components/building_config.py`,
`gui_components/building_editor.py`, `gui_components/gantt_window.py`,
`setup_report_processor.py:create_gantt_rows`

---

## ADR-007: Persist interface preferences in their own file

**Date**: 2026-08-04
**Status**: Accepted

**Context**:
Every choice in the Settings menu — output folder, Excel/CSV formats, open the
timeline when finished, verbose logging, and the new keep-awake toggle — reset
to its default on every launch. For a tool someone opens daily to process the
same reports into the same folder, that is a small chore repeated forever.

`location_config.json` was the obvious place to put them: it already carries two
independent blocks (`locations` and `buildings`, ADR-006), and a third would have
been additive in the same way.

**Decision**:
Persist them in a **separate** `gui_preferences.json`, written beside the
executable, and read/written by `gui_components/preferences.py`.

- Defaults are not restated — `Preferences.defaults()` reads `GUI_DEFAULTS` from
  `settings.py`, which stays the single source of truth
- Saved on change, not on exit, so a crash never costs a setting
- A missing, malformed, or partial file falls back to defaults and logs; it is
  treated as "first run", never as an error
- An `output_dir` whose parent no longer exists (another machine, an unplugged
  drive) falls back to the default rather than failing at the end of a run
- Only what the OS actually granted is remembered: a refused keep-awake request
  persists as off, so a machine that cannot honour it does not keep retrying

**Rationale**:
- `location_config.json` is *authored* configuration — it ships with the app,
  users hand-edit it, and it gets replaced wholesale between deployments.
  `gui_preferences.json` is *runtime state* the app rewrites whenever a toggle
  moves. Mixing the two means every preference change rewrites the locations
  file, putting hand edits in the blast radius of a stray click
- Both location and building editors already carry "preserve the other block"
  logic; a third writer with a different lifecycle would compound that
- The preferences file is created on demand, so it needs no entry in
  `build_release.bat` and nothing changes about the deliverable

**Consequences**:
- (+) A user configures the app once; the daily path is drag → Process
- (+) Deleting one file resets the interface without touching venue config
- (-) A second config file to explain in the docs, and one more thing that can
  go stale on the user's disk
- (-) Preferences do not travel with `location_config.json` when it is copied
  between machines — deliberate, since output paths are machine-specific
- `gui_preferences.json` is gitignored: it is per-user runtime state

**Alternatives considered**:
- A `preferences` block in `location_config.json`: rejected above — coupling
  runtime state to authored config
- `QSettings` (the Qt-native choice, registry-backed on Windows): rejected
  because the app is distributed as a portable folder. Settings living in the
  registry would not travel with the folder, would not be inspectable next to
  the exe, and could not be reset by deleting a file
- Saving on window close: loses everything if the app is killed, and would have
  needed the same `closeEvent` to also be crash-proof

**Relevant code**: `gui_components/preferences.py`, `gui_wrapper.py`
(`_remember`, `_set_verbose`, `_set_gantt_autolaunch`, `_set_keep_awake`,
`_browse_output_folder`), `gui_components/settings.py`

---

## ADR-008: Read the database's Excel export as a second event source

**Date**: 2026-08-22
**Status**: Accepted

**Context**:
Direct access to the events database removed the reason the app existed in its
original form: event data no longer has to be recovered from a rendered PDF.
The database's cleanest export is `Daily Events - Excel`, a real spreadsheet
whose `Location` column already uses the same room codes as the whitelist
(`UC 1225`, `UC Kochoff Hall C`) and which carries one row per **booking** —
which is exactly how the PDF path already models an event-in-a-room.

Parsing it is a column lookup instead of the regex stack described in ADR-001
and ADR-003. But those PDFs are still produced and still get processed, so this
had to be a second option rather than a replacement.

**Decision**:
Split `SetupReportProcessor` into a source-independent base class,
`EventScheduleProcessor`, plus one subclass per format, and dispatch on the
file's extension through `create_processor()`.

- The base owns everything downstream of extraction: config loading, whitelist
  matching, time parsing, schedule rows, sorting, output, and the Gantt feed
- Subclasses own only `_validate_suffix()`, `extract_report_date()` and
  `_collect_events()`, and return the identical event dict
- `SUPPORTED_SUFFIXES` next to `create_processor()` is the one place that says
  what the app accepts; the CLI, the worker, and the drop zone all read it
- **`Setup Ready By` comes from `Event Start`.** The export has no setup-start
  column, and this is precisely what `_extract_setup_time()` already does as
  its third fallback, so no data is invented
- **One whitelist filters both sources.** The export's `Location Search` is
  `All Locations`, so it carries rooms the PDF never had (`FH Gym`,
  `Pk Lot E3`); they are excluded until enabled in the Locations editor

**Rationale**:
- A parallel script would have duplicated sorting, filtering, output and Gantt
  logic, and the two copies would have drifted the first time either changed
- Extension dispatch needs no new UI: no mode switch, no extra stage, no
  preference to persist, and a mixed batch of PDFs and exports just works
- Keeping the shared event dict string-typed (`"9:00 AM"`) means the Excel path
  reuses `parse_time()` and `convert_to_24hour()` — including their tested
  midnight-crossing behaviour — rather than introducing a second time model
- The refactor was verified by slicing the PDF methods across verbatim: 18
  method bodies are byte-identical, and all 56 pre-existing tests pass unedited

**Consequences**:
- (+) The daily path no longer depends on PDF layout, the app's most fragile
  input; a pdfplumber quirk can no longer silently drop an event
- (+) A new source (a CSV, a direct query) is now a subclass, not a fork
- (−) An xlsx-derived schedule has **no setup lead time** — its "Setup Ready By"
  is the event's own start, so it will be later than the same event's row from
  a PDF. If the report builder can emit a reservation/setup start, adding it is
  a one-line change to `_parse_event_row()`
- (−) `daily_events_excel` is imported inside `create_processor()` rather than
  at module scope, because it imports the base class from
  `setup_report_processor` and a top-level import would be circular
- (−) The reader logs to `setup_report_processor.daily_events_excel`, a child of
  the logger the GUI attaches its panel handler to. A plain
  `getLogger(__name__)` would have propagated to the root logger instead, and
  its EXCLUDED lines would never have reached the log panel

**Files**:
`daily_events_excel.py`, `setup_report_processor.py:EventScheduleProcessor`,
`setup_report_processor.py:create_processor`

## ADR-009: Label the timeline bars themselves, with a readable row floor

**Date**: 2026-08-22
**Status**: Accepted

**Context**:
Every bar on the timeline was an unlabeled rectangle. An event's name lived
only in the hover tooltip (`_on_hover`), so the chart could not be read at a
glance, screenshotted, or left up on a display — which is the main thing the
keep-awake setting exists for.

Two properties of the chart made "just draw the text" insufficient:

- The X range is fixed at 6–24h and pan/zoom are deliberately off (ADR-004), so
  a bar is roughly 40px per hour. A thirty-minute event is a ~20px rectangle.
- `setYRange(0, idx)` divided the viewport across however many events there
  were. Forty events in a 640px window gave each bar ~9px of height — shorter
  than any readable type, so labels would have silently vanished on exactly the
  busiest days.

**Decision**:
- **A `GraphicsObject` that paints in device pixels** (`gantt_labels.py`),
  not `pg.TextItem`. `BarGraphItem` cannot draw text at all, and a `TextItem`
  per bar cannot measure the bar it belongs to, so it cannot elide. Mapping the
  data-space corners through `painter.transform()` and then drawing under an
  identity transform gives both fixed-size type and the bar's true pixel box,
  so the layout re-fits itself on every resize with no extra plumbing.
- **A degradation ladder, keyed on measured width**: name + times + room on two
  lines → name + times → name elided → and, under ~9 average characters of
  room, the name drawn *outside* the bar in `text_muted`.
- **The name never yields characters to the times.** The times are only drawn
  when the full, unelided name fits beside them.
- **The room's second line is all-or-nothing.** An elided room reads as a bug
  when the whole string is on the Y axis a few inches to the left.
- **A row-height floor plus a vertical scrollbar** (`_update_y_window`). The
  floor is derived from the label font's own metrics (`min_row_height`), not a
  hardcoded pixel count, so it holds at any display scaling. A day that fits
  behaves exactly as before and the scrollbar stays hidden.
- **`ink_on(fill)` in `style.py`** picks each label's ink by WCAG contrast
  ratio, between two tokens the system already had (`LIGHT["on_brand"]` and
  `DARK["bg"]`).
- **`bar_height` 0.62 → 0.78.** Bars carry their own labels now, so the row
  space is better spent on the bar than on the gap.
- **The hover tooltip stays**, covering what the pixels cannot: very short
  events and long room names the 190px Y-axis gutter still hard-clips.

**Rationale**:
- The palette (ADR-006) spans a wide luminance range on purpose — `#eda100`
  needs dark ink, `#4a3aa7` needs light. One fixed label color would have
  failed on half the buildings. Deriving the ink from the fill was measured
  across every slot in both its light and dark step: the worst case is
  `#2a78d6` at **4.4:1**, and the rest clear 5:1.
- The spill-outside rung is what makes the feature work on a real day. Without
  it only the long events would ever be labeled. It is safe because the chart
  puts **one event per row**, so the space beside a bar is always free.
- The floor is a genuine trade, made deliberately: the chart loses
  "whole day on one screen" on busy days and gains labels that always work.
- The times and room duplicate what the axes already carry, but the axis only
  approximates a time and the Y-axis room is easy to lose track of when
  scanning across; the elision rules keep the duplication from costing the name
  any room.

**Consequences**:
- (+) The timeline reads without a mouse, and survives a screenshot.
- (+) `ink_on` is general — anything painted on an arbitrary fill can use it.
- (−) **The "now" caption is gone.** Every row carries text now, so the
  `InfiniteLine` label had nowhere left to sit without covering an event; the
  red dashed rule against an hour-labeled axis carries it alone.
- (−) A day with more events than fit **scrolls**, where it used to compress.
- (−) The room shown inside a bar repeats its Y-axis tick label. This was a
  deliberate call — all three tooltip fields were wanted in the bar. Dropping
  the Y-axis labels would reclaim `left_axis_width` (190px, ~23% more bar width
  for text) if that duplication ever grates.
- (−) `gantt_labels.py` is the one module in the app that measures in device
  pixels rather than layout units. `PAD_X`/`GAP`/`MIN_NAME_CHARS` are tuned
  numbers, not tokens.

**Files**:
`gui_components/gantt_labels.py` (new), `gui_components/gantt_window.py`,
`gui_components/style.py:ink_on`, `gui_components/settings.py:GANTT`
