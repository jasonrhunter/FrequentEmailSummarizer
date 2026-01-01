"""Gmail API client for fetching and sending emails."""

import base64
import os
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


@dataclass
class Email:
    """Represents an email message."""

    id: str
    sender: str
    sender_name: str
    subject: str
    date: datetime
    body: str


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials_file: str = CREDENTIALS_FILE, token_file: str = TOKEN_FILE):
        """
        Initialize the Gmail client.

        Args:
            credentials_file: Path to OAuth credentials JSON file
            token_file: Path to store/load the auth token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth."""
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Download it from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/apis/credentials\n"
                        "2. Create an OAuth 2.0 Client ID (Desktop application)\n"
                        "3. Download the JSON and save as 'credentials.json'"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

    def fetch_emails(
        self, senders: List[str], start_date: datetime, end_date: datetime
    ) -> List[Email]:
        """
        Fetch emails from specified senders within a date range.

        Args:
            senders: List of sender email addresses
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of Email objects
        """
        emails = []

        # Build query for each sender
        sender_queries = [f"from:{sender}" for sender in senders]
        sender_query = " OR ".join(sender_queries)

        # Format dates for Gmail query
        after = start_date.strftime("%Y/%m/%d")
        before = (end_date).strftime("%Y/%m/%d")

        query = f"({sender_query}) after:{after} before:{before}"

        # Fetch message IDs
        results = (
            self.service.users().messages().list(userId="me", q=query, maxResults=500).execute()
        )

        messages = results.get("messages", [])

        for msg in messages:
            email = self._get_email_details(msg["id"])
            if email:
                emails.append(email)

        # Sort by date
        emails.sort(key=lambda e: e.date)

        return emails

    def _get_email_details(self, msg_id: str) -> Email | None:
        """
        Get full details of an email by ID.

        Args:
            msg_id: Gmail message ID

        Returns:
            Email object or None if parsing failed
        """
        msg = self.service.users().messages().get(userId="me", id=msg_id, format="full").execute()

        headers = msg.get("payload", {}).get("headers", [])

        # Extract headers
        subject = ""
        sender = ""
        sender_name = ""
        date_str = ""

        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")

            if name == "subject":
                subject = value
            elif name == "from":
                sender, sender_name = self._parse_sender(value)
            elif name == "date":
                date_str = value

        # Parse date
        date = self._parse_date(date_str)

        # Extract body
        body = self._extract_body(msg.get("payload", {}))

        return Email(
            id=msg_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            date=date,
            body=body,
        )

    def _parse_sender(self, from_header: str) -> tuple[str, str]:
        """Parse the From header into email and display name."""
        import re

        # Pattern: "Display Name <email@example.com>" or just "email@example.com"
        match = re.match(r"(?:\"?([^\"<]+)\"?\s*)?<?([^>]+@[^>]+)>?", from_header)
        if match:
            name, email = match.groups()
            name = name.strip() if name else ""
            return email.strip(), name
        return from_header, ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date header into datetime."""
        from email.utils import parsedate_to_datetime

        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()

    def _extract_body(self, payload: dict) -> str:
        """Extract the plain text body from email payload."""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                # Prefer plain text
                if mime_type == "text/plain":
                    if part.get("body", {}).get("data"):
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8", errors="ignore"
                        )

                # Recurse into multipart
                if mime_type.startswith("multipart/"):
                    body = self._extract_body(part)
                    if body:
                        return body

            # Fall back to HTML if no plain text
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html":
                    if part.get("body", {}).get("data"):
                        html = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8", errors="ignore"
                        )
                        return self._html_to_text(html)

        return ""

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (basic implementation)."""
        import re

        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Replace common elements
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)

        # Remove all other tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        import html

        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    def send_email(self, to: List[str], subject: str, html_body: str) -> None:
        """
        Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            html_body: HTML content of the email
        """
        # Get sender's email
        profile = self.service.users().getProfile(userId="me").execute()
        sender = profile["emailAddress"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(to)

        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # Encode and send
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.service.users().messages().send(userId="me", body={"raw": raw}).execute()
