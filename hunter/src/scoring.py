"""Camada 2 — qualitative scoring via Claude.

Only opportunities that survived Camada 1 reach this layer. If Claude returns a
malformed response, the pipeline degrades gracefully to OBSERVAR with an alert
instead of crashing.
"""

import logging

from src import claude_client
from src.models import Opportunity, ScoreResult

logger = logging.getLogger(__name__)

_VALID_CLASSES = {"NOTIFICAR", "OBSERVAR", "DESCARTAR"}


def score(opportunity: Opportunity) -> ScoreResult:
    """Score a surviving opportunity, with graceful fallback on failure."""
    try:
        data = claude_client.score_opportunity(opportunity)
        classification = str(data["classification"]).upper()
        if classification not in _VALID_CLASSES:
            raise ValueError(f"Unknown classification: {classification}")

        return ScoreResult(
            score=float(data["score"]),
            classification=classification,
            rationale=str(data["rationale"]),
            alerts=list(data.get("alerts", [])),
            national_flag=bool(data.get("national_flag", False)),
        )
    except Exception as error:  # noqa: BLE001 - intentional graceful degradation
        logger.warning(f"Scoring failed for opportunity {opportunity.id}: {error}")
        return ScoreResult(
            score=4.0,
            classification="OBSERVAR",
            rationale="Scoring automatico falhou; revisar manualmente.",
            alerts=["Falha no scoring automatico - revisao manual necessaria"],
            national_flag=False,
        )
