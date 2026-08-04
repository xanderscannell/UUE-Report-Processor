# Checkpoint - 2026-08-05

## Session Summary

Overhauled the PySide6 frontend: the window is now staged (empty → workspace →
results) with an app-owned light/dark design system, a results screen replacing
the post-run alert, and one-time setup moved into a Settings menu. Building colors
for the timeline became user configuration rather than a hardcoded prefix map.
All 49 tests pass; every screen was rendered and reviewed in both themes, and the
run pipeline was verified end to end. Not yet done: on-display verification with a
real Daily Setup Report PDF, and the exe rebuild.

## Completed

- Design system in `gui_components/style.py` — color tokens, spacing/type scale,
  `build_stylesheet()`, `apply_theme()` (Fusion + app-owned palettes)
- Three-stage `QStackedWidget` window; per-file queue cards with live status
- `ResultPanel` summary screen; log demoted behind a badging "Details" disclosure
- Settings menu (whitelist, building colors, output folder, preferences, log,
  shortcut, about)
- Building Colors: discovery from room-name prefixes, validated palette slots,
  persistence in `location_config.json` under an additive `buildings` key
- Timeline: building colors + legend, hover tooltips, auto-widening time axis,
  fixed clipped Y labels, stronger gridlines
- Timeline-only ("dry") runs — untick both formats, nothing is written
- Docs: README, README_GUI (rewritten), QUICKSTART, SETUP (rewritten),
  ARCHITECTURE, CONVENTIONS, MASTER_PLAN, CURRENT_STATUS, ADR-005 and ADR-006

## Files Changed

| File | Change |
|------|--------|
| `gui_components/style.py` | New — design tokens, stylesheet, `apply_theme` |
| `gui_components/widgets.py` | New — Card, HeaderBar, CollapsibleSection, painted icons |
| `gui_components/result_panel.py` | New — post-run summary screen |
| `gui_components/building_config.py` | New — building prefix → label + palette slot |
| `gui_components/building_editor.py` | New — Building Colors dialog |
| `gui_wrapper.py` | Rewritten — stage machine, Settings menu, window-wide drop |
| `gui_components/gantt_window.py` | Building colors, legend, tooltips, grid, axis fixes |
| `gui_components/file_list.py` | Rewritten as status-bearing file cards |
| `gui_components/drop_zone.py` | Hero + compact variants, reject feedback |
| `gui_components/location_editor.py` | Checkboxes, filter box, dimmed disabled rows |
| `gui_components/worker.py` | Per-file signals, run summary, dry-run handling |
| `gui_components/log_handler.py` | Warning/error counters for the Details badge |
| `gui_components/settings.py` | Behavioral defaults only; colors moved out |
| `setup_report_processor.py` | `create_gantt_rows()` also emits `EventName` |

## Issues and Solutions

| Issue | Solution |
|-------|----------|
| Half the UI painted from the wrong palette on a forced light/dark run | `apply_theme()` now owns the active scheme; widgets read `style.tokens()`, never `is_dark_mode()` |
| UC and RUC were colored as two buildings — they are one (renamed) | Same-color-means-same-building, shipped as a default; no alias concept |
| Gridlines invisible at any alpha | They derive from the axis pen; it was set to the palest border token, then multiplied by 0.18 |
| Timeline Y-axis location labels missing entirely | pyqtgraph clipped them; set an explicit `left_axis_width` |
| "Now" marker vanished during late-night runs | On a midnight-crossing chart the clock has to move onto the extended axis (`hours += 24`) |
| Progress bar never advanced for skipped/failed files | `progress.emit` moved out of the success branch |
| `GanttWindow` built without a color map painted every bar gray | Defaults to `BuildingColors.defaults()` |
| Two diagnostics gave false negatives on gridlines | `show()` fires a palette event that re-runs `_apply_theme`, overwriting any external `setGrid` call; drove the test through `GANTT` instead |

## Decisions Made

- Staged single-page GUI with an app-owned theme (ADR-005)
- Building colors discovered and user-configured, not hardcoded (ADR-006);
  deterministic palette slots rather than random hex, so colorblind separation
  and light/dark stepping survive
- Timeline is never a selectable "output"; unticking both formats is a
  timeline-only run that writes nothing

## Next Session Should

1. Run `python gui_wrapper.py` against a real Daily Setup Report PDF — confirm
   crispness on a scaled display, and check the timeline in light and dark
2. Rebuild the portable exe and smoke-test it:
   `pyinstaller --windowed --name SetupReportProcessor --icon=UUE.ico gui_wrapper.py`
3. Copy `location_config.json` into `dist/SetupReportProcessor/`, then zip
4. Consider regression tests for the GUI-side logic that now carries real
   behavior (`BuildingColors` assignment/persistence, dry-run gating) — the
   49 existing tests cover only the processor

## Open Questions

- Building colors are restricted to 8 validated palette slots plus gray. If an
  arbitrary color picker is ever wanted, it means giving up the automatic
  light/dark stepping and the colorblind guarantees.
- Only the first 3 slots stay mutually distinguishable under every colorblind
  simulation at once. With 4+ buildings on one chart, color alone is not
  sufficient — the per-bar location labels carry it. Revisit if the venue list
  grows well past three buildings.
