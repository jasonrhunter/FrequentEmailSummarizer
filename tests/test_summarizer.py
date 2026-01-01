"""Tests for summarizer module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from frequent_email_summarizer.gmail_client import Email
from frequent_email_summarizer.summarizer import Summarizer


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


class TestSummarizer:
    """Tests for Summarizer class."""

    def test_init_requires_model(self):
        """Test that initialization requires a model name."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="Model name required"):
                Summarizer()

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict("os.environ", {"LM_STUDIO_MODEL": "test-model"}):
            summarizer = Summarizer()
            assert summarizer.model == "test-model"

    def test_init_with_parameter(self):
        """Test initialization with explicit parameter."""
        summarizer = Summarizer(model="my-model")
        assert summarizer.model == "my-model"

    def test_summarize_empty_list(self):
        """Test summarizing empty email list."""
        summarizer = Summarizer(model="test-model")
        result = summarizer.summarize([])
        assert result == "No emails to summarize."

    def test_summarize_calls_api_for_each_email(self):
        """Test that summarize calls the LLM API for each email plus combining."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary text"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("frequent_email_summarizer.summarizer.OpenAI", return_value=mock_client):
            summarizer = Summarizer(model="test-model")
            emails = [
                make_email(id="1", subject="Email 1"),
                make_email(id="2", subject="Email 2"),
            ]

            result = summarizer.summarize(emails)

            # Should be called 3 times: once for each email + once for combining
            assert mock_client.chat.completions.create.call_count == 3

    def test_summarize_creates_fresh_client_per_email(self):
        """Test that a fresh client is created for each email to avoid context issues."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary text"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("frequent_email_summarizer.summarizer.OpenAI", return_value=mock_client) as mock_openai:
            summarizer = Summarizer(model="test-model")
            emails = [
                make_email(id="1", subject="Email 1"),
                make_email(id="2", subject="Email 2"),
            ]

            summarizer.summarize(emails)

            # OpenAI client should be created 3 times: once per email + once for combining
            assert mock_openai.call_count == 3

    def test_summarize_with_progress_callback(self):
        """Test that progress callback is called for each email."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        progress_calls = []

        def track_progress(current, total):
            progress_calls.append((current, total))

        with patch("frequent_email_summarizer.summarizer.OpenAI", return_value=mock_client):
            summarizer = Summarizer(model="test-model")
            emails = [make_email(id="1"), make_email(id="2"), make_email(id="3")]

            summarizer.summarize(emails, progress_callback=track_progress)

            assert progress_calls == [(1, 3), (2, 3), (3, 3)]

    def test_single_email_summary_includes_sender(self):
        """Test that individual email summaries include sender name."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Email summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("frequent_email_summarizer.summarizer.OpenAI", return_value=mock_client):
            summarizer = Summarizer(model="test-model")
            email = make_email(sender_name="John Smith", subject="Test")

            result = summarizer._summarize_single_email(email, 1)

            assert "[1]" in result
            assert "John Smith" in result

    def test_long_email_body_truncated(self):
        """Test that long email bodies are truncated."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("frequent_email_summarizer.summarizer.OpenAI", return_value=mock_client):
            summarizer = Summarizer(model="test-model")
            # Create email with very long body
            long_body = "x" * 10000
            email = make_email(body=long_body)

            summarizer._summarize_single_email(email, 1)

            # Check that the API was called with truncated content
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs["messages"][1]["content"]
            assert "[... email truncated for length ...]" in user_message
