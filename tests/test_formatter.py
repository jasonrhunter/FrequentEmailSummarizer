"""Tests for formatter module."""

from datetime import datetime

from frequent_email_summarizer.formatter import format_email, _linkify_references
from frequent_email_summarizer.gmail_client import Email


def make_email(
    id: str = "123",
    sender: str = "test@example.com",
    sender_name: str = "Test User",
    subject: str = "Test Subject",
    body: str = "Test body content",
    date: datetime = None,
) -> Email:
    """Helper to create Email objects for testing."""
    return Email(
        id=id,
        sender=sender,
        sender_name=sender_name,
        subject=subject,
        body=body,
        date=date or datetime.now(),
    )


class TestLinkifyReferences:
    """Tests for _linkify_references function."""

    def test_single_reference(self):
        """Test converting a single reference."""
        result = _linkify_references("See email [1] for details")
        assert 'href="#email-1"' in result
        assert ">[1]</a>" in result

    def test_multiple_references(self):
        """Test converting multiple references."""
        result = _linkify_references("See [1], [2], and [3]")
        assert 'href="#email-1"' in result
        assert 'href="#email-2"' in result
        assert 'href="#email-3"' in result

    def test_no_references(self):
        """Test text without references."""
        result = _linkify_references("No references here")
        assert "href" not in result
        assert "No references here" in result


class TestFormatEmail:
    """Tests for format_email function."""

    def test_basic_structure(self):
        """Test that output has required sections."""
        emails = [make_email()]
        summary = "This is the summary [1]"

        result = format_email(summary, emails, "last 7 days")

        assert "<!DOCTYPE html>" in result
        assert "<h1>Email Summary</h1>" in result
        assert "Appendix" in result
        assert "last 7 days" in result

    def test_emails_grouped_by_sender(self):
        """Test that emails are grouped by sender."""
        emails = [
            make_email(id="1", sender="alice@example.com", sender_name="Alice", subject="First"),
            make_email(id="2", sender="bob@example.com", sender_name="Bob", subject="Second"),
            make_email(id="3", sender="alice@example.com", sender_name="Alice", subject="Third"),
        ]
        summary = "Test summary"

        result = format_email(summary, emails, "last week")

        # Check both senders appear
        assert "alice@example.com" in result
        assert "bob@example.com" in result

    def test_reference_links_created(self):
        """Test that reference markers become clickable links."""
        emails = [make_email()]
        summary = "Check this email [1]"

        result = format_email(summary, emails, "last 7 days")

        assert 'href="#email-1"' in result
        assert 'id="email-1"' in result

    def test_html_escaping(self):
        """Test that special characters are escaped."""
        emails = [make_email(subject="<script>alert('xss')</script>", body="Body with <tags>")]
        summary = "Summary"

        result = format_email(summary, emails, "last 7 days")

        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_empty_emails(self):
        """Test handling of empty email list."""
        result = format_email("No emails found", [], "last 7 days")

        assert "Email Summary" in result
        assert "No emails found" in result

    def test_email_metadata_included(self):
        """Test that email metadata is included in appendix."""
        date = datetime(2024, 1, 15, 10, 30)
        emails = [
            make_email(
                sender="test@example.com",
                sender_name="Test User",
                subject="Important Subject",
                date=date,
            )
        ]

        result = format_email("Summary", emails, "last week")

        assert "Test User" in result
        assert "test@example.com" in result
        assert "Important Subject" in result
        assert "Jan 15" in result or "15" in result
