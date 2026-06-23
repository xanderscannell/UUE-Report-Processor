#!/usr/bin/env python3
"""
Daily Setup Report Processor
============================
Extracts event information from Daily Setup Report PDFs and creates
chronologically ordered schedules in Excel/CSV format.

Author: Production Script
Version: 1.0.0
"""

import re
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import pdfplumber

# Resolve base directory (works for both script and frozen .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_report_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default location config file path (alongside the script or .exe)
DEFAULT_CONFIG_PATH = BASE_DIR / "location_config.json"

# Hardcoded fallback defaults (used when no config file exists)
DEFAULT_LOCATION_CONFIG = [
    {"name": "UC 1225", "enabled": True},
    {"name": "UC 1227", "enabled": True},
    {"name": "UC 2190", "enabled": True},
    {"name": "UC Stage", "enabled": True},
    {"name": "UC Kochoff Hall", "enabled": True},
    {"name": "UC Kochoff Hall A", "enabled": True},
    {"name": "UC Kochoff Hall B", "enabled": True},
    {"name": "UC Kochoff Hall C", "enabled": True},
    {"name": "UC Lounge", "enabled": True},
    {"name": "RUC 1150 (Victors Den)", "enabled": True},
    {"name": "RUC 1171 (Lake Erie)", "enabled": True},
    {"name": "RUC 1172 (Lake Huron)", "enabled": True},
    {"name": "RUC 1173 (Lake Michigan)", "enabled": True},
    {"name": "RUC 1174 (Lake Superior)", "enabled": True},
    {"name": "RUC 1175 (Lake Ontario)", "enabled": True},
    {"name": "FCS 180", "enabled": True},
    {"name": "FCS Dining Rm D", "enabled": True},
    {"name": "FCS Michigan East", "enabled": True},
    {"name": "UC Table-Bake/Day Sale", "enabled": False},
    {"name": "UC Table-Info", "enabled": False},
    {"name": "UC Table-Promo1", "enabled": False},
    {"name": "UC Table-Promo2", "enabled": False},
    {"name": "Special", "enabled": False},
    {"name": "Notice", "enabled": False},
]


class SetupReportProcessor:
    """Process Daily Setup Report PDFs and extract event schedules."""

    def __init__(self, pdf_path: str, config_path: Optional[str] = None):
        """
        Initialize the processor.

        Args:
            pdf_path: Path to the PDF file to process
            config_path: Optional path to location config JSON file

        Raises:
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the file is not a PDF
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {self.pdf_path.suffix}")

        # Load location configuration
        self._load_location_config(config_path)

        # Store intermediate data for Gantt chart generation
        self._events = None

        # Extract report date for filename generation
        self.report_date = self.extract_report_date()
        if self.report_date:
            logger.info(f"Extracted report date: {self.report_date}")
        else:
            logger.warning("Could not extract report date from PDF, will use PDF filename")

        logger.info(f"Initialized processor for: {self.pdf_path}")

    def _load_location_config(self, config_path: Optional[str] = None) -> None:
        """
        Load location whitelist from JSON config file.

        Supports both v2 (object array with enabled flags) and v1 (legacy
        whitelist/blacklist arrays) formats.

        Resolution order:
        1. Explicit config_path parameter
        2. DEFAULT_CONFIG_PATH (location_config.json alongside this script)
        3. Hardcoded DEFAULT_LOCATION_CONFIG fallback

        Args:
            config_path: Optional explicit path to config JSON file
        """
        resolved_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

        if resolved_path.exists():
            try:
                with open(resolved_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                version = config_data.get("version", 1)

                if version >= 2:
                    # v2 format: list of objects with enabled flag
                    locations = config_data.get("locations", [])
                    enabled = [loc["name"] for loc in locations if loc.get("enabled", True)]
                    logger.info(f"Loaded v2 location config from: {resolved_path}")
                    logger.info(f"  {len(enabled)} enabled / {len(locations)} total locations")
                else:
                    # v1 legacy format: separate whitelist/blacklist arrays
                    locations_dict = config_data.get("locations", {})
                    enabled = locations_dict.get("whitelist", [])
                    logger.info(f"Loaded v1 (legacy) location config from: {resolved_path}")
                    logger.info(f"  {len(enabled)} whitelist locations")

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Error reading config file {resolved_path}: {e}")
                logger.warning("Falling back to built-in defaults")
                enabled = [loc["name"] for loc in DEFAULT_LOCATION_CONFIG if loc.get("enabled", True)]
        else:
            if config_path:
                logger.warning(f"Config file not found: {resolved_path}")
            logger.info("Using built-in default location configuration")
            enabled = [loc["name"] for loc in DEFAULT_LOCATION_CONFIG if loc.get("enabled", True)]

        # Sort whitelist longest-first for greedy matching
        self._location_whitelist = sorted(enabled, key=len, reverse=True)

    def extract_text_from_pdf(self) -> str:
        """
        Extract all text from the PDF file.

        Returns:
            Complete text content of the PDF
        """
        logger.info("Extracting text from PDF...")
        pages = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
                        logger.debug(f"Extracted text from page {page_num}")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

        text = "\n".join(pages)
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text

    def extract_report_date(self) -> Optional[str]:
        """
        Extract report date from first page and format as MM-DD-YY.

        Searches for date pattern like "Wednesday, Jan 07 2026" on the
        first page of the PDF and converts it to MM-DD-YY format.

        Returns:
            Formatted date string (e.g., "01-07-26") or None if not found

        Example:
            >>> processor = SetupReportProcessor("report.pdf")
            >>> processor.extract_report_date()
            '01-07-26'
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if not pdf.pages:
                    logger.warning("PDF has no pages")
                    return None

                # Extract first page text
                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    logger.warning("First page is empty")
                    return None

                # Search for date pattern: "Wednesday, Jan 07 2026"
                pattern = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{4})"
                match = re.search(pattern, first_page_text)

                if not match:
                    logger.warning("Date pattern not found on first page")
                    return None

                month_abbr, day, year = match.groups()

                # Parse the date
                date_str = f"{month_abbr} {day} {year}"
                report_date = datetime.strptime(date_str, "%b %d %Y")

                # Format as MM-DD-YY
                formatted_date = report_date.strftime("%m-%d-%y")
                logger.debug(f"Parsed date: {date_str} -> {formatted_date}")

                return formatted_date

        except ValueError as e:
            logger.warning(f"Invalid date format: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error extracting report date: {e}")
            return None

    def get_output_basename(self) -> str:
        """
        Get the base name for output files.

        Returns the report date in MM-DD-YY format if available,
        otherwise falls back to the PDF filename stem.

        Returns:
            Base filename string (either date or PDF name)

        Example:
            >>> processor.report_date = "01-07-26"
            >>> processor.get_output_basename()
            '01-07-26'
            >>> processor.report_date = None
            >>> processor.get_output_basename()
            'daily_report'
        """
        return self.report_date if self.report_date else self.pdf_path.stem

    def parse_time(self, time_str: str) -> Optional[datetime]:
        """
        Parse time string to datetime object for sorting.

        Args:
            time_str: Time string like "7:30 AM", "12:00 PM", or "no setup time defined"

        Returns:
            datetime object or None if parsing fails
        """
        # Handle special case
        if "no setup time defined" in time_str.lower():
            return None

        try:
            # Try standard format
            return datetime.strptime(time_str.strip(), "%I:%M %p")
        except ValueError:
            try:
                # Try without space
                return datetime.strptime(time_str.strip(), "%I:%M%p")
            except ValueError:
                logger.warning(f"Could not parse time: {time_str}")
                return None

    def convert_to_24hour(self, time_str: str, reference_hour: int = 0) -> Optional[str]:
        """
        Convert 12-hour time to 24-hour format with midnight crossing support.

        Args:
            time_str: Time like "1:15 AM", "11:30 PM"
            reference_hour: Previous event hour (0-23) for midnight crossing detection

        Returns:
            24-hour time like "01:15" or "25:00" (for next-day times)

        Example:
            >>> processor.convert_to_24hour("1:15 AM")
            '01:15'
            >>> processor.convert_to_24hour("2:00 AM", reference_hour=23)
            '26:00'  # Next day notation for midnight crossing
        """
        dt = self.parse_time(time_str)
        if not dt:
            return None

        hour_24 = dt.hour

        # Handle midnight crossing: if this time is much earlier than reference,
        # it's likely the next day (e.g., setup at 11 PM, closing at 2 AM)
        if reference_hour >= 18 and hour_24 <= 6:  # Late night → early morning
            hour_24 += 24  # Use next-day notation: 25:00, 26:00, etc.

        return f"{hour_24:02d}:{dt.minute:02d}"

    def extract_events(self, text: str) -> List[Dict[str, str]]:
        """
        Extract event information from PDF text.

        Args:
            text: Complete text content of the PDF

        Returns:
            List of event dictionaries
        """
        logger.info("Parsing events from text...")
        events = []
        total_blocks = 0

        # Split text into event blocks
        # Pattern: Split on lines that contain "Setup Starts:"
        blocks = re.split(r"(?=(?<!\d)\d{1,2}:\d{2} [AP]M Setup Starts:)", text)

        for block in blocks:
            if "Setup Starts:" not in block:
                continue

            total_blocks += 1
            try:
                event_data = self._parse_event_block(block)
                if event_data:
                    events.append(event_data)
            except Exception as e:
                logger.warning(f"Error parsing event block: {e}")
                logger.debug(f"Block content: {block[:200]}...")
                continue

        excluded_count = total_blocks - len(events)
        logger.info(f"Found {len(events)} valid events in PDF (excluded {excluded_count} events)")
        return events
    
    def _extract_setup_time(self, block: str) -> Optional[str]:
        """
        Extract setup time from event block.

        Falls back in this order:
        1. Setup Starts time (if defined)
        2. Pre-Event time (if defined)
        3. Event start time (as last resort)

        Args:
            block: Text block containing event data

        Returns:
            Setup time string or None if not found
        """
        setup_match = re.search(r"^(\d{1,2}:\d{2} [AP]M) Setup Starts:", block, re.MULTILINE)

        if setup_match:
            # Check if this is a "no setup time defined" case
            # If so, skip this match and use Pre-Event time instead
            if "Setup Starts: no setup time defined" not in block:
                return setup_match.group(1)
            # Otherwise, fall through to Pre-Event

        # If no setup time, look for Pre-Event time
        pre_event_match = re.search(r"Pre-Event:\s+(\d{1,2}:\d{2} [AP]M)", block)
        if pre_event_match:
            return pre_event_match.group(1)

        # If neither setup nor pre-event time exists, use Event start time
        event_match = re.search(r"Event:\s+(\d{1,2}:\d{2} [AP]M)\s+-", block)
        if event_match:
            logger.debug(f"Using Event start time as fallback: {event_match.group(1)}")
            return event_match.group(1)

        return None

    def _extract_event_name(self, block: str) -> Optional[str]:
        """
        Extract and clean event name from event block.

        Args:
            block: Text block containing event data

        Returns:
            Cleaned event name or None if not found
        """
        # Handle both cases: with time and "no setup time defined"
        if "no setup time defined" in block:
            name_pattern = r"Setup Starts:\s*no setup time defined\s+(.+?)\s+Requestor:"
        else:
            name_pattern = r"Setup Starts:\s*\d{1,2}:\d{2} [AP]M\s+(.+?)\s+Requestor:"

        name_match = re.search(name_pattern, block)
        if not name_match:
            return None

        event_name = name_match.group(1).strip()

        # Remove reference codes (like "2025-AANQFM") from event name
        event_name = re.sub(r"\s*\d{4}-[A-Z0-9]+\s*$", "", event_name).strip()

        return event_name

    def _extract_event_times(self, block: str) -> Optional[tuple[str, str]]:
        """
        Extract event start and end times from event block.

        Args:
            block: Text block containing event data

        Returns:
            Tuple of (start_time, end_time) or None if not found
        """
        time_match = re.search(r"Event:\s+(\d{1,2}:\d{2} [AP]M)\s+-\s+(\d{1,2}:\d{2} [AP]M)", block)
        if not time_match:
            return None

        return (time_match.group(1), time_match.group(2))

    def _extract_location(self, block: str) -> Optional[str]:
        """
        Extract raw location text from event block.

        Args:
            block: Text block containing event data

        Returns:
            Raw location string or None if not found
        """
        location_match = re.search(r"Location Layout Instructions\s*\n([^\n]+)", block)
        if not location_match:
            return None

        location = location_match.group(1).strip()

        if not location:
            return None

        return location

    def _parse_event_block(self, block: str) -> Optional[Dict[str, str]]:
        """
        Parse a single event block to extract event details.

        Args:
            block: Text block containing a single event

        Returns:
            Dictionary with event details or None if parsing fails
        """
        # Extract setup time
        setup_time = self._extract_setup_time(block)
        if not setup_time:
            logger.info("EXCLUDED: Event with no setup/pre-event/event time")
            return None

        # Extract event name
        event_name = self._extract_event_name(block)
        if not event_name:
            logger.info("EXCLUDED: Event with no name found")
            return None

        # Extract event time range
        event_times = self._extract_event_times(block)
        if not event_times:
            logger.info(f"EXCLUDED: '{event_name}' - no event times found")
            return None
        event_start, event_end = event_times

        # Extract raw location from PDF
        raw_location = self._extract_location(block)
        if not raw_location:
            logger.info(f"EXCLUDED: '{event_name}' - no valid location found")
            return None

        # Match against whitelist (returns exact room name or None)
        location = self._match_whitelist_location(raw_location)
        if not location:
            logger.info(f"EXCLUDED: '{event_name}' at '{raw_location}' - location not in whitelist")
            return None

        return {
            "event_name": event_name,
            "location": location,
            "setup_time": setup_time,
            "closing_time": event_end
        }
    
    def _match_whitelist_location(self, raw_location: str) -> Optional[str]:
        """
        Match a raw extracted location against the enabled whitelist.

        Checks if the raw location starts with any whitelist entry.
        Returns the exact whitelist entry as the canonical location name.

        Args:
            raw_location: Raw location string extracted from PDF

        Returns:
            The matched whitelist location name, or None if no match
        """
        # Check whitelist (startswith matching)
        # Whitelist is sorted longest-first, so most specific match wins
        for location_name in self._location_whitelist:
            if raw_location.startswith(location_name):
                return location_name

        return None

    def create_schedule_rows(self, events: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Create two rows for each event (Setup Ready By and Closing).

        Args:
            events: List of event dictionaries

        Returns:
            List of row dictionaries for the schedule
        """
        logger.info("Creating schedule rows...")
        rows = []

        for event in events:
            # Setup Ready By row
            rows.append({
                "Event Name": event["event_name"],
                "Location": event["location"],
                "Activity": "Setup Ready By",
                "Time": event["setup_time"]
            })

            # Closing row
            rows.append({
                "Event Name": event["event_name"],
                "Location": event["location"],
                "Activity": "Closing",
                "Time": event["closing_time"]
            })

        logger.info(f"Created {len(rows)} schedule rows from {len(events)} events")
        return rows

    def create_gantt_rows(self, events: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Create single-row events for the Gantt chart.
        Each event becomes: Location, StartTime (24h), EndTime (24h)

        Args:
            events: List of event dictionaries with setup_time and closing_time

        Returns:
            List of row dictionaries with Location, StartTime, EndTime

        Example:
            >>> events = [{
            ...     "event_name": "Test Event",
            ...     "location": "UC 1227",
            ...     "setup_time": "1:30 AM",
            ...     "closing_time": "2:00 PM"
            ... }]
            >>> rows = processor.create_gantt_rows(events)
            >>> rows[0]
            {'Location': 'UC 1227', 'StartTime': '01:30', 'EndTime': '14:00'}
        """
        logger.info("Creating Gantt event rows...")
        rows = []

        for event in events:
            # Parse setup time to get reference hour for midnight crossing
            setup_dt = self.parse_time(event["setup_time"])
            if not setup_dt:
                logger.warning(f"Skipping event '{event['event_name']}' - invalid setup time")
                continue

            start_time_24h = self.convert_to_24hour(event["setup_time"])
            end_time_24h = self.convert_to_24hour(event["closing_time"], setup_dt.hour)

            if not start_time_24h or not end_time_24h:
                logger.warning(f"Skipping event '{event['event_name']}' - time conversion failed")
                continue

            rows.append({
                "Location": event["location"],
                "StartTime": start_time_24h,
                "EndTime": end_time_24h
            })

        logger.info(f"Created {len(rows)} Gantt event rows from {len(events)} events")
        return rows

    def sort_chronologically(self, rows: List[Dict[str, str]]) -> pd.DataFrame:
        """
        Sort rows chronologically by time and create DataFrame.

        Args:
            rows: List of row dictionaries

        Returns:
            Sorted pandas DataFrame
        """
        logger.info("Sorting rows chronologically...")

        if not rows:
            logger.warning("No rows to sort")
            return pd.DataFrame(columns=["Event Name", "Location", "Activity", "Time"])

        df = pd.DataFrame(rows)

        # Create a datetime column for sorting
        df["_sort_time"] = df["Time"].apply(self.parse_time)

        # Log and remove rows where time couldn't be parsed
        invalid_mask = df["_sort_time"].isna()
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} rows with invalid times:")
            for idx, row in df[invalid_mask].iterrows():
                logger.warning(f"  - Event: '{row['Event Name']}', Activity: {row['Activity']}, Time: '{row['Time']}'")
            df = df.dropna(subset=["_sort_time"])

        # Sort by time
        df = df.sort_values("_sort_time")

        # Drop the sorting column
        df = df.drop(columns=["_sort_time"])

        # Reset index
        df = df.reset_index(drop=True)

        logger.info(f"Final schedule has {len(df)} rows")
        return df
    
    def process(self) -> pd.DataFrame:
        """
        Main processing method - orchestrates the entire workflow.

        Returns:
            Processed DataFrame with schedule
        """
        logger.info("="*60)
        logger.info("Starting report processing")
        logger.info("="*60)

        # Extract text from PDF
        text = self.extract_text_from_pdf()

        # Parse events
        events = self.extract_events(text)
        self._events = events  # Store for Gantt chart

        if not events:
            logger.warning("No valid events found in the PDF")
            return pd.DataFrame(columns=["Event Name", "Location", "Activity", "Time"])

        # Create schedule rows
        rows = self.create_schedule_rows(events)

        # Sort chronologically
        df = self.sort_chronologically(rows)

        logger.info("="*60)
        logger.info("Processing complete!")
        logger.info("="*60)

        return df

    def save_to_excel(self, df: pd.DataFrame, output_path: Optional[str] = None):
        """
        Save DataFrame to Excel file.

        Args:
            df: DataFrame to save
            output_path: Output file path (auto-generated if None)
        """
        if output_path is None:
            output_path = self.get_output_basename() + "_schedule.xlsx"

        output_path = Path(output_path)

        try:
            df.to_excel(output_path, index=False, engine="openpyxl")
            logger.info(f"Saved Excel file: {output_path}")
        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            raise

    def save_to_csv(self, df: pd.DataFrame, output_path: Optional[str] = None):
        """
        Save DataFrame to CSV file.

        Args:
            df: DataFrame to save
            output_path: Output file path (auto-generated if None)
        """
        if output_path is None:
            output_path = self.get_output_basename() + "_schedule.csv"

        output_path = Path(output_path)

        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Saved CSV file: {output_path}")
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Extract event schedules from Daily Setup Report PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s report.pdf
  %(prog)s report.pdf -o schedule.xlsx
  %(prog)s report.pdf --csv --excel
  %(prog)s report.pdf --output custom_name.xlsx --verbose
        """
    )

    parser.add_argument(
        "pdf_file",
        help="Path to the PDF file to process"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (auto-generated if not specified)"
    )

    parser.add_argument(
        "--excel",
        action="store_true",
        default=True,
        help="Generate Excel output (default: True)"
    )

    parser.add_argument(
        "--csv",
        action="store_true",
        help="Generate CSV output (default: False)"
    )

    parser.add_argument(
        "--no-excel",
        action="store_true",
        help="Disable Excel output"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to location config JSON file (default: location_config.json in project directory)"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Initialize processor
        processor = SetupReportProcessor(args.pdf_file, config_path=args.config)

        # Process the PDF
        df = processor.process()

        # Display summary
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Total events found: {len(df) // 2}")
        print(f"Total schedule entries: {len(df)}")

        if len(df) > 0:
            print("\nFirst 5 entries:")
            print(df.head().to_string(index=False))
            print("\nLast 5 entries:")
            print(df.tail().to_string(index=False))

        # Save output files
        if not args.no_excel:
            excel_path = args.output if args.output and args.output.endswith(".xlsx") else None
            processor.save_to_excel(df, excel_path)

        if args.csv:
            csv_path = args.output if args.output and args.output.endswith(".csv") else None
            processor.save_to_csv(df, csv_path)

        print("\n" + "="*60)
        print("SUCCESS! Check the output files.")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
