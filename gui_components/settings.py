"""
GUI Configuration Settings
===========================
Default settings for the Setup Report Processor GUI (PySide6).

Visual design tokens (color, spacing, type) live in ``style.py``; this module
holds behavioral defaults and chart configuration.
"""

from pathlib import Path

# Default configuration
GUI_DEFAULTS = {
    "window_title": "Setup Report Processor",
    "window_subtitle": "Setup Report PDFs and Excel exports → sorted schedules",
    "window_width": 900,
    "window_height": 780,
    "window_min_width": 720,
    "window_min_height": 620,
    "output_dir": Path("./output"),
    "excel_enabled": True,
    "csv_enabled": False,
    "gantt_autolaunch": False,
    "verbose_logging": False,
    "keep_awake": False,
    "max_log_lines": 1000,
}

# Gantt chart configuration.
#
# Bars are colored by building — a real, stable category — not by row index.
# Buildings are discovered from room-name prefixes and their colors live in the
# user's config (see `building_config.py` / the Building Colors dialog), not
# here, so a new campus building needs no code change.
GANTT = {
    "x_start": 6,    # earliest hour normally shown (6 AM); widened to fit data
    "x_end": 24,     # latest hour normally shown (midnight)
    "bar_height": 0.62,                # leaves a clear gap between adjacent rows
    "left_axis_width": 190,            # room for location names on the Y axis
    "grid_alpha": 0.5,                 # hour gridlines, tinting the axis pen
    "grid_alpha_y": 0.22,              # row gridlines — secondary, so fainter
    "time_line": "#d03b3b",            # current-time indicator
    "time_line_refresh_ms": 60_000,    # redraw the indicator every 60s
}

# UI Dimensions
DIMENSIONS = {
    "drop_zone_height": 210,           # hero drop target (empty state)
    "drop_zone_max_height": 320,       # keeps the hero from swallowing the page
    "drop_zone_compact_height": 56,    # "add more" strip (workspace)
    "log_height": 190,
    "content_max_width": 720,
}
