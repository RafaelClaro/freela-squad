"""Data models for the Arquiteto (Architect) decision step.

The Arquiteto receives a Spec and emits an ArchitectureDecision: a binding
Go/No-go with an hour estimate, an implied-rate check, and — when Go — the
technical architecture the Engenheiro and Dev will follow.
"""

from dataclasses import dataclass, field


@dataclass
class Dependency:
    """One critical dependency the architecture relies on."""

    name: str
    reason: str
    risk: str  # "baixo" / "médio" / "alto"


@dataclass
class ArchitectureDecision:
    """The Arquiteto's binding decision on a Spec.

    A No-go carries a clear reason and stops the pipeline. A Go carries the
    estimate, the validated implied rate, and the architecture definition.
    """

    project_name: str
    go: bool  # True = Go, False = No-go
    reason: str  # justification — required, especially for No-go

    # Estimate (filled on Go; may be partial on No-go if the reason is rate-based)
    estimated_hours: float = 0.0
    implied_rate: float = 0.0  # value / hours, in the opportunity's currency
    realistic_days: int = 0

    # Architecture (filled on Go)
    database: str = ""  # "PostgreSQL" / "SQLite" + justification lives in notes
    auth_type: str = ""  # "API Key" / "JWT" / "OAuth"
    folder_structure: str = ""  # tree as text
    dependencies: list[Dependency] = field(default_factory=list)
    technical_alerts: list[str] = field(default_factory=list)  # signals for the Engenheiro
    architecture_notes: str = ""
