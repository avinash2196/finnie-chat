import re

# Compiled patterns for common PII and sensitive data.
# Using precompiled regexes avoids repeated compilation on every request.
_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ssn",            re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")),
    ("credit_card",    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b")),
    ("routing_number", re.compile(r"\b\d{9}\b")),
    ("email",          re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("phone",          re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("account_number", re.compile(r"\b(?:account\s*(?:number|#|num)\s*[:\-]?\s*\d{4,17}|\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4})\b", re.IGNORECASE)),
]

# Literal blocked phrases (case-insensitive substring match).
_BLOCKED_PHRASES: tuple[str, ...] = ("my ssn is", "account number", "routing number", "bank password")


def input_guardrails(message: str):
    """
    Reject messages that contain PII or sensitive financial data.

    Returns (True, message) when clean, (False, reason) when blocked.
    Runs in O(n * p) where n = message length, p = number of patterns.
    """
    lower = message.lower()

    for phrase in _BLOCKED_PHRASES:
        if phrase in lower:
            return False, "Message contains sensitive information. Please avoid sharing personal financial data."

    for label, pattern in _PII_PATTERNS:
        if pattern.search(message):
            return False, f"Message appears to contain sensitive information ({label}). Please avoid sharing personal data."

    return True, message


def output_guardrails(text: str, risk_level: str):
    if risk_level == "HIGH":
        return (
            "I can’t provide direct investment instructions. "
            "I can explain concepts or help you understand options instead.\n\n"
            + text
        )
    return text
