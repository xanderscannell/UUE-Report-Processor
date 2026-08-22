"""
Gantt Chart Window
==================
Embedded pyqtgraph timeline of the day's events.

One horizontal bar per event — the **date** on the Y axis, time of day on the X
axis — with a live current-time indicator.

Every loaded day is stacked into one chart, separated by a rule and labeled with
its own date, all sharing a single time-of-day axis. The selector filters down to
one day when a weekend gets too busy to read at once. The database exports one
day per file, so a weekend arrives as several files; they are keyed by the date
their rows carry, not by the file they came from, so a single export holding two
sheets lands as two blocks just the same.

Each bar carries its own label — event name, room, and time range, laid out
against the bar's pixel width so it re-fits on every resize and steps outside
the bar when the event is too short to hold text. Hovering still shows the full
card for whatever the pixels could not fit.

The Y axis names the day rather than the room, because the room is now printed
on the bar itself. That leaves the axis free to stack more than one day, which
is the shape a multi-day timeline needs; today there is exactly one block.

Color encodes the **building** the event is in, which is a real, stable
category, rather than the row's position in the list. Buildings are discovered
from room-name prefixes and colored per the user's Building Colors setting (see
``building_config.py``); two prefixes given the same color collapse into one
legend entry, which is how "UC and RUC are the same building" is expressed.
Every bar also carries its room as text, so identity never rests on color alone.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pyqtgraph as pg
from PySide6.QtCore import QEvent, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollBar,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .building_config import BuildingColors, prefix_of
from .gantt_labels import BarLabels, min_row_height
from .settings import GANTT
from .style import SPACE, active_dark, tokens
from .widgets import label as make_label

pg.setConfigOptions(antialias=True)

# Selector entry that stacks every loaded day rather than filtering to one.
ALL_DAYS = "__all__"

# The hover card is the fallback for whatever a bar was too small to print, so
# it has to stay put for as long as the cursor is on the bar. Qt's own expire
# timer pulls it after about three seconds; hiding is driven by _on_hover and
# the Leave handler instead, so this only has to outlast any plausible hover.
TOOLTIP_HOLD_MS = 24 * 60 * 60 * 1000


def _to_hours(hhmm: str) -> Optional[float]:
    """Convert a 24-hour 'HH:MM' string to fractional hours, or None."""
    try:
        h, m = hhmm.split(":")
        return int(h) + int(m) / 60.0
    except (ValueError, AttributeError):
        return None


def day_sort_key(key: str):
    """
    Order day keys chronologically, with undated ones last.

    A key is normally ``MM-DD-YY``, but a report whose date could not be read
    falls back to the source filename — those sort to the end, alphabetically,
    rather than being dropped or pretending to be a date.
    """
    try:
        return (0, datetime.strptime(key, "%m-%d-%y"), "")
    except (ValueError, TypeError):
        return (1, datetime.min, str(key))


def group_rows_by_day(rows: List[dict], fallback: str = "") -> Dict[str, List[dict]]:
    """
    Split gantt rows into ``{day key: rows}``, keeping each day's own order.

    Rows carry the date they fall on (see ``create_gantt_rows``), which is what
    lets one file holding several days become several blocks. Rows from a source
    that could not date itself fall back to the report label.
    """
    days: Dict[str, List[dict]] = {}
    for row in rows:
        days.setdefault(row.get("Date") or fallback, []).append(row)
    return days


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
        # Shared by the hover lookup and the label painter: x0, x1, y0, y1,
        # the row data, the resolved fill, and the formatted time range.
        self._bars: List[dict] = []
        self._time_line = None          # bounded to today's block, when loaded
        self._x_range = (GANTT["x_start"], GANTT["x_end"])
        self._row_count = 0
        self._visible_rows = 0
        # (label, first row, last row) per day block, for the Y axis.
        self._date_groups: List[tuple] = []
        # {day key: (first row, last row)}, so the clock can find today's block.
        self._day_bounds: Dict[str, tuple] = {}
        self._windowing = False   # re-entrancy guard for _update_y_window
        # The day the user actually picked, as opposed to whatever happened to
        # be showing. Only a real choice survives new data arriving.
        self._chosen_day: Optional[str] = None

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

        self.report_label = make_label("Day", "muted")
        top.addWidget(self.report_label)
        self.selector = QComboBox()
        # The visible text is a friendly date while the item's data stays the
        # raw day key, so the two never have to agree on one string.
        self.selector.currentIndexChanged.connect(self._on_day_selected)
        top.addWidget(self.selector)
        layout.addLayout(top)

        self.legend_row = QHBoxLayout()
        self.legend_row.setSpacing(SPACE["md"])
        self.legend_row.addStretch()
        layout.addLayout(self.legend_row)

        self.plot = pg.PlotWidget()
        # Reserve room for the date label; pyqtgraph clips it otherwise.
        left = self.plot.getAxis("left")
        # tickLength=0 still paints a zero-length stub beside each label, and a
        # tick means nothing on an axis whose labels name whole blocks of rows.
        left.setStyle(tickTextOffset=8, tickLength=0, tickAlpha=0)
        left.setWidth(GANTT["left_axis_width"])
        self.plot.getAxis("bottom").setStyle(tickTextOffset=8)

        # Lock the view: no mouse pan/zoom, no context menu, no auto-range button.
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.scene().sigMouseMoved.connect(self._on_hover)
        self.plot.getViewBox().sigResized.connect(self._update_y_window)

        # A day with more events than fit at a readable row height scrolls,
        # rather than compressing every row into an unlabelable sliver.
        self.vscroll = QScrollBar(Qt.Vertical)
        self.vscroll.hide()
        self.vscroll.valueChanged.connect(self._update_y_window)
        self.plot.viewport().installEventFilter(self)

        plot_row = QHBoxLayout()
        plot_row.setSpacing(SPACE["xs"])
        plot_row.addWidget(self.plot, stretch=1)
        plot_row.addWidget(self.vscroll)
        layout.addLayout(plot_row, stretch=1)

        self.empty_label = make_label(
            "No events to show for this report.", "subtitle"
        )
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self._apply_theme()

    # -- data ------------------------------------------------------------
    def set_datasets(self, datasets: Dict[str, List[dict]]):
        """Replace all chart datasets ({day key: gantt rows})."""
        self._datasets = dict(datasets)
        keys = sorted(self._datasets, key=day_sort_key)
        self.selector.blockSignals(True)
        self.selector.clear()
        if len(keys) > 1:
            # First, and the default: a weekend is more useful whole.
            self.selector.addItem("All days", ALL_DAYS)
        for key in keys:
            self.selector.addItem(self._axis_date(key), key)
        # Falling back to index 0 means a second day arriving mid-run opens the
        # weekend rather than leaving you on day one — but only when the day on
        # screen was a default rather than something the user asked for.
        restored = self.selector.findData(self._chosen_day)
        self.selector.setCurrentIndex(restored if restored >= 0 else 0)
        self.selector.blockSignals(False)

        # The day filter only earns its space with more than one day.
        multiple = len(keys) > 1
        self.report_label.setVisible(multiple)
        self.selector.setVisible(multiple)
        self._render()

    def _on_day_selected(self, _index: int):
        # Repopulating blocks this signal, so reaching here means the user
        # picked a day themselves.
        self._chosen_day = self.selector.currentData()
        self._render()

    def refresh(self):
        """Redraw with the current building colors (after the setting changes)."""
        self._render()

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
    def _days_for(self, key: Optional[str]) -> List[tuple]:
        """The (day key, rows) blocks to draw, oldest first."""
        keys = sorted(self._datasets, key=day_sort_key)
        if key and key != ALL_DAYS:
            keys = [k for k in keys if k == key]
        return [(k, self._datasets[k]) for k in keys if self._datasets.get(k)]

    def _render(self, key: Optional[str] = None):
        t = tokens()
        if key is None:
            key = self.selector.currentData()

        self.plot.clear()
        self._time_line = None
        self._bars = []
        self._row_count = 0
        self._date_groups = []
        self._day_bounds = {}
        self.vscroll.hide()
        self._clear_legend()

        days = self._days_for(key)
        self._set_heading(days)
        if not days:
            self.plot.hide()
            self.empty_label.show()
            return
        self.plot.show()
        self.empty_label.hide()

        bar_h = GANTT["bar_height"]

        starts, ends, y0s, y1s, brushes = [], [], [], [], []
        seen_buildings = []
        boundaries = []

        idx = 0
        for day_key, rows in days:
            block_start = idx
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
                fill = self.buildings.color(building, self._dark)
                brushes.append(QColor(fill))
                self._bars.append(
                    {
                        "x0": start, "x1": end, "y0": y0, "y1": y0 + bar_h,
                        "row": row,
                        "color": fill,        # the label picks its ink from this
                        # Formatted once, so the bar and the tooltip can never
                        # disagree about a time.
                        "times": f"{_fmt_clock(start)} – {_fmt_clock(end)}",
                    }
                )
                idx += 1

            # A day whose every row failed to parse gets no block at all, rather
            # than a labeled band with nothing in it.
            if idx > block_start:
                self._date_groups.append((self._axis_date(day_key), block_start, idx))
                self._day_bounds[day_key] = (block_start, idx)
                boundaries.append(idx)

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

        # Name, room, and times painted onto the bars themselves, so the chart
        # reads without a mouse. Hover still covers what the pixels cannot.
        labels = BarLabels(self._bars, t["text_muted"])
        labels.setZValue(10)
        self.plot.addItem(labels)

        # One rule between days. The last boundary is the bottom of the chart,
        # which the plot border already draws.
        for edge in boundaries[:-1]:
            self.plot.addItem(pg.InfiniteLine(
                pos=edge, angle=0, movable=False,
                pen=pg.mkPen(t["border_strong"], width=1),
            ))

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

        # Y axis: oldest day on top, each block labeled with its own date.
        self.plot.getViewBox().invertY(True)
        self._row_count = idx
        self.vscroll.setValue(0)
        self._update_y_window()

        # Current-time indicator, drawn only across today's block — run full
        # height it would claim to be "now" on every day stacked below.
        # No "now" caption: every row carries text, so the label had nowhere
        # left to sit without covering an event. Against an hour-labeled axis a
        # red dashed rule already reads as the current time.
        self._time_line = pg.PlotCurveItem(
            pen=pg.mkPen(GANTT["time_line"], width=2, style=Qt.DashLine),
        )
        self._time_line.setZValue(11)
        self.plot.addItem(self._time_line)
        self._update_time_line()

        self._build_legend(seen_buildings)

    def _set_heading(self, days: List[tuple]) -> None:
        """Name the window and its subtitle for the day, or the range of days."""
        if not days:
            self.setWindowTitle("Event Timeline")
            self.date_label.setText("")
            return
        if len(days) == 1:
            title = self._axis_date(days[0][0])
            subtitle = self._format_date(days[0][0])
        else:
            title = f"{self._axis_date(days[0][0])} – {self._axis_date(days[-1][0])}"
            subtitle = f"{title} · {len(days)} days"
        self.setWindowTitle(f"Event Timeline — {title}")
        self.date_label.setText(subtitle)

    def _update_y_window(self, *_):
        """
        Show as many rows as stay readable, and scroll for the rest.

        The Y range used to be split across however many events there were, so a
        busy day left every bar a few pixels tall — too short to label at all.
        The floor comes from the label font itself (``min_row_height``), so it
        holds at any display scaling. A day that fits behaves exactly as before
        and the scrollbar stays hidden.
        """
        if self._windowing or self._row_count <= 0:
            return
        self._windowing = True
        try:
            height = self.plot.getViewBox().height()
            min_row = min_row_height(GANTT["bar_height"], GANTT["min_row_px"])
            # Before the first layout the viewbox has no height yet; showing
            # every row is the right guess until sigResized corrects it.
            fits = int(height // min_row) if height > 0 else self._row_count
            self._visible_rows = max(1, min(fits, self._row_count))

            scrolls = self._row_count > self._visible_rows
            self.vscroll.setVisible(scrolls)
            self.vscroll.setRange(0, self._row_count - self._visible_rows)
            self.vscroll.setPageStep(self._visible_rows)
            self.vscroll.setSingleStep(1)

            # No padding: the window has to hold whole rows, or a sliver of the
            # next event peeks in under the last one.
            top = self.vscroll.value() if scrolls else 0
            self.plot.setYRange(top, top + self._visible_rows, padding=0)
            self._place_date_ticks(top, top + self._visible_rows)
        finally:
            self._windowing = False

    def _place_date_ticks(self, top: int, bottom: int):
        """
        Label the Y axis with the day each block of rows belongs to.

        A label is pinned to the middle of the *visible* part of its block, not
        to the block's true center, so scrolling through a long day never
        scrolls that day's own label off the chart. With more than one day
        loaded, each block keeps its own label and they separate as you scroll.
        """
        major = []
        for label, first, last in self._date_groups:
            if not label or last <= top or first >= bottom:
                continue                    # this day is scrolled out of view
            major.append(((max(first, top) + min(last, bottom)) / 2, label))

        # One tick per day and nothing else. Per-row ticks were left over from
        # the location axis, where a line was what carried the eye from a room
        # name across to its bar; with the rooms on the bars there is nothing
        # for them to connect, and the only horizontal rules worth drawing are
        # the ones between days (see _render).
        self.plot.getAxis("left").setTicks([major])

    def eventFilter(self, obj, event):
        # A cursor can leave the plot without a final move event landing off a
        # bar, which would strand the held card with nothing left to hide it.
        if event.type() == QEvent.Type.Leave:
            QToolTip.hideText()

        # Pan and zoom are off, which leaves the wheel free to scroll the rows.
        if event.type() == QEvent.Type.Wheel and self.vscroll.isVisible():
            notches = event.angleDelta().y() / 120.0
            self.vscroll.setValue(self.vscroll.value() - int(round(notches * 3)))
            return True
        return super().eventFilter(obj, event)

    def _place_clock(self):
        """
        Which block the current-time marker belongs on, and where along the axis.

        Two things decide it. The marker only crosses the day it actually
        belongs to — run full height it would claim to be "now" on every day
        stacked below. And between midnight and the start of the axis you are
        working the tail of *yesterday's* schedule, which is drawn on the
        extension past 24:00 (01:30 sits at x=25.5), not in the small hours of
        today's own block, which the axis does not show at all.

        Returns:
            ``(block bounds, x position)``, bounds being None when no loaded
            day is the one currently running.
        """
        now = datetime.now()
        hours = now.hour + now.minute / 60 + now.second / 3600
        x_start, x_end = self._x_range

        if hours < x_start and x_end > 24:
            yesterday = (now - timedelta(days=1)).strftime("%m-%d-%y")
            span = self._day_bounds.get(yesterday)
            if span:
                return span, hours + 24

        return self._day_bounds.get(now.strftime("%m-%d-%y")), hours

    def _update_time_line(self):
        if self._time_line is None:
            return
        span, hours = self._place_clock()
        if span is None:
            self._time_line.setData([], [])      # no loaded day is today
            return
        first, last = span
        self._time_line.setData([hours, hours], [first, last])

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
        """
        Show the hover card for the bar under the cursor, and hold it there.

        The card follows the cursor, and stays until it leaves the bar: either a
        move that lands elsewhere, handled here, or a move out of the widget
        entirely, handled by the Leave case in ``eventFilter``.
        """
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
                lines.append(bar["times"])
                # Anchored to the event's own position rather than to
                # QCursor.pos(), so the card cannot drift from the bar it
                # describes if the events ever lag the pointer.
                local = self.plot.mapFromScene(scene_pos)

                # Qt treats a repeat showText with unchanged text as a no-op, so
                # the card would otherwise sit wherever it first appeared. A
                # one-pixel rect at the cursor makes Qt's own tipChanged() true
                # on the very next move, which is what repositions it — and Qt's
                # placement keeps it clear of the screen edges for free. Leaving
                # is still our job, not this rect's: the misses below and the
                # Leave case in eventFilter do the hiding.
                QToolTip.showText(
                    self.plot.viewport().mapToGlobal(local),
                    "<br>".join(lines), self.plot,
                    QRect(local, QSize(1, 1)),
                    TOOLTIP_HOLD_MS,
                )
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

        # Only the hour lines are drawn from the axis; they carry the reading.
        # The Y axis draws no grid at all, or every date label would trail a
        # rule across the chart from a tick that means nothing on its own.
        self.plot.getAxis("bottom").setGrid(int(GANTT["grid_alpha"] * 255))
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
            self._render()
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
    def _axis_date(report: str) -> str:
        """
        Compact date for the Y axis, e.g. 'Tue, Jun 23'.

        Falls back to the raw report label, same as the header does, when it is
        not a recognizable date.
        """
        try:
            day = datetime.strptime(report, "%m-%d-%y")
        except (ValueError, TypeError):
            return report or ""
        return f"{day:%a, %b} {day.day}"

    @staticmethod
    def _fmt_hour(h: int) -> str:
        h = h % 24
        if h == 12:
            return "12 PM"
        if h == 0:
            return "12 AM"
        return f"{h - 12} PM" if h > 12 else f"{h} AM"
