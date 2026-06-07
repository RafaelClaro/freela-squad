"""Shared test fixtures: the 6 synthetic briefings."""

import json
from pathlib import Path

import pytest

from src.models import Opportunity

FIXTURES = Path(__file__).parent / "fixtures" / "briefings.json"


@pytest.fixture
def opportunities() -> dict[str, Opportunity]:
    """Load the 6 briefings keyed by their id for easy lookup."""
    raw = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return {item["id"]: Opportunity(**item) for item in raw}
