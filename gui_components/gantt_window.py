"""
Gantt Chart Window
==================
Embedded pyqtgraph timeline of the day's events.

One horizontal bar per event — location on the Y axis, time of day on the X
axis — with a live current-time indicator.

Color encodes the **building** the event is in, which is a real, stable
category, rather than the row's position in the list. Buildings are discovered
from room-name prefixes and colored per the user's Building Colors setting (see
``building_config.py``); two prefixes given the same color collapse into one
legend entry, which is how "UC and RUC are the same building" is expressed.
Every bar is also directly labeled on the Y axis, so identity never rests on
color alone.
"""

from datetime import datetime
from typing import Dict, List, Optional

import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .building_config import BuildingColors, prefix_of
from .settings import GANTT
from .style import SPACE, active_dark, tokens
from .widgets import label as make_label

pg.setConfigOptions(antialias=True)


def _to_hours(hhmm: str) -> Optional[float]:
    """Convert a 24-hour 'HH:MM' string to fractional hours, or None."""
    try:
        h, m = hhmm.split(":")
        return int(h) + int(m) / 60.0
    except (ValueError, AttributeError):
        return None


def _fmt_clock(hours: float) -> str:
    """Format fractional hours as a 12-hour clock time, e.g. 13.5 -> '1:30 PM'."""
    hours = hours % 24
    h, m = int(hours), int(round((hours % 1) * 60))
    if m == 60:
        h, m = h + 1, 0
    suffix = "AM" if h < 12 else "PM"
    display = h % 12 or 12
    return f"{display}:{m:02d} {suffix}"


class LegendChip(QFrame):
    """A color swatch beside a building name."""

    def __init__(self, name: str, color: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        swatch = QFrame()
        swatch.setFixedSize(11, 11)
        swatch.setStyleSheet(f"background: {color}; border-radius: 3px; border: none;")
        row.addWidget(swatch)
        row.addWidget(make_label(name, "muted"))


class GanttWindow(QMainWindow):
    """Separate window showing the event schedule as a Gantt chart."""

    def __init__(self, parent=None, buildings: Optional[BuildingColors] = None):
        super().__init__(parent)
        self.setWindowTitle("Event Timeline")
        self.resize(1000, 640)
        self.setWindowIcon(parent.windowIcon() if parent else self.windowIcon())

        # Falling back to an empty map would silently paint every bar neutral
        # gray, so an unconfigured window uses the shipped assignments instead.
        self.buildings = buildings if buildings is not None else BuildingColors.defaults()
        self._datasets: Dict[str, List[dict]] = {}
        self._bars: List[dict] = []   # hover lookup: x0, x1, y0, y1, and row data
        self._time_line: Optional[pg.InfiniteLine] = None
        self._x_range = (GANTT["x_start"], GANTT["x_end"])

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
        layout.setContentsMargins(SPACE["lg"], SPACE["lg"], SPACE["lg"], SPACE["lg"])
        layout.setSpacing(SPACE["md"])

        top = QHBoxLayout()
        top.setSpacing(SPACE["md"])

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.title_label = make_label("Event Timeline", "title")
        self.date_label = make_label("", "subtitle")
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.date_label)
        top.addLayout(title_col)
        top.addStretch()

        self.report_label = make_label("Report", "muted")
        top.addWidget(self.report_label)
        self.selector = QComboBox()
        self.selector.currentTextChanged.connect(self._render)
        top.addWidget(self.selector)
        layout.addLayout(top)

        self.legend_row = QHBoxLayout()
        self.legend_row.setSpacing(SPACE["md"])
        self.legend_row.addStretch()
        layout.addLayout(self.legend_row)

        self.plot = pg.PlotWidget()
        # Reserve room for location names; pyqtgraph clips them otherwise.
        left = self.plot.getAxis("left")
        left.setStyle(tickTextOffset=8, tickLength=0)
        left.setWidth(GANTT["left_axis_width"])
        self.plot.getAxis("bottom").setStyle(tickTextOffset=8)

        # Lock the view: no mouse pan/zoom, no context menu, no auto-range button.
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.scene().sigMouseMoved.connect(self._on_hover)
        layout.addWidget(self.plot, stretch=1)

        self.empty_label = make_label(
            "No events to show for this report.", "subtitle"
        )
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

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

        # The report selector only earns its space with more than one report.
        multiple = len(self._datasets) > 1
        self.report_label.setVisible(multiple)
        self.selector.setVisible(multiple)
        self._render(self.selector.currentText())

    def refresh(self):
        """Redraw with the current building colors (after the setting changes)."""
        self._render(self.selector.currentText())

    def prefixes_in_data(self) -> List[str]:
        """Every building prefix appearing in the loaded reports."""
        return sorted(
            {
                prefix_of(row.get("Location", ""))
                for rows in self._datasets.values()
                for row in rows
                if prefix_of(row.get("Location", ""))
            }
        )

    # -- rendering -------------------------------------------------------
    def _render(self, report: str):
        t = tokens()
        self.setWindowTitle(f"Event Timeline — {report}" if report else "Event Timeline")
        self.date_label.setText(self._format_date(report))

        self.plot.clear()
        self._time_line = None
        self._bars = []
        self._clear_legend()

        rows = self._datasets.get(report)
        if not rows:
            self.plot.hide()
            self.empty_label.show()
            return
        self.plot.show()
        self.empty_label.hide()

        bar_h = GANTT["bar_height"]

        starts, ends, y0s, y1s, brushes, y_ticks = [], [], [], [], [], []
        seen_buildings = []

        idx = 0
        for row in rows:
            start = _to_hours(row.get("StartTime", ""))
            end = _to_hours(row.get("EndTime", ""))
            if start is None or end is None:
                continue
            if end < start:          # crosses midnight
                end += 24

            building = prefix_of(row.get("Location", ""))
            if building and building not in seen_buildings:
                seen_buildings.append(building)

            y0 = idx + (1 - bar_h) / 2
            starts.append(start)
            ends.append(end)
            y0s.append(y0)
            y1s.append(y0 + bar_h)
            brushes.append(QColor(self.buildings.color(building, self._dark)))
            y_ticks.append((idx + 0.5, row.get("Location", "")))
            self._bars.append(
                {"x0": start, "x1": end, "y0": y0, "y1": y0 + bar_h, "row": row}
            )
            idx += 1

        if idx == 0:
            self.plot.hide()
            self.empty_label.show()
            return

        self.plot.addItem(
            pg.BarGraphItem(
                x0=starts, x1=ends, y0=y0s, y1=y1s,
                brushes=brushes, pen=pg.mkPen(None),
            )
        )

        # X axis: clamp to the configured window but always include the data.
        x_start = min(GANTT["x_start"], int(min(starts)))
        x_end = max(GANTT["x_end"], int(max(ends)) + 1)
        self._x_range = (x_start, x_end)
        major = [(h, self._fmt_hour(h)) for h in range(x_start, x_end + 1, 2)]
        minor = [(h, "") for h in range(x_start, x_end + 1)]
        self.plot.getAxis("bottom").setTicks([major, minor])
        # A little slack on each side so the first and last hour labels are not
        # clipped by the plot edge.
        self.plot.setXRange(x_start - 0.35, x_end + 0.35, padding=0)

        # Y axis: one labeled row per event, first event on top.
        self.plot.getAxis("left").setTicks([y_ticks])
        self.plot.setYRange(0, idx, padding=0.01)
        self.plot.getViewBox().invertY(True)

        # Current-time indicator.
        self._time_line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(GANTT["time_line"], width=2, style=Qt.DashLine),
            label="now",
            labelOpts={
                "position": 0.02,
                "color": GANTT["time_line"],
                "movable": False,
                "fill": None,
            },
        )
        self.plot.addItem(self._time_line)
        self._update_time_line()

        self._build_legend(seen_buildings)

    def _update_time_line(self):
        if self._time_line is None:
            return
        now = datetime.now()
        hours = now.hour + now.minute / 60 + now.second / 3600

        # When the day runs past midnight, bars ending after 00:00 are drawn on
        # an extended axis (01:30 sits at x=25.5). The clock has to follow onto
        # that extension, or the marker lands back at x=1.5 and disappears off
        # the left edge during exactly the hours it matters most.
        x_start, x_end = self._x_range
        if x_end > 24 and hours < x_start:
            hours += 24

        self._time_line.setPos(hours)

    # -- legend ----------------------------------------------------------
    def _clear_legend(self):
        while self.legend_row.count() > 1:  # keep the trailing stretch
            item = self.legend_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _build_legend(self, buildings: List[str]):
        """
        Show a chip per distinct color present in this report.

        Buildings sharing a color share a chip, so two prefixes for the same
        physical building read as one entry.
        """
        entries = self.buildings.legend(buildings, self._dark)
        if len(entries) < 2:
            return
        for color, name in entries:
            chip = LegendChip(name, color)
            self.legend_row.insertWidget(self.legend_row.count() - 1, chip)

    # -- hover -----------------------------------------------------------
    def _on_hover(self, scene_pos):
        """Show a tooltip for the bar under the cursor."""
        vb = self.plot.getViewBox()
        if not self.plot.sceneBoundingRect().contains(scene_pos):
            QToolTip.hideText()
            return
        point = vb.mapSceneToView(scene_pos)
        x, y = point.x(), point.y()

        for bar in self._bars:
            if bar["x0"] <= x <= bar["x1"] and bar["y0"] <= y <= bar["y1"]:
                row = bar["row"]
                name = row.get("EventName")
                lines = [f"<b>{name}</b>"] if name else []
                lines.append(row.get("Location", ""))
                lines.append(f"{_fmt_clock(bar['x0'])} – {_fmt_clock(bar['x1'])}")
                QToolTip.showText(QCursor.pos(), "<br>".join(lines), self.plot)
                return
        QToolTip.hideText()

    # -- theming ---------------------------------------------------------
    def _apply_theme(self):
        """Match the chart surface, axes, and grid to the app theme."""
        self._dark = active_dark()
        t = tokens(self._dark)

        self.plot.setBackground(QColor(t["surface"]))
        # pyqtgraph draws the gridlines from the axis pen, tinted by the grid
        # alpha — so the pen has to be a mid-tone, not a hairline border color,
        # or the grid washes out entirely at any usable alpha.
        for name in ("left", "bottom"):
            axis = self.plot.getAxis(name)
            axis.setPen(pg.mkPen(t["text_faint"], width=1))
            axis.setTextPen(pg.mkPen(t["text_muted"]))

        # Set the grid per axis rather than via showGrid(), which forces one
        # alpha on both: the hour lines carry the reading, the row lines only
        # guide the eye from a label across to its bar.
        self.plot.getAxis("bottom").setGrid(int(GANTT["grid_alpha"] * 255))
        self.plot.getAxis("left").setGrid(int(GANTT["grid_alpha_y"] * 255))
        self.plot.setLabel("bottom", "Time of day", color=t["text_faint"])
        self.plot.setLabel("left", "")

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
    def _format_date(report: str) -> str:
        """Format an MM-DD-YY report label as e.g. 'Tuesday, Jun 23 2026'.

        Falls back to the raw label when it isn't a recognizable date (e.g. the
        processor used the PDF filename because no date was found).
        """
        try:
            return datetime.strptime(report, "%m-%d-%y").strftime("%A, %B %d, %Y")
        except (ValueError, TypeError):
            return report or ""

    @staticmethod
    def _fmt_hour(h: int) -> str:
        h = h % 24
        if h == 12:
            return "12 PM"
        if h == 0:
            return "12 AM"
        return f"{h - 12} PM" if h > 12 else f"{h} AM"
