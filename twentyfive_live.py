#!/usr/bin/env python3
"""
25Live Reader
=============
Pulls one day's room bookings straight from UM-Dearborn's 25Live and produces
the same event records the PDF and Excel readers do, so everything downstream
(location filtering, schedule rows, sorting, output, and the Gantt feed) is
shared.

The data comes from the public guest view that
``25live.collegenet.com/pro/umdearborn`` shows visitors who are not signed in,
so no login or API key is needed. It is not an official API and could change
without notice, which is why the PDF and Excel readers stay first-class.

That guest view also carries requesters' personal details. This reader takes
an allowlist of booking fields (room, event, layout, instructions, headcounts,
organization, times, and the reservation's resources) and no contact details;
free text has email addresses and phone numbers scrubbed. See ADR-012 and
ADR-013.
"""

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from daily_events_excel import _format_time
from setup_report_processor import EventScheduleProcessor

# A child of the logger the GUI attaches its panel handler to (see ADR-008).
logger = logging.getLogger("setup_report_processor.twentyfive_live")

# The guest view's JSON endpoints.
BASE_URL = "https://25live.collegenet.com/25live/data/umdearborn/run"

# The event's own page in the 25Live site, opened from the timeline popup.
EVENT_URL = "https://25live.collegenet.com/pro/umdearborn#!/home/event/{}/details"

# Seconds to wait for 25Live before giving up on a day.
TIMEOUT = 60

# reservation_state code 25Live uses for a cancelled booking.
CANCELLED = 99


@dataclass(frozen=True)
class LiveDay:
    """
    One day to pull from 25Live, queued alongside report files.

    ``name`` and ``stem`` mirror the ``Path`` attributes the file queue and the
    worker read, so a day travels through them exactly like a file does.
    """

    day: date

    @property
    def name(self) -> str:
        # Plain ASCII: it lands in the log file, which uses the system codepage.
        return f"{self.day:%a %b} {self.day.day}, {self.day.year} (25Live)"

    @property
    def stem(self) -> str:
        return f"25live_{self.day:%Y-%m-%d}"


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_PHONE = re.compile(r"(?<!\d)(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")


def _scrub(text) -> str:
    """Remove email addresses and phone numbers from free text."""
    text = _EMAIL.sub("[email removed]", str(text or ""))
    return _PHONE.sub("[phone removed]", text).strip()


def _room(booking: dict) -> str:
    """A booking's room name, with 25Live's doubled spaces ("FCS Michigan  East") collapsed."""
    return " ".join(str((booking.get("spaces") or {}).get("space_name") or "").split())


def _local(timestamp: str) -> datetime:
    """Read "2026-10-06T08:45:00-04:00" as campus local time."""
    return datetime.fromisoformat(timestamp).replace(tzinfo=None)


class TwentyFiveLiveProcessor(EventScheduleProcessor):
    """Pull one day's bookings from 25Live and extract event schedules."""

    SOURCE_LABEL = "25Live"

    def __init__(self, day: date, config_path: Optional[str] = None):
        """
        Initialize the processor. Nothing is fetched until ``process()``.

        Args:
            day: The day to pull
            config_path: Optional path to location config JSON file
        """
        self.day = day
        # Filled per fetch by _collect_events, read by _parse_booking.
        self._resources: Dict[object, List[Dict[str, str]]] = {}
        self._rooms_by_reservation: Dict[object, List[str]] = {}
        # There is no file: source_path only names the source in log lines.
        super().__init__(LiveDay(day).name, config_path=config_path)

    def _validate_source(self) -> None:
        """Nothing to check before fetching; a bad day just has no bookings."""

    def extract_report_date(self) -> Optional[str]:
        """The report date is the day requested."""
        return self.day.strftime("%m-%d-%y")

    def _collect_events(self) -> List[Dict[str, str]]:
        """Fetch the day's room bookings and turn them into event records."""
        logger.info(f"Fetching {self.day:%a %b %d %Y} from 25Live...")
        # 25Live sorts by room, then time. The timeline keeps source order
        # within a day (ADR-011), so put bookings in setup-start order here.
        # ISO strings sort by time within a day (one UTC offset per day).
        bookings = sorted(
            self._fetch_bookings(),
            key=lambda b: str(b.get("reservation_start_dt") or ""),
        )

        # Resources belong to the reservation, which can cover several rooms,
        # so each event also needs to know the reservation's other rooms.
        self._resources = self._fetch_resources()
        self._rooms_by_reservation = {}
        for booking in bookings:
            self._rooms_by_reservation.setdefault(
                booking.get("reservation_id"), []
            ).append(_room(booking))

        events = [e for e in map(self._parse_booking, bookings) if e]
        logger.info(
            f"Found {len(events)} valid events in 25Live "
            f"(excluded {len(bookings) - len(events)} bookings)"
        )
        return events

    def _fetch_bookings(self) -> list:
        """
        Download every room booking on ``self.day``.

        Returns:
            The raw booking objects, one per event per room

        Raises:
            ConnectionError: If 25Live cannot be reached
            ValueError: If 25Live answers with something this reader cannot read
        """
        return self._fetch_list("rm_reservations", "space_reservations", "space_reservation")

    def _fetch_resources(self) -> Dict[object, List[Dict[str, str]]]:
        """
        Download the day's resource bookings, grouped by reservation id.

        Resources only feed the event popup, so a failure here is logged and
        the day still loads without them.

        Returns:
            ``{reservation id: [{name, quantity, instructions}]}``, allowlisted
        """
        try:
            items = self._fetch_list(
                "rs_reservations", "resource_reservations", "resource_reservation"
            )
        except (ConnectionError, ValueError) as e:
            logger.warning(f"25Live resources unavailable, loading without them: {e}")
            return {}

        grouped: Dict[object, List[Dict[str, str]]] = {}
        for item in items:
            if item.get("reservation_state") == CANCELLED:
                continue
            name = str((item.get("resources") or {}).get("resource_name") or "").strip()
            if not name:
                continue
            grouped.setdefault(item.get("reservation_id"), []).append({
                "name": name,
                "quantity": str(item.get("quantity") or ""),
                "instructions": _scrub(item.get("resource_instructions")),
            })
        return grouped

    def _fetch_list(self, endpoint: str, container: str, key: str) -> list:
        """
        Download one of 25Live's day lists and return its items.

        Raises:
            ConnectionError: If 25Live cannot be reached
            ValueError: If 25Live answers with something this reader cannot read
        """
        stamp = f"{self.day:%Y%m%d}"
        request = urllib.request.Request(
            f"{BASE_URL}/{endpoint}.json?start_dt={stamp}&end_dt={stamp}",
            headers={"User-Agent": "UUE-Report-Processor"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                data = json.load(response)
        except (urllib.error.URLError, TimeoutError) as e:
            raise ConnectionError(
                f"Could not reach 25Live ({getattr(e, 'reason', e)})"
            ) from e

        try:
            items = data[container].get(key)
        except (KeyError, AttributeError, TypeError) as e:
            raise ValueError("25Live sent a response this reader cannot read") from e

        # A day with no bookings omits the key, and a day with one booking
        # sends it as a bare object rather than a one-item list.
        if items is None:
            return []
        return items if isinstance(items, list) else [items]

    def _parse_booking(self, booking: dict) -> Optional[Dict[str, str]]:
        """
        Build an event record from one booking, or None if it is excluded.

        ``Setup Ready By`` is the reservation start, which is when setup begins:
        the same "Setup Starts" time the PDF reader prefers. ``Closing`` is the
        event's end, as in the PDF.

        Args:
            booking: One object from 25Live's ``space_reservation`` list

        Returns:
            Dictionary with event details or None if the booking is excluded
        """
        event = booking.get("event") or {}

        # Event Name is what the PDF and the Excel export both show.
        event_name = (event.get("event_name") or event.get("event_title") or "").strip()
        if not event_name:
            logger.info("EXCLUDED: Event with no name found")
            return None

        if (booking.get("reservation_state") == CANCELLED
                or event.get("state_name") == "Cancelled"):
            logger.info(f"EXCLUDED: '{event_name}' - cancelled")
            return None

        raw_location = _room(booking)
        if not raw_location:
            logger.info(f"EXCLUDED: '{event_name}' - no valid location found")
            return None

        location = self._match_whitelist_location(raw_location)
        if not location:
            logger.info(
                f"EXCLUDED: '{event_name}' at '{raw_location}' - "
                "location not in whitelist"
            )
            return None

        try:
            setup = _local(booking["reservation_start_dt"])
            start = _local(event["event_start_dt"])
            end = _local(event["event_end_dt"])
        except (KeyError, TypeError, ValueError):
            logger.info(f"EXCLUDED: '{event_name}' - no event times found")
            return None

        # A booking that crosses midnight is returned for both days; keep it
        # on the day it starts so a stacked weekend does not show it twice.
        if start.date() != self.day:
            logger.info(
                f"EXCLUDED: '{event_name}' - starts on {start:%m-%d-%y}, "
                "not this day"
            )
            return None

        reservation = booking.get("reservation_id")
        resources = self._resources.get(reservation, [])
        details = self._details(booking, event_name, setup, start, end)
        # Resources are booked for the whole reservation, so say which other
        # rooms they cover rather than imply this room gets all of them.
        others = [
            room for room in self._rooms_by_reservation.get(reservation, [])
            if room != raw_location
        ]
        if resources and others:
            details["Resources shared with"] = ", ".join(others)

        return {
            "event_name": event_name,
            "location": location,
            "setup_time": _format_time(setup),
            "closing_time": _format_time(end),
            "date": start.strftime("%m-%d-%y"),
            "details": details,
            "resources": resources,
            "url": EVENT_URL.format(event["event_id"]) if event.get("event_id") else "",
        }

    @staticmethod
    def _details(booking: dict, event_name: str, setup: datetime,
                 start: datetime, end: datetime) -> Dict[str, str]:
        """
        What the timeline's event popup shows, from allowlisted fields only.

        Contact details are never read. Booking comments are left out too:
        25Live uses them for internal notes.
        """
        event = booking.get("event") or {}
        space = booking.get("spaces") or {}

        def clock(field: str, source: dict) -> Optional[str]:
            try:
                return _format_time(_local(source[field]))
            except (KeyError, TypeError, ValueError):
                return None

        pre, post = clock("pre_event_dt", event), clock("post_event_dt", event)
        title = (event.get("event_title") or "").strip()
        pairs = (
            ("Title", title if title != event_name else None),
            ("Reference", event.get("event_locator")),
            ("Room", space.get("formal_name")),
            ("Layout", booking.get("layout_name")),
            ("Room instructions", _scrub(booking.get("space_instructions"))),
            ("Expected headcount", event.get("expected_count")),
            ("Registered headcount", event.get("registered_count")),
            ("Actual headcount", booking.get("act_head_count")),
            ("Event type", event.get("event_type_name")),
            ("Organization", event.get("organization_name")),
            ("Setup starts", _format_time(setup)),
            ("Pre-event", pre if pre != _format_time(start) else None),
            ("Event", f"{_format_time(start)} – {_format_time(end)}"),
            ("Post-event", post if post != _format_time(end) else None),
            ("Takedown ends", clock("reservation_end_dt", booking)),
        )
        return {
            label: str(value).strip()
            for label, value in pairs
            if value not in (None, "", 0) and str(value).strip()
        }
