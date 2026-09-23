"""
Intent classification for incoming chat messages.

Deliberately rule-based (regex/keyword), not LLM-based. Routing a
message to the availability tool vs. the knowledge base is a business
decision that must be predictable and testable -- it is not something
we want an LLM guessing at.
"""
from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    AVAILABILITY = "availability"
    KNOWLEDGE = "knowledge"


_AVAILABILITY_KEYWORDS = [
    "availability", "available", "vacancy", "vacant", "book a room",
    "booking", "free rooms", "any rooms", "do you have rooms",
    "check availability", "room for",
]

_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_GUEST_COUNT_PATTERN = re.compile(
    r"\b(\d{1,2})\s*(guests?|adults?|people|persons?)\b", re.IGNORECASE
)


def classify_intent(message: str) -> Intent:
    """
    Returns AVAILABILITY if the message looks like a room-availability
    request (contains an explicit date or availability-related
    keywords), otherwise KNOWLEDGE.
    """
    message_lower = message.lower()

    if _DATE_PATTERN.search(message):
        return Intent.AVAILABILITY

    if any(keyword in message_lower for keyword in _AVAILABILITY_KEYWORDS):
        return Intent.AVAILABILITY

    return Intent.KNOWLEDGE


def extract_availability_params(
    message: str,
) -> tuple[str | None, str | None, int | None]:
    """
    Best-effort extraction of (check_in, check_out, guests) from a
    natural-language message, e.g.:
        "Do you have rooms for 3 guests from 2026-10-10 to 2026-10-12?"
    Returns None for any field that could not be confidently extracted.
    This is a convenience parser only -- the returned dates are still
    validated by the deterministic availability tool before any
    business decision is made.
    """
    dates = _DATE_PATTERN.findall(message)
    check_in = dates[0] if len(dates) >= 1 else None
    check_out = dates[1] if len(dates) >= 2 else None

    guest_match = _GUEST_COUNT_PATTERN.search(message)
    guests = int(guest_match.group(1)) if guest_match else None

    return check_in, check_out, guests
