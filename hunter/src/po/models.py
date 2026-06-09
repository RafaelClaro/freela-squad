"""Data models for the PO (Product Owner) translation step.

The PO turns a raw Opportunity into a Spec: a lean, structured technical brief
the rest of the squad can build from. The Spec mirrors the squad's spec-template:
objective, deliverables, functional requirements, out-of-scope, inputs/outputs,
acceptance criteria, and assumptions.
"""

from dataclasses import dataclass, field


@dataclass
class IOPair:
    """One row of the inputs/outputs table in the spec."""

    input: str
    source: str
    output: str
    destination: str


@dataclass
class Spec:
    """A lean technical spec produced by the PO from an Opportunity.

    This is what the Arquiteto consumes next. It is intentionally lightweight —
    not a corporate PRD. Every gap the PO had to fill lives in `assumptions`,
    so no hidden decisions reach the rest of the squad.
    """

    project_name: str
    objective: str  # one sentence — what the client wants
    deliverables: list[str]
    functional_requirements: list[str]
    out_of_scope: list[str]
    acceptance_criteria: list[str]  # Given/When/Then style strings
    assumptions: list[str]  # each gap the PO resolved, made explicit
    io_pairs: list[IOPair] = field(default_factory=list)
    notes_for_architect: str = ""  # optional technical signal for the Arquiteto
    untranslatable: bool = False  # True when the briefing has no usable technical info
    untranslatable_reason: str = ""  # filled only when untranslatable is True
