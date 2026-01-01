"""Format email summary with appendix into HTML."""

import html
import re
from collections import defaultdict
from typing import List

import markdown

from .gmail_client import Email


def format_email(summary: str, emails: List[Email], date_range: str) -> str:
    """
    Format the summary and original emails into an HTML document.

    The output contains:
    1. A summary section with clickable reference links
    2. An appendix with original emails grouped by sender

    Args:
        summary: The generated summary text with [N] reference markers
        emails: List of original Email objects
        date_range: The date range string used for the query

    Returns:
        Formatted HTML string
    """
    # Convert markdown to HTML and reference markers [N] to clickable links
    summary_html = _linkify_references(summary)

    # Group emails by sender
    emails_by_sender = defaultdict(list)
    for i, email in enumerate(emails, 1):
        emails_by_sender[email.sender].append((i, email))

    # Build appendix HTML
    appendix_html = _build_appendix(emails_by_sender)

    # Assemble full document
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
        }}
        h3 {{
            color: #27ae60;
            margin-top: 25px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary p {{
            margin: 0.5em 0;
        }}
        .email-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #fff;
        }}
        .email-header {{
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        .email-meta {{
            font-size: 0.9em;
            color: #666;
        }}
        .email-subject {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .email-body {{
            white-space: pre-wrap;
            font-family: inherit;
            background-color: #fafafa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        .ref-link {{
            color: #3498db;
            text-decoration: none;
            font-weight: bold;
        }}
        .ref-link:hover {{
            text-decoration: underline;
        }}
        .date-range {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .sender-group {{
            margin-bottom: 30px;
        }}
        .sender-email {{
            color: #666;
            font-size: 0.9em;
        }}
        .back-to-top {{
            font-size: 0.8em;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>Email Summary</h1>
    <p class="date-range">Date range: {html.escape(date_range)}</p>

    <div class="summary">
        {summary_html}
    </div>

    <h2>Appendix: Original Emails</h2>
    {appendix_html}

    <p class="back-to-top"><a href="#top">Back to top</a></p>
</body>
</html>"""


def _linkify_references(text: str) -> str:
    """Convert markdown to HTML and [N] markers to clickable anchor links."""
    # First, protect reference markers from markdown processing
    # Replace [N] with a placeholder that won't be interpreted as markdown
    def protect_ref(match):
        ref_num = match.group(1)
        return f"EMAILREF{ref_num}ENDREF"

    text = re.sub(r"\[(\d+)\]", protect_ref, text)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=["extra"])
    text = md.convert(text)

    # Now replace placeholders with actual anchor links
    def replace_ref(match):
        ref_num = match.group(1)
        return f'<a href="#email-{ref_num}" class="ref-link">[{ref_num}]</a>'

    text = re.sub(r"EMAILREF(\d+)ENDREF", replace_ref, text)

    return text


def _build_appendix(emails_by_sender: dict) -> str:
    """Build the appendix HTML with emails grouped by sender."""
    sections = []

    for sender, email_list in sorted(emails_by_sender.items()):
        # Get sender display name from first email
        sender_name = email_list[0][1].sender_name or sender

        email_items = []
        for ref_num, email in email_list:
            date_str = email.date.strftime("%a, %b %d %Y at %I:%M %p")
            body_escaped = html.escape(email.body)

            email_items.append(f"""
            <div class="email-item" id="email-{ref_num}">
                <div class="email-header">
                    <span class="ref-link">[{ref_num}]</span>
                    <span class="email-subject">{html.escape(email.subject)}</span>
                </div>
                <div class="email-meta">
                    Date: {date_str}
                </div>
                <div class="email-body">{body_escaped}</div>
            </div>""")

        sections.append(f"""
        <div class="sender-group">
            <h3>{html.escape(sender_name)} <span class="sender-email">&lt;{html.escape(sender)}&gt;</span></h3>
            {"".join(email_items)}
        </div>""")

    return "".join(sections)
