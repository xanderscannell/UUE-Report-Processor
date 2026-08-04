# Project Conventions

## Language and Runtime

- **Language**: Python 3.7+ (uses 3.10+ type hint syntax)
- **Version**: Python 3.13 (installed on dev machine)
- **Package manager**: pip with venv

## Code Style

- **Formatter**: None configured (follow existing style)
- **Linter**: None configured
- **Type checker**: None configured (type hints used but not enforced)

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `SetupReportProcessor` |
| Functions | snake_case | `extract_text_from_pdf` |
| Constants | UPPER_SNAKE_CASE | `VALID_LOCATION_PREFIXES` |
| Private members | _leading_underscore | `_extract_setup_time` |
| Files | snake_case | `setup_report_processor.py` |
| Test files | test_ prefix | `test_setup_report_processor.py` |

## File Organization

```
./
  setup_report_processor.py   # Core processor (single file)
  gui_wrapper.py              # GUI entry point (MainWindow, stage machine)
  gui_components/
    __init__.py               # Public exports
    style.py                  # Design tokens + application stylesheet
    theme.py                  # OS color-scheme detection
    widgets.py                # Shared primitives (Card, HeaderBar, icons…)
    settings.py               # Behavioral defaults, dimensions, Gantt config
    drop_zone.py              # Drag-drop widget (hero + compact)
    file_list.py              # File queue widget
    result_panel.py           # Post-run summary screen
    keep_awake.py             # OS sleep/display inhibitor (Windows only)
    preferences.py            # Persisted user preferences (gui_preferences.json)
    log_handler.py            # Logging widget
    location_editor.py        # Whitelist editor dialog
    worker.py                 # Background QThread
    gantt_window.py           # Event timeline
  test_setup_report_processor.py  # All tests in one file
```

## Docstrings

- Google-style docstrings with Args, Returns, Raises, Example sections
- All public methods should have docstrings
- Example:
```python
def parse_time(self, time_str: str) -> Optional[datetime]:
    """
    Parse time string to datetime object for sorting.

    Args:
        time_str: Time string like "7:30 AM", "12:00 PM"

    Returns:
        datetime object or None if parsing fails
    """
```

## Error Handling

- Fail fast in `__init__` with `FileNotFoundError` / `ValueError`
- Try-except with logging in processing methods
- Graceful degradation for optional features and missing config (e.g. a missing
  `location_config.json` falls back to built-in defaults)
- Never silently swallow exceptions; always log at WARNING or ERROR level

## Logging

- Module-level logger: `logger = logging.getLogger(__name__)`
- Dual output: file (`setup_report_processor.log`) + console
- Levels: DEBUG for tracing, INFO for milestones, WARNING for skipped items
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Always log excluded events with event name and reason

## Testing

- **Framework**: pytest
- **Coverage target**: 85%+
- **Test naming**: `test_[method]_[scenario]` (e.g., `test_parse_standard_time_format`)
- **Test classes**: Group by feature (`TestTimeParser`, `TestLocationValidation`, etc.)
- **Run tests**: `python -m pytest test_setup_report_processor.py -v`
- **Fixtures**: Use pytest fixtures for processor instances with `tmp_path`

## Git Conventions

- **Commit style**: Imperative mood, sentence case (e.g., "Fixed 11 o'clock being read as 1 o'clock")
- **No conventional commits format enforced** — keep messages descriptive and clear

## Import Order

1. Standard library (`re`, `logging`, `argparse`, `pathlib`, `datetime`, `typing`)
2. Third-party packages (`pandas`, `pdfplumber`, `openpyxl`)
3. Local modules (`gui_components`)

## Constants and Configuration

- Location filters defined as class-level constants (not in external config)
- Regex patterns stored as class constants when reused
- GUI behavioral defaults in `gui_components/settings.py`

## GUI Styling

- **Never hard-code a color in a widget.** Read it from `style.tokens()` so both
  schemes stay in sync; add a new token if none fits.
- **Never call `is_dark_mode()` from a widget.** `tokens()` returns the scheme
  `apply_theme()` actually applied, which is what the widget must match.
- Prefer the shared stylesheet (an `objectName` or a `variant`/`role`/`card`
  dynamic property) over per-widget `setStyleSheet`, so theme switches take
  effect without touching each widget.
- Button variants: `primary` (maize, exactly one per screen), `secondary`
  (brand navy), `ghost`, `quiet`, `icon`, `toggle`.
- Typography roles on `QLabel`: `display`, `title`, `subtitle`, `muted`,
  `faint`, `eyebrow`, `metric` — use `widgets.label(text, role)`.
- Spacing comes from `style.SPACE`; corner radii from `style.RADIUS`.
