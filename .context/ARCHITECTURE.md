# System Architecture

## High-Level Overview

The application reads Daily Setup Report PDFs, extracts event data via regex pattern matching on pdfplumber text output, filters events by location rules, and generates sorted schedule files in multiple formats.

```
PDF File ──► SetupReportProcessor ──► Excel/CSV Output
                     │
                     ▼
              GUI Wrapper (optional)
              ├── DragDropZone
              ├── FileListManager
              └── ProcessorWorker (background thread)
```

## Components

### SetupReportProcessor

**Purpose**: Core engine that handles PDF-to-schedule conversion
**Tech stack**: Python, pdfplumber, pandas, openpyxl
**Key files**:
- `setup_report_processor.py` (lines 34-939)

**Interfaces**:
- Input: PDF file path (Daily Setup Report format)
- Output: Excel (.xlsx), CSV (.csv), MATLAB CSV (.csv)

**Notes**:
- Single class containing all processing logic
- Class-level constants define location whitelist/blacklist and cleanup patterns (lines 38-80)
- `process()` method (line 601) orchestrates the full pipeline
- Text extraction relies on pdfplumber's layout-aware parsing; the extracted text format is critical to all downstream regex patterns

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
  (delivered on the GUI thread automatically — no manual queue polling)
- High-DPI crisp rendering (Qt6 per-monitor scaling, `PassThrough` rounding policy)
- Native Qt drag-and-drop — the old `tkinterdnd2` dependency is gone
- See [DECISIONS.md](DECISIONS.md) ADR-004 for the tkinter→PySide6 migration

---

### GUI Components

**Purpose**: Modular, reusable UI widgets (PySide6)
**Key files**:
- `gui_components/settings.py` — colors, defaults, window + Gantt config
- `gui_components/drop_zone.py` — native drag-and-drop `QFrame`
- `gui_components/file_list.py` — file queue (`QListWidget`)
- `gui_components/log_handler.py` — `QtLogHandler` (logging→Qt signal) + `LogPanel`
- `gui_components/location_editor.py` — whitelist editor `QDialog`
- `gui_components/worker.py` — `ProcessorWorker` background `QThread`
- `gui_components/gantt_window.py` — embedded pyqtgraph Gantt chart (replaces MATLAB)

---

## Data Flow

1. **PDF Input**: User provides a Daily Setup Report PDF
2. **Text Extraction**: `extract_text_from_pdf()` uses pdfplumber to extract all text, page by page
3. **Block Splitting**: `extract_events()` splits text on `(?=(?<!\d)\d{1,2}:\d{2} [AP]M Setup Starts:)` pattern into event blocks
4. **Event Parsing**: `_parse_event_block()` orchestrates extraction of each field:
   - `_extract_setup_time()` — setup ready by time (fallback chain: Setup Starts → Pre-Event → Event start)
   - `_extract_event_name()` — event name with reference code removal
   - `_extract_event_times()` — start and end times
   - `_extract_location()` — location with text cleanup
5. **Location Filtering**: `_is_valid_location()` applies blacklist then whitelist rules
6. **Row Creation**: `create_schedule_rows()` generates 2 rows per event (Setup Ready By + Closing)
7. **Sorting**: `sort_chronologically()` parses times and sorts the DataFrame
8. **Output**: `save_to_excel()` / `save_to_csv()` write final files; `create_gantt_rows()` feeds the in-app Gantt chart

## External Dependencies

| Dependency | Purpose | Version |
|-----------|---------|---------|
| pdfplumber | PDF text extraction | 0.11.x |
| pandas | DataFrame operations, CSV export | 2.1.4+ |
| openpyxl | Excel file generation | 3.1.2+ |
| PySide6 | GUI framework (Qt for Python) | 6.6+ |
| pyqtgraph | Embedded Gantt chart rendering | 0.13+ |
| pytest | Unit testing | 7.4.0+ |

## Key Design Patterns

- **Whitelist/Blacklist filtering**: Location validation uses prefix whitelist + substring blacklist (lines 38-53, 455-475)
- **Fallback chain**: Setup time extraction tries 3 sources in order (lines 300-335)
- **Worker thread**: GUI processing runs in a background thread with queue-based status updates
- **Regex-driven parsing**: All event data extraction uses compiled regex patterns against pdfplumber text output

## Technology Decisions

See [DECISIONS.md](DECISIONS.md) for rationale behind technology choices.
