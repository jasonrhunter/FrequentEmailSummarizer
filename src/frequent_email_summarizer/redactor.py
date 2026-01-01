"""Redact personally identifying information (PII) from text."""

import re
from typing import Set


# Patterns for common PII - order matters for overlapping patterns
# More specific patterns should be checked first
PATTERNS = [
    # Credit card numbers (16 digits, various separators) - check before phone
    ("credit_card", re.compile(
        r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b"
    )),
    # Social Security Numbers - check before phone
    ("ssn", re.compile(
        r"\b\d{3}[-.\s]\d{2}[-.\s]\d{4}\b"
    )),
    # Bank account numbers (with keyword context)
    ("bank_account", re.compile(
        r"\b(?:account|acct)\.?\s*#?\s*\d{8,17}\b",
        re.IGNORECASE
    )),
    # Routing numbers
    ("routing_number", re.compile(
        r"\b(?:routing|ABA)\.?\s*#?\s*\d{9}\b",
        re.IGNORECASE
    )),
    # Email addresses
    ("email", re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )),
    # Phone numbers (more specific pattern)
    ("phone", re.compile(
        r"(?<!\d)"  # Not preceded by digit
        r"(?:\+?1[-.\s])?"  # Optional country code
        r"\(?\d{3}\)?[-.\s]?"  # Area code
        r"\d{3}[-.\s]?\d{4}"  # Main number
        r"(?:\s*(?:ext|x|extension)\.?\s*\d+)?"  # Optional extension
        r"(?!\d)"  # Not followed by digit
    )),
    # IP addresses
    ("ip_address", re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )),
    # Street addresses (basic US format)
    ("street_address", re.compile(
        r"\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Place|Pl)\.?\s*(?:#\s*\d+|Suite\s*\d+|Apt\.?\s*\d+)?\b",
        re.IGNORECASE
    )),
    # ZIP codes (US) - with word boundary
    ("zip_code", re.compile(
        r"(?<![0-9-])\b\d{5}(?:-\d{4})?\b(?![0-9-])"
    )),
    # Dates of birth patterns (various formats)
    ("dob", re.compile(
        r"\b(?:DOB|Date of Birth|Birthday|Born)[:\s]+\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
        re.IGNORECASE
    )),
    # Driver's license (varies by state, generic pattern)
    ("drivers_license", re.compile(
        r"\b(?:DL|Driver'?s?\s*License|License\s*#?)\.?\s*#?\s*[A-Z0-9]{6,15}\b",
        re.IGNORECASE
    )),
    # Passport numbers
    ("passport", re.compile(
        r"\b(?:Passport)\.?\s*#?\s*[A-Z0-9]{6,12}\b",
        re.IGNORECASE
    )),
]

# Replacement text for each PII type
REDACTION_MARKERS = {
    "email": "[EMAIL REDACTED]",
    "phone": "[PHONE REDACTED]",
    "ssn": "[SSN REDACTED]",
    "credit_card": "[CARD REDACTED]",
    "ip_address": "[IP REDACTED]",
    "street_address": "[ADDRESS REDACTED]",
    "zip_code": "[ZIP REDACTED]",
    "dob": "[DOB REDACTED]",
    "bank_account": "[ACCOUNT REDACTED]",
    "routing_number": "[ROUTING REDACTED]",
    "drivers_license": "[LICENSE REDACTED]",
    "passport": "[PASSPORT REDACTED]",
}


def redact_pii(text: str, preserve_emails: Set[str] | None = None) -> str:
    """
    Redact personally identifying information from text.

    Args:
        text: The text to redact PII from
        preserve_emails: Set of email addresses to NOT redact (e.g., known sender)

    Returns:
        Text with PII replaced by redaction markers
    """
    if preserve_emails is None:
        preserve_emails = set()

    # Normalize preserved emails to lowercase for comparison
    preserve_emails_lower = {e.lower() for e in preserve_emails}

    result = text

    for pii_type, pattern in PATTERNS:
        if pii_type == "email":
            # Special handling for emails - preserve known ones
            def replace_email(match):
                email = match.group(0)
                if email.lower() in preserve_emails_lower:
                    return email
                return REDACTION_MARKERS["email"]

            result = pattern.sub(replace_email, result)
        else:
            result = pattern.sub(REDACTION_MARKERS[pii_type], result)

    return result
