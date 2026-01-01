"""Tests for redactor module."""

import pytest

from frequent_email_summarizer.redactor import redact_pii


class TestRedactPii:
    """Tests for redact_pii function."""

    def test_redacts_email_addresses(self):
        """Test that email addresses are redacted."""
        text = "Contact me at john.doe@example.com for more info."
        result = redact_pii(text)
        assert "john.doe@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_preserves_specified_emails(self):
        """Test that specified emails are preserved."""
        text = "From sender@company.com: Please contact other@example.com"
        result = redact_pii(text, preserve_emails={"sender@company.com"})
        assert "sender@company.com" in result
        assert "other@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_redacts_phone_numbers(self):
        """Test various phone number formats are redacted."""
        texts = [
            "Call me at 555-123-4567",
            "Phone: (555) 123-4567",
            "Reach me at 555.123.4567",
            "Call +1 555-123-4567",
            "Phone: 555 123 4567 ext 123",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[PHONE REDACTED]" in result, f"Failed for: {text}"

    def test_redacts_ssn(self):
        """Test that SSN patterns are redacted."""
        texts = [
            "SSN: 123-45-6789",
            "Social: 123.45.6789",
            "SSN 123 45 6789",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[SSN REDACTED]" in result, f"Failed for: {text}"

    def test_redacts_credit_card(self):
        """Test that credit card numbers are redacted."""
        texts = [
            "Card: 1234-5678-9012-3456",
            "CC: 1234 5678 9012 3456",
            "Payment: 1234567890123456",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[CARD REDACTED]" in result, f"Failed for: {text}"

    def test_redacts_ip_addresses(self):
        """Test that IP addresses are redacted."""
        text = "Server IP: 192.168.1.100"
        result = redact_pii(text)
        assert "192.168.1.100" not in result
        assert "[IP REDACTED]" in result

    def test_redacts_street_addresses(self):
        """Test that street addresses are redacted."""
        texts = [
            "Send to 123 Main Street",
            "Address: 456 Oak Ave",
            "Located at 789 Broadway Blvd Suite 100",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[ADDRESS REDACTED]" in result, f"Failed for: {text}"

    def test_redacts_zip_codes(self):
        """Test that ZIP codes are redacted."""
        texts = [
            "ZIP: 12345",
            "Postal code: 12345-6789",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[ZIP REDACTED]" in result, f"Failed for: {text}"

    def test_redacts_bank_account(self):
        """Test that bank account numbers are redacted."""
        texts = [
            "Account #12345678901",
            "Acct. 987654321012",
        ]
        for text in texts:
            result = redact_pii(text)
            assert "[ACCOUNT REDACTED]" in result, f"Failed for: {text}"

    def test_preserves_non_pii_text(self):
        """Test that regular text is not affected."""
        text = "Hello, this is a regular email about the project status."
        result = redact_pii(text)
        assert result == text

    def test_handles_empty_string(self):
        """Test that empty string is handled."""
        result = redact_pii("")
        assert result == ""

    def test_multiple_pii_types(self):
        """Test redaction of multiple PII types in one text."""
        text = """
        Contact John at john@example.com or call 555-123-4567.
        His SSN is 123-45-6789 and he lives at 100 Main Street.
        """
        result = redact_pii(text)
        assert "[EMAIL REDACTED]" in result
        assert "[PHONE REDACTED]" in result
        assert "[SSN REDACTED]" in result
        assert "[ADDRESS REDACTED]" in result
        assert "Contact John" in result  # Non-PII preserved

    def test_case_insensitive_email_preservation(self):
        """Test that email preservation is case-insensitive."""
        text = "From SENDER@COMPANY.COM to recipient@other.com"
        result = redact_pii(text, preserve_emails={"sender@company.com"})
        assert "SENDER@COMPANY.COM" in result
        assert "recipient@other.com" not in result
