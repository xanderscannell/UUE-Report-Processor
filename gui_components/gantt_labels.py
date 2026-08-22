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
hours, so it re-fits itself on every window resize and steps down a ladder as
the space runs out: all three fields, then the name with whichever single field
fits beside it, then the name alone elided, and finally — for a fifteen-minute
event that can never hold text — the label spills into the whitespace beside
the bar, the way a short cue gets its label in a printed run sheet's margin.
Without that last rung only the long events would ever be labeled.

The room outranks the time range whenever only one of them fits. The X axis
already places an event to within a few minutes, but since the Y axis became a
date, nothing outside the bar says which room an event is in.

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
    The shortest row that still leaves a legible label inside its bar.

    Measured from the real font rather than assumed, so the chart stays readable
    at any display scaling. ``floor`` is the configured minimum, which wins when
    the font turns out not to need the room.
    """
    needed = (QFontMetrics(_name_font()).height() + 2 * PAD_Y) / max(bar_height, 0.01)
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

        # Outside the bar there is no second line to put the room on, and the Y
        # axis no longer carries it either, so it rides along with the name.
        spilled = " · ".join(part for part in (name, location) if part)

        inner = rect.width() - 2 * PAD_X
        head_w = self._fm_name.horizontalAdvance(headline)

        # Inside the bar is where a label belongs, and an elided name still
        # identifies its event. Only a bar with no usable inside — a fifteen
        # minute event is a dozen pixels wide — hands its name to the whitespace
        # beside it.
        if inner < self._floor_w:
            self._paint_spill(p, rect, spilled, view_px)
            return

        ink = QColor(ink_on(bar["color"]))
        sub_ink = QColor(ink)
        sub_ink.setAlpha(SUB_ALPHA)

        # The room only earns a second line when it is not already the headline.
        # An elided room reads as a bug when the whole string is sitting on the
        # axis a few inches to the left, so the second line is all or nothing.
        sub = location if name and location else ""
        head_h = self._fm_name.height()
        sub_h = self._fm_meta.height()
        two_line = (
            bool(sub)
            and rect.height() >= head_h + sub_h
            and self._fm_meta.horizontalAdvance(sub) <= inner
        )

        p.save()
        p.setClipRect(rect)

        block_h = head_h + (sub_h if two_line else 0)
        head = QRectF(
            rect.left() + PAD_X,
            rect.top() + (rect.height() - block_h) / 2,
            inner,
            head_h,
        )

        # One field rides the right edge of the headline row. On two lines the
        # room already has its own line, so the times go here; on one line the
        # room takes the slot and the times give way, because the X axis already
        # places the event and nothing else names the room. Either way the name
        # never gives up characters to make space.
        for trailer in ([times] if two_line else [sub, times]):
            if not trailer:
                continue
            trailer_w = self._fm_meta.horizontalAdvance(trailer)
            if head_w + GAP + trailer_w <= inner:
                p.setFont(self._font_meta)
                p.setPen(sub_ink)
                p.drawText(head, Qt.AlignRight | Qt.AlignVCenter, trailer)
                head.setWidth(inner - GAP - trailer_w)
                break

        p.setFont(self._font_name)
        p.setPen(ink)
        p.drawText(
            head,
            Qt.AlignLeft | Qt.AlignVCenter,
            self._fm_name.elidedText(headline, Qt.ElideRight, int(head.width())),
        )

        if two_line:
            below = QRectF(rect.left() + PAD_X, head.bottom(), inner, sub_h)
            p.setFont(self._font_meta)
            p.setPen(sub_ink)
            p.drawText(below, Qt.AlignLeft | Qt.AlignVCenter, sub)

        p.restore()

    def _paint_spill(self, p, rect: QRectF, text: str, view_px: QRectF) -> bool:
        """
        Label a bar in the whitespace beside it. Returns False when even that is
        too tight, leaving the caller to decide what to do instead.

        Every event gets its own row, so the space next to a bar is always free.
        """
        right = view_px.right() - rect.right() - PAD_X
        left = rect.left() - view_px.left() - PAD_X
        if right >= left:
            box = QRectF(rect.right() + PAD_X, rect.top(), right, rect.height())
            align = Qt.AlignLeft
        else:
            box = QRectF(view_px.left(), rect.top(), left, rect.height())
            align = Qt.AlignRight
        if box.width() < self._fm_name.horizontalAdvance("Ww"):
            return False

        p.setFont(self._font_name)
        p.setPen(self._muted)
        p.drawText(
            box,
            align | Qt.AlignVCenter,
            self._fm_name.elidedText(text, Qt.ElideRight, int(box.width())),
        )
        return True
