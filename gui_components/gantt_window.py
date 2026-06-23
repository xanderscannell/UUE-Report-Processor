"""
Gantt Chart Window
==================
Embedded pyqtgraph Gantt chart of the event schedule.

Draws one horizontal bar per event (location on the Y axis, time of day on the
X axis), with a live red current-time indicator that refreshes every 60s.
"""

from datetime import datetime
from typing import Dict, List, Optional

import pyqtgraph as pg
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from .settings import GANTT

pg.setConfigOptions(antialias=True)


def _to_hours(hhmm: str) -> Optional[float]:
    """Convert a 24-hour 'HH:MM' string to fractional hours, or None."""
    try:
        h, m = hhmm.split(":")
        return int(h) + int(m) / 60.0
    except (ValueError, AttributeError):
        return None


class GanttWindow(QMainWindow):
    """Separate window showing the event schedule as a Gantt chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Event Schedule - Gantt Chart")
        self.resize(900, 600)

        self._datasets: Dict[str, List[dict]] = {}
        self._time_line: Optional[pg.InfiniteLine] = None

        self._build_ui()

        # Refresh the current-time indicator every 60s.
        self._timer = QTimer(self)
        self._timer.setInterval(GANTT["time_line_refresh_ms"])
        self._timer.timeout.connect(self._update_time_line)
        self._timer.start()

    # -- UI --------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QHBoxLayout()
        self.report_label = QLabel("Report:")
        top.addWidget(self.report_label)
        self.selector = QComboBox()
        self.selector.currentTextChanged.connect(self._render)
        top.addWidget(self.selector)
        top.addStretch()
        layout.addLayout(top)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.getAxis("left").setStyle(tickTextOffset=5)

        # Lock the view: no mouse pan/zoom (drag or wheel), no right-click menu,
        # no auto-range button.
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()

        layout.addWidget(self.plot)

        # Colors follow the system light/dark theme.
        self._fg = QColor("#000000")
        self._bg = QColor("#ffffff")
        self._apply_theme()

    # -- data ------------------------------------------------------------
    def set_datasets(self, datasets: Dict[str, List[dict]]):
        """Replace all chart datasets ({report label: gantt rows})."""
        self._datasets = dict(datasets)
        current = self.selector.currentText()
        self.selector.blockSignals(True)
        self.selector.clear()
        self.selector.addItems(self._datasets.keys())
        if current in self._datasets:
            self.selector.setCurrentText(current)
        self.selector.blockSignals(False)
        # The report selector is only useful with more than one report; for a
        # single report, hide the whole row and show its name in the title bar.
        multiple = len(self._datasets) > 1
        self.report_label.setVisible(multiple)
        self.selector.setVisible(multiple)
        self._render(self.selector.currentText())

    # -- rendering -------------------------------------------------------
    def _render(self, label: str):
        self.setWindowTitle(
            f"Event Schedule - {label}" if label else "Event Schedule - Gantt Chart"
        )
        self.plot.setTitle(
            self._format_date(label), color=self._fg.name(), size="13pt"
        )
        self.plot.clear()
        self._time_line = None

        rows = self._datasets.get(label)
        if not rows:
            return

        starts, ends, y0s, y1s, brushes, y_ticks = [], [], [], [], [], []
        bar_h = GANTT["bar_height"]
        palette = GANTT["palette"]

        idx = 0
        for row in rows:
            start = _to_hours(row.get("StartTime", ""))
            end = _to_hours(row.get("EndTime", ""))
            if start is None or end is None:
                continue
            if end < start:          # crosses midnight
                end += 24

            y0 = idx
            starts.append(start)
            ends.append(end)
            y0s.append(y0)
            y1s.append(y0 + bar_h)
            brushes.append(QColor(palette[idx % len(palette)]))
            y_ticks.append((y0 + bar_h / 2, row.get("Location", "")))
            idx += 1

        if idx == 0:
            return

        bars = pg.BarGraphItem(
            x0=starts, x1=ends, y0=y0s, y1=y1s,
            brushes=brushes, pen=pg.mkPen(self._fg, width=1),
        )
        self.plot.addItem(bars)

        # X axis: 6 AM .. midnight, hourly major ticks + half-hour minors.
        x_start, x_end = GANTT["x_start"], GANTT["x_end"]
        major = [(h, self._fmt_hour(h)) for h in range(x_start, x_end + 1)]
        minor = [(h + 0.5, "") for h in range(x_start, x_end)]
        self.plot.getAxis("bottom").setTicks([major, minor])
        self.plot.setXRange(x_start, x_end, padding=0.01)

        # Y axis: one labeled row per event, first event on top.
        self.plot.getAxis("left").setTicks([y_ticks])
        self.plot.setYRange(-0.3, idx - 1 + bar_h + 0.3, padding=0)
        self.plot.getViewBox().invertY(True)

        # Current-time indicator (red vertical line).
        self._time_line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(GANTT["time_line"], width=2),
        )
        self.plot.addItem(self._time_line)
        self._update_time_line()

    def _update_time_line(self):
        if self._time_line is None:
            return
        now = datetime.now()
        self._time_line.setPos(now.hour + now.minute / 60 + now.second / 3600)

    # -- theming ---------------------------------------------------------
    def _apply_theme(self):
        """Match the chart canvas, axes, and labels to the system palette."""
        app = QApplication.instance()
        pal = app.palette() if app is not None else self.palette()
        self._fg = pal.color(QPalette.Text)
        self._bg = pal.color(QPalette.Base)
        self.plot.setBackground(self._bg)
        for name in ("left", "bottom"):
            axis = self.plot.getAxis(name)
            axis.setPen(self._fg)
            axis.setTextPen(self._fg)
        self.plot.setLabel("bottom", "Time of Day", color=self._fg.name())
        self.plot.setLabel("left", "Events", color=self._fg.name())

    def changeEvent(self, event):
        # Re-theme (and redraw the colored elements) when the OS switches modes.
        if event.type() in (
            QEvent.Type.PaletteChange,
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.ThemeChange,
        ):
            self._apply_theme()
            self._render(self.selector.currentText())
        super().changeEvent(event)

    @staticmethod
    def _format_date(label: str) -> str:
        """Format an MM-DD-YY report label as e.g. 'Tuesday, Jun 23 2026'.

        Falls back to the raw label when it isn't a recognizable date (e.g. the
        processor used the PDF filename because no date was found).
        """
        try:
            return datetime.strptime(label, "%m-%d-%y").strftime("%A, %b %d %Y")
        except (ValueError, TypeError):
            return label or ""

    @staticmethod
    def _fmt_hour(h: int) -> str:
        if h == 12:
            return "12 PM"
        if h in (0, 24):
            return "12 AM"
        if h > 12:
            return f"{h - 12} PM"
        return f"{h} AM"
