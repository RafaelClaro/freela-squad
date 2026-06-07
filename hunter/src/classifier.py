"""Orchestrates the two-layer qualification: filters first, then scoring."""

from src import filters, scoring
from src.models import Opportunity, ScoreResult


def qualify(opportunity: Opportunity) -> ScoreResult:
    """Qualify one opportunity through Camada 1 then Camada 2."""
    filter_result = filters.apply_filters(opportunity)

    if not filter_result.passed:
        # Cut in Camada 1 — never calls Claude.
        return ScoreResult(
            score=0.0,
            classification="DESCARTAR",
            rationale=filter_result.reason or "Filtro eliminatorio",
            alerts=[],
            national_flag=False,
        )

    # Survived Camada 1 — qualitative scoring.
    return scoring.score(opportunity)
