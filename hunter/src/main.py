"""Hunter entrypoint — reads opportunities from JSON, qualifies, sends notifications."""

import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from src import classifier, telegram_format, telegram_sender
from src.models import Opportunity

logging.basicConfig(level=logging.INFO)
load_dotenv()
logger = logging.getLogger(__name__)


def load_opportunities(path: Path) -> list[Opportunity]:
    """Load opportunities from a JSON file into Opportunity objects."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Opportunity(**item) for item in raw]


def run(path: Path, dry_run: bool = False) -> None:
    """Qualify every opportunity and notify the ones that qualify.

    When dry_run is True, notifications are printed instead of sent to Telegram.
    """
    opportunities = load_opportunities(path)
    for opportunity in opportunities:
        result = classifier.qualify(opportunity)
        logger.info(f"#{opportunity.id}: {result.classification} (score {result.score:.1f})")
        if result.classification in ("NOTIFICAR", "OBSERVAR"):
            message = telegram_format.format_notification(opportunity, result)
            if dry_run:
                print(message)
                print("-" * 40)
            else:
                telegram_sender.send_message(message)


if __name__ == "__main__":
    args = sys.argv[1:]
    is_dry_run = "--dry-run" in args
    positional = [a for a in args if not a.startswith("--")]
    input_path = Path(positional[0]) if positional else Path("tests/fixtures/briefings.json")
    run(input_path, dry_run=is_dry_run)
