# FrequentEmailSummarizer

A Python CLI application that summarizes emails from Gmail using a local LLM via LM Studio. It supports natural language date ranges and filters by sender, producing a formatted HTML summary with an appendix of original emails.

## Features

- **Natural language date ranges**: "last 7 days", "from last Tuesday to Friday", "the past month"
- **Multiple sender filtering**: Fetch emails from specific senders
- **AI-powered summarization**: Uses a local LLM via LM Studio to generate concise summaries
- **Privacy protection**: Automatically redacts PII before sending to the LLM
- **Reference linking**: Summary includes `[1]`, `[2]` links to original emails in appendix
- **Multiple output options**: Save to file or send via email

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd FrequentEmailSummarizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Configuration

### LM Studio Setup

1. Download and install LM Studio from https://lmstudio.ai/
2. Download a model (e.g., Llama, Mistral, etc.)
3. Start the local server in LM Studio (default: http://localhost:1234)
4. Set the model name: `export LM_STUDIO_MODEL="your-model-name"`

### Environment Variables

- `LM_STUDIO_URL` - LM Studio API URL (default: `http://localhost:1234/v1`)
- `LM_STUDIO_MODEL` - Model name to use in LM Studio (required)

### Gmail Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Desktop application)
3. Download the JSON and save as `credentials.json` in the project root
4. On first run, a browser will open for OAuth authorization


## Usage

```bash
# Output to file (for development/testing)
python -m frequent_email_summarizer \
  --range "last 7 days" \
  --senders "sender@example.com" \
  --output summary.html

# Send summary via email
python -m frequent_email_summarizer \
  --range "last 7 days" \
  --senders "alice@example.com,bob@example.com" \
  --to "recipient@example.com"

# With custom subject
python -m frequent_email_summarizer \
  --range "the past month" \
  --senders "newsletter@service.com" \
  --to "team@company.com" \
  --subject "Monthly Newsletter Summary"
```

## Privacy

Before sending email content to the local LLM for summarization, the application automatically redacts personally identifying information (PII) including:

- Email addresses (except the known sender)
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- Street addresses and ZIP codes
- Bank account and routing numbers

The original unredacted emails are preserved in the appendix of the output document.

## Development

```bash
# Run tests
pytest

# Run linting
black .
flake8
mypy src/
```

## License

MIT
