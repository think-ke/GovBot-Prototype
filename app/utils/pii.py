"""
PII detection and redaction utilities.

This module preserves the simple detect/redact API used across the codebase
while delegating to Microsoft Presidio for robust detection/anonymization when
available. If Presidio isn't available at runtime, it falls back to lightweight
regex-based heuristics for minimal protection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Tuple

try:
    from app.utils.presidio_pii import analyze_text, redact_text
    _PRESIDIO_AVAILABLE = True
except Exception:  # pragma: no cover - runtime fallback
    analyze_text = None  # type: ignore
    redact_text = None  # type: ignore
    _PRESIDIO_AVAILABLE = False


@dataclass
class PIIMatch:
    kind: str
    match: str
    start: int
    end: int


def _compile_patterns() -> Dict[str, Pattern[str]]:
    """Compile regex patterns for PII detection.

    Patterns are intentionally conservative to reduce false positives.
    """
    return {
        # Basic email
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        # Kenyan phone formats (e.g., +2547XXXXXXXX, 07XXXXXXXX, 01XXXXXXXX)
        "phone": re.compile(r"\b(?:\+?254|0)(?:7|1)\d{8}\b"),
        # National ID: commonly 7 or 8 digits (heuristic)
        "national_id": re.compile(r"\b\d{7,8}\b"),
        # Passport: alphanumeric 6-9 chars (heuristic)
        "passport": re.compile(r"\b[A-Za-z0-9]{6,9}\b"),
    }


_PATTERNS = _compile_patterns()


def detect_pii(text: str) -> List[PIIMatch]:
    """Detect likely PII in text and return a list of matches.

    Prefers Presidio results; falls back to regex heuristics if unavailable.
    """
    if not text:
        return []

    if _PRESIDIO_AVAILABLE and analyze_text is not None:
        results = analyze_text(text, language="en")
        return [PIIMatch(kind=r.entity_type.lower(), match=text[r.start:r.end], start=r.start, end=r.end) for r in results]

    # Fallback regex heuristic
    matches: List[PIIMatch] = []
    for kind, pattern in _PATTERNS.items():
        for m in pattern.finditer(text):
            if kind in {"national_id", "passport"}:
                surrounding = text[max(0, m.start()-8): m.end()+8]
                if "http" in surrounding or "@" in surrounding:
                    continue
            matches.append(PIIMatch(kind=kind, match=m.group(0), start=m.start(), end=m.end()))
    return matches


def redact_pii(text: str, matches: Optional[List[PIIMatch]] = None) -> str:
    """Redact detected PII spans in the text using kind-specific placeholders.

    Prefers Presidio anonymization; falls back to regex replacement if unavailable.
    """
    if not text:
        return text

    if _PRESIDIO_AVAILABLE and redact_text is not None and matches is None:
        redacted, _results = redact_text(text, language="en")
        return redacted

    # Fallback path uses provided matches or regex detection
    matches = matches if matches is not None else detect_pii(text)
    if not matches:
        return text

    redacted = text
    for m in sorted(matches, key=lambda x: x.start, reverse=True):
        placeholder = f"<{m.kind.upper()}_REDACTED>"
        redacted = redacted[: m.start] + placeholder + redacted[m.end :]
    return redacted
