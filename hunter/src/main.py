"""Hunter entrypoint — collects opportunities from a source, qualifies, notifies."""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from src import classifier, telegram_format, telegram_sender
from src.collectors.base import Collector
from src.collectors.manual import ManualCollector

load_dotenv()  # load credentials from .env into the environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(collector: Collector, dry_run: bool = False) -> None:
    """Collect opportunities from any source, qualify, and notify the qualified ones.

    The collector can be ManualCollector, FreelancerCollector, UpworkCollector, etc.
    The pipeline treats them all identically — that is the white-label design.
    When dry_run is True, notifications are printed instead of sent to Telegram.
    """
    opportunities = collector.collect()
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
    run(ManualCollector(input_path), dry_run=is_dry_run)
