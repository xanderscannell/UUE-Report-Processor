#!/usr/bin/env python3
"""
Unit Tests for Setup Report Processor
=====================================
Comprehensive test suite for the Daily Setup Report Processor.
"""

import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
from setup_report_processor import SetupReportProcessor


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
    """Test location filtering logic."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_valid_uc_location(self, processor):
        """Test valid UC location."""
        assert processor._is_valid_location("UC 1227 Conference") is True

    def test_valid_ruc_location(self, processor):
        """Test valid RUC location."""
        assert processor._is_valid_location("RUC 123 Room") is True

    def test_valid_fcs_michigan(self, processor):
        """Test valid FCS Michigan location."""
        assert processor._is_valid_location("FCS Michigan Room") is True

    def test_valid_fcs_180(self, processor):
        """Test valid FCS 180 location."""
        assert processor._is_valid_location("FCS 180") is True

    def test_valid_fcs_dining(self, processor):
        """Test valid FCS Dining Rm D location."""
        assert processor._is_valid_location("FCS Dining Rm D") is True

    def test_excluded_location_bake_sale(self, processor):
        """Test excluded location: Bake Sale."""
        assert processor._is_valid_location("UC Table-Bake/Day Sale") is False

    def test_excluded_location_info(self, processor):
        """Test excluded location: Info table."""
        assert processor._is_valid_location("UC Table-Info") is False

    def test_excluded_location_default(self, processor):
        """Test excluded location with default."""
        assert processor._is_valid_location("UC Lounge (default)") is False

    def test_invalid_location_prefix(self, processor):
        """Test invalid location prefix."""
        assert processor._is_valid_location("FH Ice Arena") is False

    def test_invalid_location_no_prefix(self, processor):
        """Test location with no valid prefix."""
        assert processor._is_valid_location("Random Room") is False


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
        block = """
        7:30 AM Setup Starts: Event Details
        """
        result = processor._extract_setup_time(block)
        assert result == "7:30 AM"

    def test_extract_setup_time_pm(self, processor):
        """Test extracting PM setup time."""
        block = """
        2:15 PM Setup Starts: Event Details
        """
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
    """Test location extraction and cleaning."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("")
        return SetupReportProcessor(str(pdf_file))

    def test_extract_clean_location(self, processor):
        """Test extracting clean location."""
        block = """
        Location Layout Instructions
        UC 1227 Conference
        """
        result = processor._extract_location(block)
        assert result == "UC 1227 Conference"

    def test_extract_location_with_notes(self, processor):
        """Test extracting location with extra notes."""
        block = """
        Location Layout Instructions
        UC 1227 Conference See Diagram
        """
        result = processor._extract_location(block)
        assert result == "UC 1227 Conference"

    def test_extract_location_with_setup_info(self, processor):
        """Test extracting location with setup information."""
        block = """
        Location Layout Instructions
        UC 1225 Cluster Set up in rows
        """
        result = processor._extract_location(block)
        assert result == "UC 1225 Cluster"

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
        assert result["location"] == "UC 1227 Conference"
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
