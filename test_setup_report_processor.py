#!/usr/bin/env python3
"""
Unit Tests for Setup Report Processor
=====================================
Comprehensive test suite for the Daily Setup Report Processor.
"""

import json
import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook

from setup_report_processor import SetupReportProcessor, create_processor
from daily_events_excel import DailyEventsExcelProcessor, _format_time

# Imported directly rather than via the package, so the suite stays runnable
# without PySide6 installed.
from gui_components.preferences import Preferences
from gui_components.settings import GUI_DEFAULTS


class TestInitialization:
    """Test processor initialization."""

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent PDF file."""
        with pytest.raises(FileNotFoundError):
            SetupReportProcessor("nonexistent_file.pdf")

    def test_init_with_non_pdf_file(self, tmp_path):
        """Test initialization with non-PDF file."""
        # Create a temporary text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="Expected PDF file"):
            SetupReportProcessor(str(txt_file))

    def test_init_with_valid_pdf(self, tmp_path):
        """Test initialization with valid PDF file (empty is ok for init)."""
        # Create a temporary PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")  # Empty file is fine for initialization test

        # Should not raise any exception
        processor = SetupReportProcessor(str(pdf_file))
        assert processor.pdf_path == pdf_file


class TestTimeParser:
    """Test time parsing functionality."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_parse_standard_time_format(self, processor):
        """Test parsing standard time format with space."""
        result = processor.parse_time("7:30 AM")
        assert result is not None
        assert result.hour == 7
        assert result.minute == 30

    def test_parse_time_without_space(self, processor):
        """Test parsing time format without space."""
        result = processor.parse_time("11:45PM")
        assert result is not None
        assert result.hour == 23
        assert result.minute == 45

    def test_parse_pm_time(self, processor):
        """Test parsing PM times."""
        result = processor.parse_time("2:15 PM")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 15

    def test_parse_noon(self, processor):
        """Test parsing noon."""
        result = processor.parse_time("12:00 PM")
        assert result is not None
        assert result.hour == 12
        assert result.minute == 0

    def test_parse_midnight(self, processor):
        """Test parsing midnight."""
        result = processor.parse_time("12:00 AM")
        assert result is not None
        assert result.hour == 0
        assert result.minute == 0

    def test_parse_no_setup_time(self, processor):
        """Test parsing 'no setup time defined'."""
        result = processor.parse_time("no setup time defined")
        assert result is None

    def test_parse_invalid_time(self, processor):
        """Test parsing invalid time string."""
        result = processor.parse_time("invalid time")
        assert result is None


class TestLocationValidation:
    """Test location whitelist matching."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_valid_uc_location(self, processor):
        """Test valid UC location returns exact whitelist name."""
        result = processor._match_whitelist_location("UC 1227 Conference Square")
        assert result == "UC 1227"

    def test_valid_ruc_location(self, processor):
        """Test valid RUC location returns exact whitelist name."""
        result = processor._match_whitelist_location("RUC 1172 (Lake Huron) Boardroom")
        assert result == "RUC 1172 (Lake Huron)"

    def test_valid_fcs_michigan(self, processor):
        """Test valid FCS Michigan East location."""
        result = processor._match_whitelist_location("FCS Michigan East Empty")
        assert result == "FCS Michigan East"

    def test_valid_fcs_180(self, processor):
        """Test valid FCS 180 location."""
        result = processor._match_whitelist_location("FCS 180 Classroom")
        assert result == "FCS 180"

    def test_valid_fcs_dining(self, processor):
        """Test valid FCS Dining Rm D location."""
        result = processor._match_whitelist_location("FCS Dining Rm D Cluster")
        assert result == "FCS Dining Rm D"

    def test_dirty_location_returns_clean_name(self, processor):
        """Test that dirty extracted text returns exact whitelist name."""
        dirty = "UC Kochoff Hall C Crescent Rounds Group has order with Picasso"
        result = processor._match_whitelist_location(dirty)
        assert result == "UC Kochoff Hall C"

    def test_non_whitelisted_table(self, processor):
        """Test non-whitelisted table location returns None."""
        assert processor._match_whitelist_location("UC Table-Bake/Day Sale") is None

    def test_non_whitelisted_info(self, processor):
        """Test non-whitelisted info table returns None."""
        assert processor._match_whitelist_location("UC Table-Info") is None

    def test_lounge_default_matches_lounge(self, processor):
        """Test UC Lounge (default) matches whitelisted UC Lounge."""
        result = processor._match_whitelist_location("UC Lounge (default)")
        assert result == "UC Lounge"

    def test_non_whitelisted_special(self, processor):
        """Test non-whitelisted Special location returns None."""
        assert processor._match_whitelist_location("UC Special Event Room") is None

    def test_invalid_location_prefix(self, processor):
        """Test invalid location prefix."""
        assert processor._match_whitelist_location("FH Ice Arena") is None

    def test_invalid_location_no_prefix(self, processor):
        """Test location with no valid prefix."""
        assert processor._match_whitelist_location("Random Room") is None


class TestEventNameExtraction:
    """Test event name extraction."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_extract_event_name_with_time(self, processor):
        """Test extracting event name with setup time."""
        block = """
        7:30 AM Setup Starts: 7:30 AM Book Club January Meeting Requestor: John Doe
        """
        result = processor._extract_event_name(block)
        assert result == "Book Club January Meeting"

    def test_extract_event_name_with_reference_code(self, processor):
        """Test extracting event name and removing reference code."""
        block = """
        7:30 AM Setup Starts: 7:30 AM Staff Meeting 2025-AANQFM Requestor: Jane Smith
        """
        result = processor._extract_event_name(block)
        assert result == "Staff Meeting"

    def test_extract_event_name_no_setup_time(self, processor):
        """Test extracting event name with no setup time defined."""
        block = """
        Setup Starts: no setup time defined Conference Call Requestor: Admin
        """
        result = processor._extract_event_name(block)
        assert result == "Conference Call"

    def test_extract_event_name_missing(self, processor):
        """Test when event name cannot be extracted."""
        block = """
        Some random text without the expected pattern
        """
        result = processor._extract_event_name(block)
        assert result is None


class TestSetupTimeExtraction:
    """Test setup time extraction."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_extract_setup_time_standard(self, processor):
        """Test extracting standard setup time."""
        block = "7:30 AM Setup Starts: Event Details"
        result = processor._extract_setup_time(block)
        assert result == "7:30 AM"

    def test_extract_setup_time_pm(self, processor):
        """Test extracting PM setup time."""
        block = "2:15 PM Setup Starts: Event Details"
        result = processor._extract_setup_time(block)
        assert result == "2:15 PM"

    def test_extract_setup_time_missing(self, processor):
        """Test when setup time is missing."""
        block = """
        Some text without setup time
        """
        result = processor._extract_setup_time(block)
        assert result is None


class TestEventTimesExtraction:
    """Test event times extraction."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_extract_event_times_standard(self, processor):
        """Test extracting standard event times."""
        block = """
        Event: 8:00 AM - 10:00 AM
        """
        result = processor._extract_event_times(block)
        assert result == ("8:00 AM", "10:00 AM")

    def test_extract_event_times_pm(self, processor):
        """Test extracting PM event times."""
        block = """
        Event: 2:00 PM - 4:30 PM
        """
        result = processor._extract_event_times(block)
        assert result == ("2:00 PM", "4:30 PM")

    def test_extract_event_times_missing(self, processor):
        """Test when event times are missing."""
        block = """
        Some text without event times
        """
        result = processor._extract_event_times(block)
        assert result is None


class TestLocationExtraction:
    """Test raw location extraction from event blocks."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_extract_raw_location(self, processor):
        """Test extracting raw location text."""
        block = """
        Location Layout Instructions
        UC 1227 Conference
        """
        result = processor._extract_location(block)
        assert result == "UC 1227 Conference"

    def test_extract_raw_location_with_junk(self, processor):
        """Test that raw extraction returns unclean text (cleanup is done by whitelist matching)."""
        block = """
        Location Layout Instructions
        UC Kochoff Hall C Crescent Rounds Group has order
        """
        result = processor._extract_location(block)
        assert result == "UC Kochoff Hall C Crescent Rounds Group has order"

    def test_extract_location_missing(self, processor):
        """Test when location is missing."""
        block = """
        Some text without location
        """
        result = processor._extract_location(block)
        assert result is None


class TestScheduleRowCreation:
    """Test schedule row creation."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_create_schedule_rows_single_event(self, processor):
        """Test creating schedule rows for single event."""
        events = [{
            "event_name": "Test Event",
            "location": "UC 1227",
            "setup_time": "7:30 AM",
            "closing_time": "10:00 AM"
        }]

        rows = processor.create_schedule_rows(events)

        assert len(rows) == 2
        assert rows[0]["Event Name"] == "Test Event"
        assert rows[0]["Activity"] == "Setup Ready By"
        assert rows[0]["Time"] == "7:30 AM"
        assert rows[1]["Activity"] == "Closing"
        assert rows[1]["Time"] == "10:00 AM"

    def test_create_schedule_rows_multiple_events(self, processor):
        """Test creating schedule rows for multiple events."""
        events = [
            {
                "event_name": "Event 1",
                "location": "UC 1227",
                "setup_time": "7:30 AM",
                "closing_time": "10:00 AM"
            },
            {
                "event_name": "Event 2",
                "location": "UC 1225",
                "setup_time": "11:00 AM",
                "closing_time": "2:00 PM"
            }
        ]

        rows = processor.create_schedule_rows(events)

        assert len(rows) == 4
        assert rows[0]["Event Name"] == "Event 1"
        assert rows[2]["Event Name"] == "Event 2"

    def test_create_schedule_rows_empty(self, processor):
        """Test creating schedule rows with no events."""
        rows = processor.create_schedule_rows([])
        assert len(rows) == 0


class TestChronologicalSorting:
    """Test chronological sorting."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_sort_chronologically_ordered(self, processor):
        """Test sorting already ordered rows."""
        rows = [
            {"Event Name": "Event 1", "Location": "UC 1227", "Activity": "Setup Ready By", "Time": "7:30 AM"},
            {"Event Name": "Event 1", "Location": "UC 1227", "Activity": "Closing", "Time": "10:00 AM"},
            {"Event Name": "Event 2", "Location": "UC 1225", "Activity": "Setup Ready By", "Time": "11:00 AM"},
        ]

        df = processor.sort_chronologically(rows)

        assert len(df) == 3
        assert df.iloc[0]["Time"] == "7:30 AM"
        assert df.iloc[1]["Time"] == "10:00 AM"
        assert df.iloc[2]["Time"] == "11:00 AM"

    def test_sort_chronologically_unordered(self, processor):
        """Test sorting unordered rows."""
        rows = [
            {"Event Name": "Event 2", "Location": "UC 1225", "Activity": "Setup Ready By", "Time": "11:00 AM"},
            {"Event Name": "Event 1", "Location": "UC 1227", "Activity": "Setup Ready By", "Time": "7:30 AM"},
            {"Event Name": "Event 1", "Location": "UC 1227", "Activity": "Closing", "Time": "10:00 AM"},
        ]

        df = processor.sort_chronologically(rows)

        assert len(df) == 3
        assert df.iloc[0]["Time"] == "7:30 AM"
        assert df.iloc[1]["Time"] == "10:00 AM"
        assert df.iloc[2]["Time"] == "11:00 AM"

    def test_sort_chronologically_with_pm_times(self, processor):
        """Test sorting with AM and PM times."""
        rows = [
            {"Event Name": "Event 1", "Location": "UC 1227", "Activity": "Setup Ready By", "Time": "2:00 PM"},
            {"Event Name": "Event 2", "Location": "UC 1225", "Activity": "Setup Ready By", "Time": "7:30 AM"},
            {"Event Name": "Event 3", "Location": "UC 1226", "Activity": "Setup Ready By", "Time": "11:00 AM"},
        ]

        df = processor.sort_chronologically(rows)

        assert len(df) == 3
        assert df.iloc[0]["Time"] == "7:30 AM"
        assert df.iloc[1]["Time"] == "11:00 AM"
        assert df.iloc[2]["Time"] == "2:00 PM"

    def test_sort_chronologically_empty(self, processor):
        """Test sorting empty row list."""
        df = processor.sort_chronologically([])

        assert len(df) == 0
        assert list(df.columns) == ["Event Name", "Location", "Activity", "Time"]


class TestIntegration:
    """Integration tests for full workflow."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_full_event_parsing(self, processor):
        """Test parsing a complete event block."""
        block = """
7:30 AM Setup Starts: 7:30 AM Book Club January Meeting Requestor: John Doe
Pre-Event: 7:30 AM
Event: 8:00 AM - 10:00 AM
Location Layout Instructions
UC 1227 Conference
Some other details
"""
        result = processor._parse_event_block(block)

        assert result is not None
        assert result["event_name"] == "Book Club January Meeting"
        assert result["location"] == "UC 1227"
        assert result["setup_time"] == "7:30 AM"
        assert result["closing_time"] == "10:00 AM"

    def test_event_parsing_with_filtering(self, processor):
        """Test parsing event that should be filtered out."""
        block = """
7:30 AM Setup Starts: 7:30 AM Hockey Practice Requestor: Coach
Pre-Event: 7:30 AM
Event: 8:00 AM - 10:00 AM
Location Layout Instructions
FH Ice Arena
"""
        result = processor._parse_event_block(block)

        # Should be None because location doesn't match criteria
        assert result is None


class TestConfigLoading:
    """Test location config file loading."""

    def test_default_config_fallback(self, tmp_path):
        """Test that processor works with no config file (hardcoded defaults)."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        # Pass a nonexistent config path to force fallback
        processor = SetupReportProcessor(str(pdf_file), config_path=str(tmp_path / "nonexistent.json"))
        assert len(processor._location_whitelist) > 0

    def test_explicit_v2_config_file(self, tmp_path):
        """Test loading from an explicit v2 config file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")

        config = {
            "version": 2,
            "locations": [
                {"name": "Custom Room A", "enabled": True},
                {"name": "Custom Room B", "enabled": True},
                {"name": "Disabled Room", "enabled": False},
            ]
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config))

        processor = SetupReportProcessor(str(pdf_file), config_path=str(config_file))
        assert set(processor._location_whitelist) == {"Custom Room A", "Custom Room B"}
        assert len(processor._location_whitelist) == 2

    def test_legacy_v1_config_file(self, tmp_path):
        """Test loading from a legacy v1 config file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")

        config = {
            "version": 1,
            "locations": {
                "whitelist": ["Room Alpha", "Room Beta"],
                "blacklist": ["Excluded"]
            }
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config))

        processor = SetupReportProcessor(str(pdf_file), config_path=str(config_file))
        assert set(processor._location_whitelist) == {"Room Alpha", "Room Beta"}

    def test_invalid_config_falls_back(self, tmp_path):
        """Test that invalid JSON falls back to defaults."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")

        config_file = tmp_path / "bad_config.json"
        config_file.write_text("not valid json {{{")

        processor = SetupReportProcessor(str(pdf_file), config_path=str(config_file))
        assert len(processor._location_whitelist) > 0

    def test_custom_whitelist_matching(self, tmp_path):
        """Test that custom config whitelist is used for matching."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")

        config = {
            "version": 2,
            "locations": [
                {"name": "Test Room 101", "enabled": True},
            ]
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config))

        processor = SetupReportProcessor(str(pdf_file), config_path=str(config_file))
        assert processor._match_whitelist_location("Test Room 101 Extra Junk") == "Test Room 101"
        assert processor._match_whitelist_location("UC 1227") is None


class TestPreferences:
    """Test persistence of GUI preferences (no Qt required)."""

    def test_defaults_when_file_missing(self, tmp_path):
        """Test that a first run falls back to the shipped defaults."""
        prefs = Preferences.load(tmp_path / "gui_preferences.json")
        assert prefs.get_bool("excel_enabled") is True
        assert prefs.get_bool("keep_awake") is False

    def test_round_trip(self, tmp_path):
        """Test that saved preferences come back on the next load."""
        path = tmp_path / "gui_preferences.json"
        prefs = Preferences()
        prefs.set("keep_awake", True)
        prefs.set("excel_enabled", False)
        prefs.set("output_dir", tmp_path)
        assert prefs.save(path) is True

        reloaded = Preferences.load(path)
        assert reloaded.get_bool("keep_awake") is True
        assert reloaded.get_bool("excel_enabled") is False
        assert reloaded.get_path("output_dir") == tmp_path

    def test_set_reports_whether_anything_changed(self):
        """Test that set() only reports True for a real change."""
        prefs = Preferences()
        assert prefs.set("keep_awake", False) is False
        assert prefs.set("keep_awake", True) is True

    def test_unknown_key_is_ignored(self):
        """Test that an unknown preference is refused, not stored."""
        prefs = Preferences()
        assert prefs.set("not_a_preference", True) is False
        assert "not_a_preference" not in prefs.values

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path):
        """Test that a malformed file degrades to defaults instead of raising."""
        path = tmp_path / "gui_preferences.json"
        path.write_text("{ this is not json", encoding="utf-8")

        prefs = Preferences.load(path)
        assert prefs.get_bool("excel_enabled") is True

    def test_unreachable_output_dir_falls_back(self, tmp_path):
        """Test that a saved folder on a missing drive reverts to the default."""
        path = tmp_path / "gui_preferences.json"
        path.write_text(
            json.dumps({"output_dir": "Z:\\gone\\reports", "csv_enabled": True}),
            encoding="utf-8",
        )

        prefs = Preferences.load(path)
        assert prefs.get_path("output_dir") == Path(GUI_DEFAULTS["output_dir"])
        assert prefs.get_bool("csv_enabled") is True  # other keys still load

    def test_save_failure_is_reported_not_raised(self):
        """Test that an unwritable location returns False rather than raising."""
        assert Preferences().save(Path("Z:\\nowhere\\gui_preferences.json")) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ======================================================================
# Daily Events Excel export
# ======================================================================

# Columns as the database emits them, in order.
EXPORT_HEADERS = [
    "Day", "Event Start", "Event End", "Event Name", "Event Title",
    "Reference #", "Location", "Formal Name", "Layout", "Event Type",
]

DAY = datetime(2026, 8, 22)


def booking(location, name="FSL Retreat", start=(9, 0), end=(15, 30),
            title=None, reference="2026-AAPFPT", day=DAY):
    """Build one export row (a booking) in EXPORT_HEADERS order."""
    return [
        day,
        datetime(day.year, day.month, day.day, *start),
        datetime(day.year, day.month, day.day, *end),
        name, title, reference, location,
        f"Formal {location}", "Banquet Rounds", "Staff Retreat",
    ]


def write_export(path, rows, headers=None, report_date="Aug 22 2026",
                 sheet_titles=("Event List Aug 22 2026",)):
    """
    Write a workbook shaped like the database's Daily Events export.

    The real sample file is gitignored (``*.xlsx``), so every test builds its
    own fixture rather than depending on a file that a clean clone lacks.

    Args:
        path: Where to write the .xlsx
        rows: List of row lists, or a dict of sheet title to row lists
        headers: Header row (defaults to EXPORT_HEADERS)
        report_date: Value beside the "Report Date" label; None omits the
            Parameter Summary sheet entirely
        sheet_titles: Titles for the data sheets
    """
    workbook = Workbook()
    first = workbook.active

    if report_date is None:
        first.title = sheet_titles[0]
        sheets = [first]
    else:
        first.title = "Parameter Summary"
        first.append([None, "Report Name", "Daily Events - Excel"])
        first.append([None, "Report Date", report_date])
        first.append([None, "Location Search", "All Locations"])
        sheets = [workbook.create_sheet(title) for title in sheet_titles]

    by_sheet = rows if isinstance(rows, dict) else {sheet_titles[0]: rows}
    for sheet in sheets:
        sheet.append(headers if headers is not None else EXPORT_HEADERS)
        for row in by_sheet.get(sheet.title, []):
            sheet.append(row)

    workbook.save(path)
    return path


@pytest.fixture
def export_config(tmp_path):
    """A location config with two rooms enabled, matching the export's codes."""
    config = {
        "version": 2,
        "locations": [
            {"name": "UC 1225", "enabled": True},
            {"name": "UC Kochoff Hall C", "enabled": True},
            {"name": "FH Gym", "enabled": False},
        ],
    }
    path = tmp_path / "export_config.json"
    path.write_text(json.dumps(config))
    return str(path)


class TestExcelTimeFormatting:
    """Times must come out in the same 12-hour strings the PDF path produces."""

    @pytest.mark.parametrize("hour,minute,expected", [
        (9, 0, "9:00 AM"),
        (15, 30, "3:30 PM"),
        (10, 0, "10:00 AM"),
        (0, 30, "12:30 AM"),
        (12, 15, "12:15 PM"),
        (23, 59, "11:59 PM"),
    ])
    def test_datetime_cells(self, hour, minute, expected):
        """Datetime cells render without a leading zero, as the PDF does."""
        assert _format_time(datetime(2026, 8, 22, hour, minute)) == expected

    def test_string_cell_is_parsed(self):
        """Exports that emit text instead of datetimes still work."""
        assert _format_time("3:30 PM") == "3:30 PM"
        assert _format_time("09:05 a.m.") == "9:05 AM"

    def test_unusable_cell_returns_none(self):
        """A blank or unreadable cell yields None rather than raising."""
        assert _format_time(None) is None
        assert _format_time("") is None
        assert _format_time("sometime") is None


class TestDailyEventsExcel:
    """Test reading events out of the Daily Events Excel export."""

    def test_report_date_from_parameter_summary(self, tmp_path, export_config):
        """The Parameter Summary's Report Date is the preferred source."""
        path = write_export(tmp_path / "export.xlsx", [booking("UC 1225")])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert processor.report_date == "08-22-26"
        assert processor.get_output_basename() == "08-22-26"

    def test_report_date_falls_back_to_sheet_title(self, tmp_path, export_config):
        """With no Parameter Summary, the sheet title carries the date."""
        path = write_export(
            tmp_path / "export.xlsx", [booking("UC 1225")], report_date=None
        )
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert processor.report_date == "08-22-26"

    def test_report_date_falls_back_to_day_column(self, tmp_path, export_config):
        """With no date in the title either, the Day column is used."""
        path = write_export(
            tmp_path / "export.xlsx", {"Event List": [booking("UC 1225")]},
            report_date=None, sheet_titles=("Event List",),
        )
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert processor.report_date == "08-22-26"

    def test_report_date_absent_falls_back_to_filename(self, tmp_path, export_config):
        """With no date anywhere, output naming reverts to the file stem."""
        rows = [booking("UC 1225")]
        rows[0][0] = None  # blank the Day cell
        path = write_export(
            tmp_path / "DailyEventsExcel.xlsx", {"Event List": rows},
            report_date=None, sheet_titles=("Event List",),
        )
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert processor.report_date is None
        assert processor.get_output_basename() == "DailyEventsExcel"

    def test_whitelisted_location_is_kept(self, tmp_path, export_config):
        """A room on the whitelist produces an event record."""
        path = write_export(tmp_path / "export.xlsx", [booking("UC 1225")])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        events = processor._collect_events()

        assert len(events) == 1
        assert events[0] == {
            "event_name": "FSL Retreat",
            "location": "UC 1225",
            "setup_time": "9:00 AM",
            "closing_time": "3:30 PM",
        }

    def test_unlisted_locations_are_dropped(self, tmp_path, export_config):
        """The export covers all campus rooms; only whitelisted ones survive."""
        path = write_export(tmp_path / "export.xlsx", [
            booking("UC 1225"),
            booking("FH Gym", name="Just Between Friends"),
            booking("Pk Lot E3", name="Dearborn Electric Racing"),
            booking("FH Ice Arena", name="W. Ice Hockey Camp"),
        ])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        events = processor._collect_events()

        assert [e["location"] for e in events] == ["UC 1225"]

    def test_two_bookings_of_one_event_yield_two_records(self, tmp_path, export_config):
        """One event in two rooms is two bookings, matching the PDF model."""
        path = write_export(tmp_path / "export.xlsx", [
            booking("UC 1225"),
            booking("UC Kochoff Hall C"),
        ])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        events = processor._collect_events()

        assert len(events) == 2
        assert {e["location"] for e in events} == {"UC 1225", "UC Kochoff Hall C"}
        assert {e["event_name"] for e in events} == {"FSL Retreat"}

    def test_event_title_used_when_name_is_blank(self, tmp_path, export_config):
        """Event Title is the fallback when Event Name is empty."""
        row = booking("UC 1225", name=None, title="Fraternity & Sorority Life Retreat")
        path = write_export(tmp_path / "export.xlsx", [row])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)

        events = processor._collect_events()
        assert events[0]["event_name"] == "Fraternity & Sorority Life Retreat"

    def test_blank_rows_are_ignored(self, tmp_path, export_config):
        """Trailing empty rows must not count as excluded events."""
        path = write_export(tmp_path / "export.xlsx", [
            booking("UC 1225"),
            [None] * len(EXPORT_HEADERS),
            [None] * len(EXPORT_HEADERS),
        ])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert len(processor._collect_events()) == 1

    def test_row_missing_times_is_excluded(self, tmp_path, export_config):
        """A booking with no usable times cannot be scheduled."""
        row = booking("UC 1225")
        row[1] = None
        path = write_export(tmp_path / "export.xlsx", [row])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert processor._collect_events() == []

    def test_all_event_list_sheets_are_read(self, tmp_path, export_config):
        """A multi-day export must not be truncated to its first sheet."""
        titles = ("Event List Aug 22 2026", "Event List Aug 23 2026")
        path = write_export(
            tmp_path / "export.xlsx",
            {
                titles[0]: [booking("UC 1225")],
                titles[1]: [booking("UC Kochoff Hall C", name="Day Two")],
            },
            sheet_titles=titles,
        )
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        events = processor._collect_events()

        assert len(events) == 2
        assert {e["event_name"] for e in events} == {"FSL Retreat", "Day Two"}

    def test_missing_required_column_raises(self, tmp_path, export_config):
        """A changed report definition fails loudly, naming what is absent."""
        headers = [h for h in EXPORT_HEADERS if h != "Location"]
        rows = [[c for i, c in enumerate(booking("UC 1225"))
                 if EXPORT_HEADERS[i] != "Location"]]
        path = write_export(tmp_path / "export.xlsx", rows, headers=headers)

        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        with pytest.raises(ValueError, match="Missing required column"):
            processor._collect_events()

    def test_headers_are_matched_case_insensitively(self, tmp_path, export_config):
        """Column names are matched loosely so casing changes do not break it."""
        headers = [h.upper() for h in EXPORT_HEADERS]
        path = write_export(
            tmp_path / "export.xlsx", [booking("UC 1225")], headers=headers
        )
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        assert len(processor._collect_events()) == 1

    def test_non_xlsx_file_rejected(self, tmp_path):
        """The reader refuses files it cannot open."""
        txt = tmp_path / "notes.txt"
        txt.write_text("not a workbook")
        with pytest.raises(ValueError, match="Expected Excel file"):
            DailyEventsExcelProcessor(str(txt))

    def test_legacy_xls_gets_a_pointed_message(self, tmp_path):
        """.xls cannot be read by openpyxl, so say so rather than failing oddly."""
        legacy = tmp_path / "old.xls"
        legacy.write_text("")
        with pytest.raises(ValueError, match="re-save the report as .xlsx"):
            DailyEventsExcelProcessor(str(legacy))

    def test_missing_file_raises(self, tmp_path):
        """A path that does not exist fails before any parsing."""
        with pytest.raises(FileNotFoundError):
            DailyEventsExcelProcessor(str(tmp_path / "gone.xlsx"))

    def test_process_produces_a_sorted_schedule(self, tmp_path, export_config):
        """End to end: two bookings become four chronologically sorted rows."""
        path = write_export(tmp_path / "export.xlsx", [
            booking("UC Kochoff Hall C", start=(13, 0), end=(16, 0)),
            booking("UC 1225", start=(9, 0), end=(15, 30)),
            booking("FH Gym", name="Excluded"),
        ])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)
        df = processor.process()

        assert list(df.columns) == ["Event Name", "Location", "Activity", "Time"]
        assert len(df) == 4
        assert list(df["Time"]) == ["9:00 AM", "1:00 PM", "3:30 PM", "4:00 PM"]
        assert list(df["Activity"]) == [
            "Setup Ready By", "Setup Ready By", "Closing", "Closing"
        ]
        assert "Excluded" not in set(df["Event Name"])

    def test_gantt_rows_share_the_pdf_path(self, tmp_path, export_config):
        """Excel events feed the timeline through the same conversion."""
        path = write_export(tmp_path / "export.xlsx", [booking("UC 1225")])
        processor = DailyEventsExcelProcessor(str(path), config_path=export_config)

        rows = processor.create_gantt_rows(processor._collect_events())
        assert rows == [{
            "EventName": "FSL Retreat",
            "Location": "UC 1225",
            "StartTime": "09:00",
            "EndTime": "15:30",
        }]


class TestProcessorFactory:
    """Test extension-based dispatch to the right reader."""

    def test_pdf_returns_the_pdf_processor(self, tmp_path):
        """A .pdf is routed to the regex-based reader."""
        pdf = tmp_path / "report.pdf"
        pdf.write_text("")
        assert isinstance(create_processor(str(pdf)), SetupReportProcessor)

    def test_xlsx_returns_the_excel_processor(self, tmp_path, export_config):
        """An .xlsx is routed to the database export reader."""
        path = write_export(tmp_path / "export.xlsx", [booking("UC 1225")])
        processor = create_processor(str(path), config_path=export_config)
        assert isinstance(processor, DailyEventsExcelProcessor)

    def test_extension_matching_is_case_insensitive(self, tmp_path, export_config):
        """An .XLSX from a Windows share dispatches the same way."""
        path = write_export(tmp_path / "EXPORT.XLSX", [booking("UC 1225")])
        processor = create_processor(str(path), config_path=export_config)
        assert isinstance(processor, DailyEventsExcelProcessor)

    def test_unsupported_extension_raises(self, tmp_path):
        """Anything else is refused before the file is opened."""
        other = tmp_path / "notes.docx"
        other.write_text("")
        with pytest.raises(ValueError, match="Unsupported report type"):
            create_processor(str(other))

    def test_config_path_is_passed_through(self, tmp_path, export_config):
        """The factory must not drop the caller's config path."""
        path = write_export(tmp_path / "export.xlsx", [booking("UC 1225")])
        processor = create_processor(str(path), config_path=export_config)
        assert set(processor._location_whitelist) == {"UC 1225", "UC Kochoff Hall C"}
