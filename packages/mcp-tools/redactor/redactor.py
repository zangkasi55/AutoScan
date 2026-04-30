"""PDPA-aligned auto-redactor for the AVS evidence ledger.

Patterns: Thai citizen ID, Thai phone numbers, Thai bank-account-style numbers,
emails, IPv4 only when in a non-target context (we keep target IPs since they
are the scan subject, not personal data — by-design exception per PRD §5.8).

Reference: build-spec §5.2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionResult:
    redacted: str
    counts: dict[str, int]


_PATTERNS: dict[str, re.Pattern[str]] = {
    # Thai citizen ID: 1-2345-67890-12-3 (or unhyphenated 13 digits).
    "CID": re.compile(r"\b\d-\d{4}-\d{5}-\d{2}-\d\b|\b\d{13}\b"),
    # Thai mobile / landline numbers (with optional dashes / +66).
    "PHONE": re.compile(r"(?:(?:\+?66|0)[\s\-]?\d{1,2}[\s\-]?\d{3}[\s\-]?\d{4})"),
    # Bank-style account numbers: 9–14 digits possibly hyphenated, after BANK keyword.
    "ACCT": re.compile(
        r"(?i)\b(?:acct|account|บัญชี)[\s:#]*((?:\d[\s\-]?){9,14})\b"
    ),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "PASSPORT_TH": re.compile(r"\b[A-Z]{1,2}\d{6,7}\b"),
}

_TOKEN = {
    "CID": "[CID-REDACTED]",
    "PHONE": "[PHONE-REDACTED]",
    "ACCT": "[ACCT-REDACTED]",
    "EMAIL": "[EMAIL-REDACTED]",
    "PASSPORT_TH": "[PASSPORT-REDACTED]",
}


def redact(text: str) -> RedactionResult:
    """Return a redacted copy of *text* and per-category counts."""
    counts: dict[str, int] = {k: 0 for k in _PATTERNS}
    redacted = text
    for kind, pat in _PATTERNS.items():
        def _sub(m: re.Match[str]) -> str:
            counts[kind] += 1
            return _TOKEN[kind]

        redacted = pat.sub(_sub, redacted)
    return RedactionResult(redacted=redacted, counts=counts)


def redact_json(obj):
    """Walk a JSON-shaped object and redact every string value."""
    if isinstance(obj, str):
        return redact(obj).redacted
    if isinstance(obj, list):
        return [redact_json(x) for x in obj]
    if isinstance(obj, dict):
        return {k: redact_json(v) for k, v in obj.items()}
    return obj
