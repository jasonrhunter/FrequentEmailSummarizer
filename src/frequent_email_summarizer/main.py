"""Main CLI entry point for FrequentEmailSummarizer."""

import argparse
import sys
from typing import List

from .date_parser import parse_date_range
from .formatter import format_email
from .gmail_client import Email, GmailClient
from .summarizer import Summarizer


def generate_subject(emails: List[Email], date_range: str) -> str:
    """Generate an email subject from sender names and date range."""
    # Get unique sender names, preferring full names over email addresses
    sender_names = []
    seen = set()
    for email in emails:
        name = email.sender_name or email.sender
        if name not in seen:
            seen.add(name)
            sender_names.append(name)

    # Format sender list
    if len(sender_names) == 1:
        senders_str = sender_names[0]
    elif len(sender_names) == 2:
        senders_str = f"{sender_names[0]} and {sender_names[1]}"
    elif len(sender_names) <= 4:
        senders_str = ", ".join(sender_names[:-1]) + f", and {sender_names[-1]}"
    else:
        senders_str = ", ".join(sender_names[:3]) + f", and {len(sender_names) - 3} others"

    return f"Summary of {senders_str} for {date_range}"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Summarize emails from Gmail and send a formatted summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --range "last 7 days" --senders "boss@company.com" --output summary.html
  %(prog)s --range "from Monday to Friday" --senders "alice@example.com,bob@example.com" --to "me@example.com"
  %(prog)s --range "the past month" --senders "newsletter@service.com" --to "team@company.com" --subject "Monthly Newsletter Summary"
        """,
    )

    parser.add_argument(
        "--range",
        "-r",
        required=True,
        help='Natural language date range (e.g., "last 7 days", "from Monday to Friday")',
    )

    parser.add_argument(
        "--senders",
        "-s",
        required=True,
        help="Comma-separated list of sender email addresses to include",
    )

    parser.add_argument(
        "--to",
        "-t",
        help="Comma-separated list of recipient email addresses",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (for local development/debugging)",
    )

    parser.add_argument(
        "--subject",
        default=None,
        help="Email subject line (default: auto-generated from sender names and date range)",
    )

    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to Google OAuth credentials file (default: credentials.json)",
    )

    parser.add_argument(
        "--token",
        default="token.json",
        help="Path to store/load auth token (default: token.json)",
    )

    args = parser.parse_args()

    # Validate: need either --to or --output
    if not args.to and not args.output:
        parser.error("Either --to (send email) or --output (save to file) is required")

    # Parse senders
    senders = [s.strip() for s in args.senders.split(",")]

    # Parse date range
    try:
        start_date, end_date = parse_date_range(args.range)
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    except ValueError as e:
        print(f"Error parsing date range: {e}", file=sys.stderr)
        return 1

    # Initialize Gmail client
    try:
        print("Authenticating with Gmail...")
        gmail = GmailClient(credentials_file=args.credentials, token_file=args.token)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Fetch emails
    print(f"Fetching emails from {len(senders)} sender(s)...")
    emails = gmail.fetch_emails(senders, start_date, end_date)
    print(f"Found {len(emails)} email(s)")

    if not emails:
        print("No emails found matching the criteria.")
        return 0

    # Summarize
    print("Generating summary...")
    try:
        summarizer = Summarizer()

        def show_progress(current: int, total: int) -> None:
            print(f"  Summarizing email {current}/{total}...", end="\r")

        summary = summarizer.summarize(emails, progress_callback=show_progress)
        print(f"Summarized {len(emails)} email(s)        ")  # Clear the progress line
        print("Combining into final summary...")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calling LM Studio API: {e}", file=sys.stderr)
        return 1

    # Format output
    html_output = format_email(summary, emails, args.range)

    # Output results
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"Summary saved to: {args.output}")

    if args.to:
        recipients = [r.strip() for r in args.to.split(",")]
        # Generate subject if not provided
        subject = args.subject or generate_subject(emails, args.range)
        print(f"Sending email to {len(recipients)} recipient(s)...")
        print(f"Subject: {subject}")
        gmail.send_email(recipients, subject, html_output)
        print("Email sent successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
