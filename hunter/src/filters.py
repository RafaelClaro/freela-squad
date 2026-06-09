"""Camada 1 — eliminatory filters. Pure Python, no external calls.

These run BEFORE any Claude API call. Anything cut here never reaches scoring,
which keeps API cost down (the cheap filter runs first).
"""

import re

from src.models import FilterResult, Opportunity

STRONG_CURRENCIES = {"USD", "EUR", "GBP"}
MIN_DEADLINE_DAYS = 2.0
MIN_HOURLY_RATE = 30.0

# Stack keywords that mean the project is incompatible (not Python backend work).
INCOMPATIBLE_STACK_KEYWORDS = (
    "react native",
    "ios",
    "android",
    "flutter",
    "swift",
    "kotlin",
)


def _has_incompatible_stack(opportunity: Opportunity) -> bool:
    """Return True if the description points to a non-Python / mobile stack."""
    text = f"{opportunity.title} {opportunity.description}".lower()
    # Match whole words only, so short keywords like "ios" don't match inside
    # words such as "varios" or "negocios".
    return any(
        re.search(rf"\b{re.escape(keyword)}\b", text)
        for keyword in INCOMPATIBLE_STACK_KEYWORDS
    )


def _deadline_too_short(opportunity: Opportunity) -> bool:
    """Return True if the deadline is below the squad minimum (2 business days)."""
    if opportunity.deadline_days is None:
        return False  # unknown deadline is not an automatic cut; scoring handles it
    return opportunity.deadline_days < MIN_DEADLINE_DAYS


def _hourly_rate_too_low(opportunity: Opportunity) -> bool:
    """Return True if an hourly opportunity pays below the minimum rate."""
    if opportunity.price_model != "hourly":
        return False
    return opportunity.budget < MIN_HOURLY_RATE


def apply_filters(opportunity: Opportunity) -> FilterResult:
    """Run all eliminatory filters and return the first failure, if any."""
    if _has_incompatible_stack(opportunity):
        return FilterResult(passed=False, reason="Stack incompativel (mobile/nao-Python)")

    if _deadline_too_short(opportunity):
        return FilterResult(passed=False, reason="Prazo inferior a 2 dias uteis")

    if _hourly_rate_too_low(opportunity):
        return FilterResult(passed=False, reason="Rate horario abaixo de $30/h")

    # Weak currency (BRL) is NOT cut here on purpose: it passes to Camada 2,
    # which decides whether it is an exceptional national opportunity.
    return FilterResult(passed=True)
