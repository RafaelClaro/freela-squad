"""Data models for the QA (Quality Assurance) step.

The QA is the squad's final gate. Its rule is absolute: ANY bug, of any severity,
blocks delivery — because Rafael cannot validate before handing off to the client.
QA validation has two layers: objective technical checks (run the tools on disk)
and functional validation against the PO's spec (does it do what was asked).
"""

from dataclasses import dataclass, field


@dataclass
class TechnicalChecks:
    """Objective, measured results from running the tooling on the generated project.

    These are facts, not opinions: did pytest pass, what is the coverage, is there
    any print(), are ruff/mypy clean. Each failing check is a blocker.
    """

    tests_passed: bool = False
    tests_summary: str = ""  # e.g. "7 passed"
    coverage_percent: float = 0.0
    coverage_ok: bool = False  # >= 80
    ruff_clean: bool = False
    mypy_clean: bool = False
    has_print_statements: bool = False  # any print() is a problem
    notes: list[str] = field(default_factory=list)


@dataclass
class FunctionalFinding:
    """One functional check against the spec, with a verdict."""

    requirement: str
    covered: bool
    note: str = ""


@dataclass
class QAReport:
    """The QA verdict on a project: Go only if everything is clean.

    go is True only when technical checks all pass AND every functional requirement
    is covered AND no bugs were found. Any single failure flips it to No-go.
    """

    project_name: str
    go: bool
    technical: TechnicalChecks
    functional_findings: list[FunctionalFinding] = field(default_factory=list)
    bugs: list[str] = field(default_factory=list)  # any entry here means No-go
    summary: str = ""
