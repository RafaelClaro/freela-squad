"""Data models for the Hunter qualification pipeline."""

from dataclasses import dataclass


@dataclass
class Opportunity:
    """A freelance opportunity to be qualified."""

    id: str
    platform: str
    title: str
    price_model: str  # "fixed" or "hourly"
    budget: float
    currency: str
    deadline_days: float | None
    client_reviews: int
    payment_verified: bool
    description: str


@dataclass
class FilterResult:
    """Result of the eliminatory (Camada 1) filters."""

    passed: bool
    reason: str | None = None  # filled only when passed is False


@dataclass
class ScoreResult:
    """Result of the qualitative (Camada 2) scoring."""

    score: float
    classification: str  # NOTIFICAR / OBSERVAR / DESCARTAR
    rationale: str
    alerts: list[str]
    national_flag: bool = False  # True for the BRL exceptional case
