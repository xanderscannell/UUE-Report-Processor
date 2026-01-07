"""
GUI Configuration Settings
===========================
Default settings and color scheme for the Setup Report Processor GUI.
"""

from pathlib import Path

# Default configuration
GUI_DEFAULTS = {
    "window_size": "800x900",
    "window_title": "Setup Report Processor",
    "output_dir": Path("./output"),
    "excel_enabled": True,
    "csv_enabled": False,
    "matlab_csv_enabled": False,
    "matlab_autolaunch": False,
    "verbose_logging": False,
    "max_log_lines": 1000,
    "poll_interval_ms": 100,  # How often to check processing queue
}

# Color scheme
COLORS = {
    "drop_zone_normal": "#e0e0e0",
    "drop_zone_hover": "#90caf9",
    "drop_zone_border": "#757575",
    "success": "#4caf50",
    "error": "#f44336",
    "warning": "#ff9800",
    "info": "#2196f3",
}

# UI Dimensions
DIMENSIONS = {
    "drop_zone_height": 150,
    "drop_zone_width": 600,
    "file_list_height": 150,
    "status_log_height": 250,
    "button_width": 15,
}

# File paths for persistence
CONFIG_FILE = Path.home() / ".setup_report_processor_gui.json"
