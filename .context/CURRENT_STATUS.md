# Project Status

**Last updated**: 2026-02-04

## Current Position

**Phase**: Maintenance & Bug Fixes
**Subphase**: PDF parsing edge cases
**Progress**: Core features 100% complete, ongoing bug fixes

## Recently Completed

- Fixed 11:XX AM times being parsed as 1:XX AM (regex lookahead split bug in `extract_events`)
- Added "Special Notice" to location blacklist
- Added CDS prevention context framework
- Fixed "no setup time defined" event handling
- Added special notice to the blacklist

## In Progress

- [ ] Context framework initialization (this session)

## Next Up

1. Verify fix works across all existing input PDFs
2. Address any additional PDF parsing edge cases as they arise
3. Consider adding config file support for location filters

## Active Files and Modules

```
setup_report_processor.py    [status: stable, active bug fixes]
gui_wrapper.py               [status: stable]
gui_components/              [status: stable]
test_setup_report_processor.py [status: stable, may need new test cases]
```

## Recent Decisions

- **2026-02-04**: Added negative lookbehind `(?<!\d)` to block-splitting regex to prevent 11:XX time truncation (see DECISIONS.md #ADR-003)
- **2026-02-04**: Added "Special" and "Notice" as separate blacklist entries for case-insensitive substring matching

## Open Questions

- **Q**: Should location filters be moved to an external config file (YAML/JSON)?
  - Leaning toward: Yes, for easier customization without code changes
  - Blocked by: Not a priority yet

## Notes for Claude

- The PDF format has times appearing TWICE per line: `11:30 AM Setup Starts: 11:00 AM Event Name...` — the first time is "Setup Ready By", the second is the actual "Setup Starts" time
- pdfplumber text extraction can produce unexpected layouts; always test regex changes against real PDFs in `input/`
- The `_is_valid_location()` method uses case-insensitive substring matching for blacklist and prefix matching for whitelist
- Output files go to both `./output/` (via GUI) and `./` (via CLI) depending on entry point
