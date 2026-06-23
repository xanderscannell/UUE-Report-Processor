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
