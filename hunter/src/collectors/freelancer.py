"""Freelancer.com collector — fetches active projects via the REST API using httpx.

No SDK dependency: we talk to the API directly, the same pattern as telegram_sender.
The field mapping (Freelancer JSON -> Opportunity) is isolated in _to_opportunity
so it is trivial to adjust against the real sandbox response if any field differs.
"""

import logging
import os

import httpx

from src.collectors.base import Collector
from src.models import Opportunity

logger = logging.getLogger(__name__)

# Sandbox by default; production is set via FLN_URL env var when ready.
_DEFAULT_BASE_URL = "https://www.freelancer-sandbox.com"
_PROJECTS_PATH = "/api/projects/0.1/projects/active"
_TIMEOUT_SECONDS = 15.0


def _to_opportunity(raw: dict) -> Opportunity:
    """Translate one Freelancer project object into the common Opportunity format.

    Freelancer nests currency and budget as objects, so we read them defensively.
    If a field is missing, we fall back to safe defaults rather than crashing.
    """
    budget = raw.get("budget") or {}
    currency = raw.get("currency") or {}
    project_type = raw.get("type", "fixed")
    price_model = "hourly" if project_type == "hourly" else "fixed"

    # Budget: use maximum if present, else minimum, else 0.
    budget_value = budget.get("maximum") or budget.get("minimum") or 0

    return Opportunity(
        id=str(raw.get("id", "")),
        platform="Freelancer",
        title=raw.get("title", ""),
        price_model=price_model,
        budget=float(budget_value),
        currency=currency.get("code", "USD"),
        deadline_days=None,  # Freelancer does not expose a fixed deadline in the listing
        client_reviews=0,  # enriched later if needed; not in the basic listing
        payment_verified=bool(raw.get("upgrades", {}).get("verified", False)),
        description=raw.get("preview_description") or raw.get("description", ""),
    )


class FreelancerCollector(Collector):
    """Collects active projects from the Freelancer.com API."""

    def __init__(self, query: str = "python", limit: int = 20):
        self.query = query
        self.limit = limit
        self.token = os.environ.get("FREELANCER_OAUTH_TOKEN")
        # Empty or unset FLN_URL falls back to the sandbox default.
        self.base_url = os.environ.get("FLN_URL") or _DEFAULT_BASE_URL

    def collect(self) -> list[Opportunity]:
        """Fetch active projects matching the query and map them to Opportunity.

        Returns an empty list (never raises) if credentials are missing or the
        request fails, so a broken source never crashes the whole pipeline.
        """
        if not self.token:
            logger.error("FREELANCER_OAUTH_TOKEN missing; skipping Freelancer source")
            return []

        url = f"{self.base_url}{_PROJECTS_PATH}"
        headers = {"freelancer-oauth-v1": self.token}
        params: dict[str, str] = {
            "query": self.query,
            "limit": str(self.limit),
            "compact": "true",
            "job_details": "true",
        }

        try:
            response = httpx.get(url, headers=headers, params=params, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except Exception as error:  # noqa: BLE001 - a broken source must not crash the run
            logger.error(f"Freelancer request failed: {error}")
            return []

        projects = payload.get("result", {}).get("projects", [])
        opportunities = [_to_opportunity(project) for project in projects]
        logger.info(f"Freelancer collector returned {len(opportunities)} opportunities")
        return opportunities
