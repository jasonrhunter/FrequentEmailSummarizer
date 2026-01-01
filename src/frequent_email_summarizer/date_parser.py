"""Parse natural language date ranges into start and end datetime objects."""

import re
from datetime import datetime, timedelta
from typing import Tuple

import dateparser


def parse_date_range(range_str: str) -> Tuple[datetime, datetime]:
    """
    Parse a natural language date range string into start and end datetimes.

    Supported formats:
    - "last 7 days", "past week", "last month"
    - "from Monday to Friday", "from last Tuesday to Thursday"
    - "yesterday", "last week"

    Args:
        range_str: Natural language date range string

    Returns:
        Tuple of (start_datetime, end_datetime)

    Raises:
        ValueError: If the date range cannot be parsed
    """
    range_str = range_str.strip().lower()
    now = datetime.now()

    # Handle "from X to Y" pattern
    from_to_match = re.match(r"from\s+(.+?)\s+to\s+(.+)", range_str, re.IGNORECASE)
    if from_to_match:
        start_str, end_str = from_to_match.groups()
        start = _parse_single_date(start_str)
        end = _parse_single_date(end_str)

        if start is None:
            raise ValueError(f"Could not parse start date: '{start_str}'")
        if end is None:
            raise ValueError(f"Could not parse end date: '{end_str}'")

        # Set end to end of day
        end = end.replace(hour=23, minute=59, second=59)
        return start, end

    # Handle relative ranges like "last 7 days", "past month"
    relative_match = re.match(r"(?:the\s+)?(?:last|past)\s+(\d+)?\s*(\w+)", range_str)
    if relative_match:
        count_str, unit = relative_match.groups()
        count = int(count_str) if count_str else 1

        unit = unit.rstrip("s")  # Normalize: days -> day
        if unit in ("day",):
            start = now - timedelta(days=count)
        elif unit in ("week",):
            start = now - timedelta(weeks=count)
        elif unit in ("month",):
            start = now - timedelta(days=count * 30)
        elif unit in ("year",):
            start = now - timedelta(days=count * 365)
        else:
            # Try dateparser for other cases
            start = _parse_single_date(range_str)
            if start is None:
                raise ValueError(f"Could not parse date range: '{range_str}'")
            return start, now

        return start, now

    # Fall back to dateparser for single date expressions
    start = _parse_single_date(range_str)
    if start is None:
        raise ValueError(f"Could not parse date range: '{range_str}'")

    return start, now


def _parse_single_date(date_str: str) -> datetime | None:
    """
    Parse a single date string using dateparser.

    Args:
        date_str: Natural language date string

    Returns:
        Parsed datetime or None if parsing failed
    """
    settings = {
        "PREFER_DATES_FROM": "past",
        "RELATIVE_BASE": datetime.now(),
    }
    return dateparser.parse(date_str, settings=settings)
