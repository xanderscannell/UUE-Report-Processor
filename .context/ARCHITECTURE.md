# System Architecture

## High-Level Overview

The application reads an event report — either a Daily Setup Report PDF or
the events database's Daily Events Excel export — extracts the events, filters
them by location rules, and generates sorted schedule files in multiple formats.

```
PDF File  ──► SetupReportProcessor  ─┐
                                     ├─► EventScheduleProcessor ──► Excel/CSV
Excel File ─► DailyEventsExcel…     ─┘   (shared pipeline)          + timeline
                     ▲
              create_processor() picks by file extension
                     │
              GUI Wrapper (optional)
              ├── DragDropZone
              ├── FileListManager
              └── ProcessorWorker (background thread)
```

**Where the split falls.** Everything after event extraction is identical for
every source and lives on `EventScheduleProcessor`. A format subclass supplies
only three things: which extensions it accepts, the report date, and the event
list. Both produce the same record — `{event_name, location, setup_time,
closing_time}` — with times as `"9:00 AM"` strings, so the Excel path reuses the
PDF path's time parsing rather than introducing a second time model (ADR-008).

## Components

### EventScheduleProcessor

**Purpose**: Shared pipeline from event records to a sorted schedule
**Tech stack**: Python, pandas, openpyxl
**Key files**:
- `setup_report_processor.py`

**Interfaces**:
- Input: event dicts from a format subclass
- Output: Excel (.xlsx), CSV (.csv), Gantt rows

**Notes**:
- Owns config loading, whitelist matching, time parsing, schedule rows,
  sorting, and output — everything that does not depend on the file format
- `process()` orchestrates the pipeline, calling the subclass's
  `_collect_events()` for the format-specific part
- `create_processor(path)` picks the subclass by extension; `SUPPORTED_SUFFIXES`
  beside it is the single source of truth for what the app accepts, read by the
  CLI, the worker, and the drop zone

---

### SetupReportProcessor

**Purpose**: Reads Daily Setup Report PDFs
**Tech stack**: Python, pdfplumber
**Key files**:
- `setup_report_processor.py`

**Interfaces**:
- Input: PDF file path (Daily Setup Report format)
- Output: event dicts for the shared pipeline

**Notes**:
- Class-level constants define the location whitelist and cleanup patterns
- Text extraction relies on pdfplumber's layout-aware parsing; the extracted
  text format is critical to all downstream regex patterns (ADR-001, ADR-003)
- `pdf_path` is kept as an alias for the base class's `source_path`

---

### DailyEventsExcelProcessor

**Purpose**: Reads the events database's Daily Events Excel export
**Tech stack**: Python, openpyxl
**Key files**:
- `daily_events_excel.py`

**Interfaces**:
- Input: `.xlsx` path (Daily Events - Excel format)
- Output: event dicts for the shared pipeline

**Notes**:
- Two sheets: `Parameter Summary` (report date) and `Event List <date>`
  (headers on row 1, one row per booking). Every `Event List` sheet is read, so
  a multi-day export is not truncated to its first day
- The report date falls back Parameter Summary → sheet title → `Day` column,
  because these files carry a generic name (`DailyEventsExcel.xlsx`)
- A missing required column raises `ValueError` naming it, which the worker
  surfaces on the file card rather than failing obscurely
- **No setup-start column exists**, so `Setup Ready By` is the event's own start
  time — the PDF parser's own third fallback (ADR-008)
- Logs to `setup_report_processor.daily_events_excel`, a child of the logger the
  GUI panel attaches to, so its EXCLUDED lines reach the log panel

---

### GUI Application

**Purpose**: Drag-and-drop interface for batch processing PDFs
**Tech stack**: Python, PySide6 (Qt), pyqtgraph
**Key files**:
- `gui_wrapper.py` (`MainWindow`, `QApplication` entry point)
- `gui_components/` (7 modules)

**Interfaces**:
- Input: PDF files via native drag-and-drop or file dialog
- Output: Excel/CSV files in configured output directory; in-app Gantt chart

**Notes**:
- `ProcessorWorker` is a `QThread`; communicates with the GUI via Qt signals
  (delivered on the GUI thread automatically — no manual queue polling). It
  reports per-file outcomes (`file_started`/`file_done`) plus a run summary dict
  on `finished_all`, which drives the queue status glyphs and the results screen
- Files can be dropped anywhere in the window, not just on the drop zone
- High-DPI crisp rendering (Qt6 per-monitor scaling, `PassThrough` rounding policy)
- Native Qt drag-and-drop — the old `tkinterdnd2` dependency is gone
- See [DECISIONS.md](DECISIONS.md) ADR-004 for the tkinter→PySide6 migration

---

### GUI Components

**Purpose**: Modular, reusable UI widgets (PySide6)
**Key files**:
- `gui_components/style.py` — **design system**: color tokens, spacing/type scale,
  `build_stylesheet()`, `apply_theme()`; owns the active light/dark scheme
- `gui_components/theme.py` — OS color-scheme detection (`is_dark_mode`)
- `gui_components/widgets.py` — shared primitives: `Card`, `HeaderBar`,
  `CollapsibleSection`, painted icons (`DropIcon`, `OutcomeIcon`, `StatusGlyph`)
- `gui_components/settings.py` — behavioral defaults, dimensions, Gantt config
- `gui_components/drop_zone.py` — native drag-and-drop `QFrame` (hero + compact)
- `gui_components/file_list.py` — file queue of `FileRow` cards with live status
- `gui_components/result_panel.py` — post-run summary screen
- `gui_components/keep_awake.py` — `KeepAwake`, an optional OS sleep/display
  inhibitor (Windows `SetThreadExecutionState`); a no-op elsewhere
- `gui_components/preferences.py` — `Preferences`, persisted to
  `gui_preferences.json` beside the exe (see ADR-007)
- `gui_components/log_handler.py` — `QtLogHandler` (logging→Qt signal) + `LogPanel`
- `gui_components/location_editor.py` — whitelist editor `QDialog`
- `gui_components/building_config.py` — building prefix → label + palette slot;
  discovery, auto-assignment, and persistence (see ADR-006)
- `gui_components/building_editor.py` — Building Colors `QDialog`
- `gui_components/worker.py` — `ProcessorWorker` background `QThread`
- `gui_components/gantt_window.py` — embedded pyqtgraph event timeline

**Theming rule**: custom-painted widgets must read colors from `style.tokens()`,
which returns the scheme `apply_theme()` selected. Asking the OS directly
(`is_dark_mode()`) inside a widget breaks any forced light/dark run.

**Two config files, two lifecycles.** `location_config.json` is authored
configuration — it ships with the app, is hand-editable, and gets replaced
wholesale. `gui_preferences.json` is runtime state the app rewrites whenever a
toggle moves, created on demand and gitignored. Keeping them apart means a stray
click on a preference can never put hand-edited venue config at risk (ADR-007).

**`location_config.json` holds two independent blocks**: `locations` (read by
both the processor and the GUI) and `buildings` (GUI only — timeline colors). The
processor reads only `version` and `locations`, so `buildings` is additive and the
file stays at version 2. Both editors preserve the other's block when saving.

---

### GUI Stages

The main window is a `QStackedWidget` over three stages (see ADR-005):

| Stage | Shown when | Contents |
|-------|-----------|----------|
| `STAGE_EMPTY` | queue is empty | hero drop zone + 3-step explainer |
| `STAGE_WORK` | files queued or running | compact drop strip, file cards, output toggles, primary CTA / progress |
| `STAGE_DONE` | a run finished | `ResultPanel` — metrics and follow-up actions |

A persistent "Details" disclosure (collapsed log with a warning/error badge) sits
below the stack in every stage. One-time setup lives in the header Settings menu.

---

## Data Flow

1. **Input**: User provides a report; `create_processor()` picks the reader by
   extension (`.pdf` or `.xlsx`)

**PDF branch** (`SetupReportProcessor`):

2. **Text Extraction**: `extract_text_from_pdf()` uses pdfplumber to extract all text, page by page
3. **Block Splitting**: `extract_events()` splits text on `(?=(?<!\d)\d{1,2}:\d{2} [AP]M Setup Starts:)` pattern into event blocks
4. **Event Parsing**: `_parse_event_block()` orchestrates extraction of each field:
   - `_extract_setup_time()` — setup ready by time (fallback chain: Setup Starts → Pre-Event → Event start)
   - `_extract_event_name()` — event name with reference code removal
   - `_extract_event_times()` — start and end times
   - `_extract_location()` — location with text cleanup
**Excel branch** (`DailyEventsExcelProcessor`):

2. **Sheet Selection**: `_data_sheet_titles()` finds every `Event List` sheet
3. **Header Mapping**: `_header_index()` maps column names to positions and
   fails loudly if a required column is gone
4. **Row Parsing**: `_parse_event_row()` reads one booking per row, formatting
   `Event Start` / `Event End` into the PDF path's `"9:00 AM"` strings

**Shared from here on** (`EventScheduleProcessor`):

5. **Location Filtering**: `_match_whitelist_location()` applies longest-first prefix matching
6. **Row Creation**: `create_schedule_rows()` generates 2 rows per event (Setup Ready By + Closing)
7. **Sorting**: `sort_chronologically()` parses times and sorts the DataFrame
8. **Output**: `save_to_excel()` / `save_to_csv()` write final files; `create_gantt_rows()` feeds the in-app Gantt chart

## External Dependencies

| Dependency | Purpose | Version |
|-----------|---------|---------|
| pdfplumber | PDF text extraction | 0.11.x |
| openpyxl | Excel export reading + writing | 3.1.2+ |
| pandas | DataFrame operations, CSV export | 2.1.4+ |
| openpyxl | Excel file generation | 3.1.2+ |
| PySide6 | GUI framework (Qt for Python) | 6.6+ |
| pyqtgraph | Embedded Gantt chart rendering | 0.13+ |
| pytest | Unit testing | 7.4.0+ |

## Key Design Patterns

- **Template method**: `EventScheduleProcessor.process()` fixes the pipeline; format subclasses fill in `_collect_events()` and `extract_report_date()` (ADR-008)
- **Whitelist filtering**: Location validation uses a longest-first prefix whitelist, shared by both sources
- **Fallback chain**: Setup time extraction tries 3 sources in order (lines 300-335)
- **Worker thread**: GUI processing runs in a background thread with queue-based status updates
- **Regex-driven parsing**: All event data extraction uses compiled regex patterns against pdfplumber text output

## Technology Decisions

See [DECISIONS.md](DECISIONS.md) for rationale behind technology choices.
