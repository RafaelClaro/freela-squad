"""Tests for the manual collector — reads the fixtures and produces Opportunity objects."""

from pathlib import Path

from src.collectors.manual import ManualCollector
from src.models import Opportunity

FIXTURES = Path(__file__).parent / "fixtures" / "briefings.json"


def test_manual_collector_le_os_seis():
    """ManualCollector reads all 6 briefings from JSON."""
    collector = ManualCollector(FIXTURES)
    opportunities = collector.collect()
    assert len(opportunities) == 6


def test_manual_collector_retorna_opportunity():
    """Each item collected is a proper Opportunity object with expected fields."""
    collector = ManualCollector(FIXTURES)
    opportunities = collector.collect()
    first = opportunities[0]
    assert isinstance(first, Opportunity)
    assert first.id == "1"
    assert first.currency == "USD"
