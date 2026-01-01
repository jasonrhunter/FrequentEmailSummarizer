"""Tests for date_parser module."""

from datetime import datetime, timedelta

import pytest

from frequent_email_summarizer.date_parser import parse_date_range


class TestParseDateRange:
    """Tests for parse_date_range function."""

    def test_last_n_days(self):
        """Test parsing 'last N days' format."""
        start, end = parse_date_range("last 7 days")

        now = datetime.now()
        expected_start = now - timedelta(days=7)

        # Check start is approximately 7 days ago (within a minute)
        assert abs((start - expected_start).total_seconds()) < 60
        # Check end is approximately now
        assert abs((end - now).total_seconds()) < 60

    def test_last_week(self):
        """Test parsing 'last week' format."""
        start, end = parse_date_range("last week")

        now = datetime.now()
        expected_start = now - timedelta(weeks=1)

        assert abs((start - expected_start).total_seconds()) < 60

    def test_past_month(self):
        """Test parsing 'past month' format."""
        start, end = parse_date_range("the past month")

        now = datetime.now()
        # Approximately 30 days
        assert (now - start).days >= 28
        assert (now - start).days <= 32

    def test_from_to_format(self):
        """Test parsing 'from X to Y' format."""
        start, end = parse_date_range("from december 1 to december 15")

        # Both should be valid datetimes
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        # End should be after start
        assert end >= start

    def test_invalid_range_raises_error(self):
        """Test that invalid ranges raise ValueError."""
        with pytest.raises(ValueError):
            parse_date_range("not a valid date range xyz123")

    def test_yesterday(self):
        """Test parsing 'yesterday' format."""
        start, end = parse_date_range("yesterday")

        now = datetime.now()
        # Start should be approximately 1 day ago
        assert (now - start).days <= 2

    def test_case_insensitive(self):
        """Test that parsing is case insensitive."""
        start1, _ = parse_date_range("Last 7 Days")
        start2, _ = parse_date_range("LAST 7 DAYS")
        start3, _ = parse_date_range("last 7 days")

        # All should parse to approximately the same time
        assert abs((start1 - start2).total_seconds()) < 60
        assert abs((start2 - start3).total_seconds()) < 60

    def test_extra_whitespace(self):
        """Test that extra whitespace is handled."""
        start, end = parse_date_range("  last 7 days  ")

        now = datetime.now()
        expected_start = now - timedelta(days=7)
        assert abs((start - expected_start).total_seconds()) < 60
