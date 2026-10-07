"""
Timeline Bar Labels
===================
Paints the event name, room, and time range directly onto the timeline bars.

The reference is a **run sheet** — the day-of-show schedule taped to a wall
backstage. The name of the thing goes on the block, the call times ride its
edge, the room sits underneath::

    +-----------------------------------------------+
    | Commencement Rehearsal          9:00-11:30 AM |
    | RUC 1171 (Lake Erie)                          |
    +-----------------------------------------------+

Text is laid out against each bar's measured **pixel** box, not its width in
hours, so it re-fits itself on every window resize. Rows are never shorter than
the name plus the room, so the room always has its own line. The time range
appears only when it fits beside the whole name; the name elides as the bar
narrows. A bar too narrow to show the room in full (or a readable stub of the
name) moves its label, both lines, into the whitespace beside it, the way a
short cue gets its label in a printed run sheet's margin.

The room is never dropped or elided inside a bar. The X axis already places an
event to within a few minutes, but since the Y axis became a date, nothing
outside the label says which room an event is in.

``pg.BarGraphItem`` cannot draw text at all, and a ``pg.TextItem`` per bar
cannot measure the bar it belongs to, so neither can elide. A ``GraphicsObject``
that paints in device pixels does both: the type keeps a fixed point size while
the bars scale with the view.
"""

import math

import pyqtgraph as pg
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QTransform
from PySide6.QtWidgets import QApplication

from .style import TYPE, ink_on

# Inset from the bar edge, gap between the name and the times, and the breathing
# room a label needs above and below itself. Pixels, deliberately — this is the
# one place in the app that measures in device space rather than layout units.
PAD_X = 7
PAD_Y = 3
GAP = 12

# Recessed text (room, times) keeps the ink but drops its weight on the page, so
# the event name stays the thing the eye lands on first.
SUB_ALPHA = 217          # 85%

# Roughly the shortest run of characters that still reads as a name rather than
# noise. A bar that cannot hold this much gives up and spills outside instead.
# Measured in average characters so it tracks whatever font the app resolved.
MIN_NAME_CHARS = 9


def _name_font() -> QFont:
    """The event-name face: the app font, one step down, at DemiBold."""
    font = QFont(QApplication.font())
    font.setPointSize(TYPE["small"])
    font.setWeight(QFont.Weight.DemiBold)
    return font


def _meta_font() -> QFont:
    """The supporting face for the room and the time range."""
    font = QFont(QApplication.font())
    font.setPointSize(TYPE["micro"])
    return font


def min_row_height(bar_height: float, floor: int) -> int:
    """
    The shortest row whose bar still holds the event name with the room below.

    Measured from the real font rather than assumed, so the chart stays readable
    at any display scaling. ``floor`` is the configured minimum, which wins when
    the font turns out not to need the room.
    """
    text_h = QFontMetrics(_name_font()).height() + QFontMetrics(_meta_font()).height()
    needed = (text_h + 2 * PAD_Y) / max(bar_height, 0.01)
    return max(floor, int(math.ceil(needed)))


class BarLabels(pg.GraphicsObject):
    """Draws every bar's label in one item, in device pixels."""

    def __init__(self, bars, muted_ink: str):
        super().__init__()
        self._bars = bars
        self._muted = QColor(muted_ink)

        self._font_name = _name_font()
        self._font_meta = _meta_font()
        self._fm_name = QFontMetrics(self._font_name)
        self._fm_meta = QFontMetrics(self._font_meta)
        self._floor_w = self._fm_name.averageCharWidth() * MIN_NAME_CHARS

    # -- geometry --------------------------------------------------------
    def boundingRect(self) -> QRectF:
        # Spilled labels reach outside their own bar, so the item claims the
        # whole visible plot rather than the union of the bars.
        vb = self.getViewBox()
        return QRectF() if vb is None else QRectF(vb.viewRect())

    def viewRangeChanged(self):
        self.prepareGeometryChange()

    def viewTransformChanged(self):
        self.prepareGeometryChange()

    # -- painting --------------------------------------------------------
    def paint(self, p, *args):
        vb = self.getViewBox()
        if vb is None or not self._bars:
            return

        tr = p.transform()                       # data units -> device pixels
        view_px = tr.mapRect(QRectF(vb.viewRect()))

        p.save()
        p.setTransform(QTransform())             # from here on, draw in pixels
        p.setClipRect(view_px)
        for bar in self._bars:
            rect = QRectF(
                tr.map(QPointF(bar["x0"], bar["y0"])),
                tr.map(QPointF(bar["x1"], bar["y1"])),
            ).normalized()                       # the Y axis is inverted
            if rect.bottom() < view_px.top() or rect.top() > view_px.bottom():
                continue                         # scrolled out of the window
            self._paint_bar(p, rect, bar, view_px)
        p.restore()

    def _paint_bar(self, p, rect: QRectF, bar: dict, view_px: QRectF):
        row = bar["row"]
        name = (row.get("EventName") or "").strip()
        location = (row.get("Location") or "").strip()
        times = bar.get("times", "")

        headline = name or location
        if not headline or rect.height() < self._fm_name.height():
            return

        # The room only earns a second line when it is not already the headline.
        sub = location if name else ""
        inner = rect.width() - 2 * PAD_X

        # The room is always shown whole: nothing else on the chart names it.
        # A bar too narrow for the room, or for a readable stub of the name,
        # hands the whole label to the whitespace beside it.
        room_w = (
            self._fm_meta.horizontalAdvance(sub) if sub
            else self._fm_name.horizontalAdvance(location) if location
            else 0
        )
        if inner < self._floor_w or room_w > inner:
            self._paint_spill(p, rect, headline, sub, view_px)
            return

        ink = QColor(ink_on(bar["color"]))
        sub_ink = QColor(ink)
        sub_ink.setAlpha(SUB_ALPHA)

        head_h = self._fm_name.height()
        sub_h = self._fm_meta.height() if sub else 0

        p.save()
        p.setClipRect(rect)

        head = QRectF(
            rect.left() + PAD_X,
            rect.top() + (rect.height() - head_h - sub_h) / 2,
            inner,
            head_h,
        )

        # The times ride the right edge of the headline row when they fit beside
        # the whole name; the name never gives up characters to make space.
        if times:
            times_w = self._fm_meta.horizontalAdvance(times)
            if self._fm_name.horizontalAdvance(headline) + GAP + times_w <= inner:
                p.setFont(self._font_meta)
                p.setPen(sub_ink)
                p.drawText(head, Qt.AlignRight | Qt.AlignVCenter, times)
                head.setWidth(inner - GAP - times_w)

        p.setFont(self._font_name)
        p.setPen(ink)
        p.drawText(
            head,
            Qt.AlignLeft | Qt.AlignVCenter,
            self._fm_name.elidedText(headline, Qt.ElideRight, int(head.width())),
        )

        if sub:
            below = QRectF(rect.left() + PAD_X, head.bottom(), inner, sub_h)
            p.setFont(self._font_meta)
            p.setPen(sub_ink)
            p.drawText(below, Qt.AlignLeft | Qt.AlignVCenter, sub)

        p.restore()

    def _paint_spill(self, p, rect: QRectF, headline: str, sub: str, view_px: QRectF):
        """
        Label a bar in the whitespace beside it, laid out as it would be inside:
        the name, and the room on the line below.

        Every event gets its own row, so the space next to a bar is always free.
        """
        right = view_px.right() - rect.right() - PAD_X
        left = rect.left() - view_px.left() - PAD_X
        if right >= left:
            x, width, align = rect.right() + PAD_X, right, Qt.AlignLeft
        else:
            x, width, align = view_px.left(), left, Qt.AlignRight
        if width < self._fm_name.horizontalAdvance("Ww"):
            return

        head_h = self._fm_name.height()
        sub_h = self._fm_meta.height() if sub else 0
        head = QRectF(x, rect.top() + (rect.height() - head_h - sub_h) / 2, width, head_h)

        p.setPen(self._muted)
        p.setFont(self._font_name)
        p.drawText(
            head,
            align | Qt.AlignVCenter,
            self._fm_name.elidedText(headline, Qt.ElideRight, int(width)),
        )
        if sub:
            p.setFont(self._font_meta)
            p.drawText(
                QRectF(x, head.bottom(), width, sub_h),
                align | Qt.AlignVCenter,
                self._fm_meta.elidedText(sub, Qt.ElideRight, int(width)),
            )
