"""Manual collector — reads opportunities from a JSON file.

This is the first collector and the fallback for any source without an API:
national platforms, sites that block scraping, or one-off briefings pasted by
Rafael. The JSON must contain a list of objects matching the Opportunity fields.
"""

import json
from pathlib import Path

from src.collectors.base import Collector
from src.models import Opportunity


class ManualCollector(Collector):
    """Loads opportunities from a local JSON file."""

    def __init__(self, path: Path):
        self.path = path

    def collect(self) -> list[Opportunity]:
        """Read the JSON file and translate each entry into an Opportunity."""
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [Opportunity(**item) for item in raw]
