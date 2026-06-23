"""
GUI Configuration Settings
===========================
Default settings for the Setup Report Processor GUI (PySide6).
"""

from pathlib import Path

# Default configuration
GUI_DEFAULTS = {
    "window_title": "Setup Report Processor",
    "window_width": 820,
    "window_height": 900,
    "output_dir": Path("./output"),
    "excel_enabled": True,
    "csv_enabled": False,
    "gantt_autolaunch": False,
    "verbose_logging": False,
    "max_log_lines": 1000,
}

# Gantt chart configuration (canvas/axis colors follow the system palette)
GANTT = {
    "x_start": 6,    # earliest hour shown on the chart (6 AM)
    "x_end": 24,     # latest hour shown (midnight)
    "bar_height": 0.8,
    "time_line": "#d32f2f",            # current-time indicator (red)
    "time_line_refresh_ms": 60_000,    # redraw the indicator every 60s
    # Qualitative palette cycled across event bars
    "palette": [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ],
}

# UI Dimensions
DIMENSIONS = {
    "drop_zone_height": 130,
}
