"""Summarize emails using LM Studio's local LLM."""

import os
from typing import List, Callable

from openai import OpenAI

from .gmail_client import Email
from .redactor import redact_pii

DEFAULT_LM_STUDIO_URL = "http://localhost:1234/v1"

# Max characters for email body to stay within context window
# ~4 chars per token, leave room for prompt and response
MAX_EMAIL_BODY_CHARS = 8000


class Summarizer:
    """Summarize emails using a local LLM via LM Studio."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the summarizer.

        Args:
            base_url: LM Studio API URL (default: http://localhost:1234/v1)
            model: Model name to use (default: from LM_STUDIO_MODEL env var)
        """
        self.base_url = base_url or os.environ.get("LM_STUDIO_URL", DEFAULT_LM_STUDIO_URL)
        self.model = model or os.environ.get("LM_STUDIO_MODEL", "")

        if not self.model:
            raise ValueError(
                "Model name required. Set LM_STUDIO_MODEL environment variable "
                "or pass model parameter."
            )

    def _create_client(self) -> OpenAI:
        """Create a fresh OpenAI client for LM Studio.

        Creating a new client for each request helps avoid context window
        accumulation issues with LM Studio.
        """
        return OpenAI(base_url=self.base_url, api_key="not-needed")

    def summarize(
        self, emails: List[Email], progress_callback: Callable[[int, int], None] | None = None
    ) -> str:
        """
        Generate a summary of the provided emails by processing them individually.

        Each email is summarized with a fresh client session and grouped by sender.

        Args:
            emails: List of Email objects to summarize
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Markdown-formatted summary grouped by sender with reference markers
        """
        if not emails:
            return "No emails to summarize."

        # Summarize each email individually (fresh client per email)
        email_summaries = []
        for i, email in enumerate(emails, 1):
            if progress_callback:
                progress_callback(i, len(emails))

            summary = self._summarize_single_email(email, i)
            email_summaries.append((email, i, summary))

        # Group summaries by sender
        return self._format_by_sender(email_summaries)

    def _summarize_single_email(self, email: Email, ref_num: int) -> str:
        """Summarize a single email using a fresh client session."""
        # Redact PII from subject and body, preserving sender's email
        redacted_subject = redact_pii(email.subject, preserve_emails={email.sender})
        redacted_body = redact_pii(email.body, preserve_emails={email.sender})

        # Truncate long email bodies to fit within context window
        if len(redacted_body) > MAX_EMAIL_BODY_CHARS:
            redacted_body = redacted_body[:MAX_EMAIL_BODY_CHARS] + "\n\n[... email truncated for length ...]"

        system_prompt = """You are an email summarizer. Summarize the key points of this email in 2-4 concise sentences.
Focus on: main topic, any requests/action items, deadlines, highlights, and important decisions.
Include the subject and date in your summary but NOT the sender name.
Be concise but capture the essential information and highlights.
Note: Some personally identifying information has been redacted for privacy."""

        user_prompt = f"""Summarize the key content of this email in 2-4 sentences (do not include sender)

and output with the format:

Subject: <put the email subject here>
Date: <put the email date here>
Summary: <put the summary here>

Subject: {redacted_subject}
Date: {email.date}

{redacted_body} 
"""

        # Create fresh client for each email to avoid context accumulation
        client = self._create_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    def _format_by_sender(self, email_summaries: List[tuple[Email, int, str]]) -> str:
        """Format individual email summaries grouped by sender."""
        from collections import defaultdict

        # Group by sender
        by_sender = defaultdict(list)
        for email, ref_num, summary in email_summaries:
            sender_name = email.sender_name or email.sender
            by_sender[sender_name].append((ref_num, summary))

        # Build markdown output
        sections = []
        for sender_name in sorted(by_sender.keys()):
            sections.append(f"### {sender_name}\n")
            for ref_num, summary in by_sender[sender_name]:
                sections.append(f"[{ref_num}] {summary}\n")

        return "\n".join(sections)
