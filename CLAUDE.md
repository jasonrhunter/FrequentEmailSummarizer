# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FrequentEmailSummarizer is a Python 3.13 application that summarizes emails from Gmail accounts. It supports natural language date ranges (e.g., "last 7 days", "from last Tuesday to Friday", "the past month") and can filter by multiple senders.

## Development Environment

- Python virtual environment located at `.venv/`
- Install dependencies: `.venv/bin/pip install -r requirements.txt`
- Install package in dev mode: `.venv/bin/pip install -e .`

## Commands

```bash
# Run the application (output to file for development)
.venv/bin/python -m frequent_email_summarizer --range "last 7 days" --senders "sender@example.com" --output summary.html

# Run the application (send email)
.venv/bin/python -m frequent_email_summarizer --range "last 7 days" --senders "sender@example.com" --to "recipient@example.com"

# Run all tests
.venv/bin/pytest

# Run a single test file
.venv/bin/pytest tests/test_summarizer.py

# Run a specific test
.venv/bin/pytest tests/test_summarizer.py::test_function_name

# Lint and format
.venv/bin/black .
.venv/bin/flake8
.venv/bin/mypy src/
```

## Architecture

- `src/frequent_email_summarizer/` - Main package
  - `main.py` - Entry point, CLI argument parsing, orchestration
  - `gmail_client.py` - Gmail API integration for fetching and sending emails
  - `date_parser.py` - Natural language date range parsing (uses dateparser)
  - `summarizer.py` - LLM summarization (calls LM Studio via OpenAI-compatible API)
  - `redactor.py` - PII redaction before sending to LLM
  - `formatter.py` - Formats HTML output with summary and appendix
- `tests/` - Test suite mirroring src structure

### Data Flow

1. CLI parses arguments (date range, senders)
2. DateParser converts natural language range to start/end timestamps
3. GmailClient authenticates via OAuth and fetches emails from specified senders within the date range
4. Redactor removes PII from email content before sending to LM Studio
5. Summarizer processes emails and generates summaries with links to originals
6. Output formatter assembles final document with summary and appendix

### Privacy

Before sending email content to the LLM for summarization, the redactor module removes personally identifying information (PII) including:
- Email addresses (except the known sender)
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- Street addresses and ZIP codes
- Bank account and routing numbers
- Driver's license and passport numbers

The original unredacted emails are preserved in the appendix of the output document.

### Output Format

The generated summary document contains two main sections:

1. **Summary Section** - Condensed summary with inline links (e.g., `[1]`, `[2]`) referencing specific emails in the appendix
2. **Appendix** - Full original emails grouped by sender, each with an anchor ID for linking

Example structure:
```
## Summary
John sent 3 updates about the project timeline [1][2][3]. Jane requested budget approval [4]...

## Appendix

### John Smith (john@example.com)
[1] Subject: Project Update - Mon Dec 18
Full email content...

[2] Subject: Re: Project Update - Tue Dec 19
Full email content...

### Jane Doe (jane@example.com)
[4] Subject: Budget Request - Wed Dec 20
Full email content...
```

## Configuration

Environment variables:
- `LM_STUDIO_URL` - LM Studio API URL (default: `http://localhost:1234/v1`)
- `LM_STUDIO_MODEL` - Model name to use in LM Studio (required)

Files:
- `credentials.json` - OAuth client ID from Google Cloud Console (required for first run)
- `token.json` - Stored refresh token (auto-generated after OAuth flow)

### Gmail Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Desktop application)
3. Download the JSON and save as `credentials.json` in the project root
4. On first run, a browser will open for OAuth authorization
