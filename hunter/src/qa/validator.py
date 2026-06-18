"""QA validator — functional validation against the spec, plus the final verdict.

Functional validation (does the build cover every requirement?) needs judgement,
so it uses Claude. The final verdict combines the objective technical checks with
the functional findings under the squad's absolute rule: ANY failure => No-go.
"""

import os

import anthropic

from src.claude_client import _extract_json
from src.po.models import Spec
from src.qa.models import FunctionalFinding, QAReport, TechnicalChecks

_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """You are the QA Senior of an autonomous Python dev squad.
You validate whether the delivered project covers every functional requirement in
the spec. You are strict: if a requirement has no corresponding implementation or
test, it is NOT covered.

You receive the spec's requirements and acceptance criteria, plus the list of files
in the delivered project. For each requirement, decide if it appears to be covered
by the delivered files (by their presence and naming) and note any gap.

Be honest about gaps — the squad's rule is zero defects, so a missed requirement
must be flagged, not glossed over.

Respond with ONLY a JSON object, no markdown, no preamble:
{
  "findings": [
    {"requirement": "<requirement text>", "covered": true, "note": "<why/where>"}
  ],
  "bugs": ["<any functional gap or defect you can infer>"],
  "summary": "<one or two sentence overall assessment>"
}"""


def _build_user_content(
    spec: Spec, technical: TechnicalChecks, delivered_files: list[str]
) -> str:
    """Render spec requirements, measured technical results, and delivered files.

    The technical facts (test count, coverage %, linting) are already measured
    objectively by the checker. Including them here prevents Claude from guessing
    at numbers it cannot observe and focuses its judgement on functional coverage.
    """
    requirements = "\n".join(f"- {item}" for item in spec.functional_requirements)
    criteria = "\n".join(f"- {item}" for item in spec.acceptance_criteria)
    files = "\n".join(f"- {path}" for path in delivered_files)
    tech_summary = (
        f"Tests: {'PASSED' if technical.tests_passed else 'FAILED'} "
        f"({technical.tests_summary})\n"
        f"Coverage: {technical.coverage_percent:.0f}% "
        f"({'OK' if technical.coverage_ok else 'BELOW 80%'})\n"
        f"Ruff: {'clean' if technical.ruff_clean else 'errors found'}\n"
        f"MyPy: {'clean' if technical.mypy_clean else 'errors found'}\n"
        f"print() in code: {'YES (blocker)' if technical.has_print_statements else 'none'}"
    )
    return (
        f"TECHNICAL CHECK RESULTS (already measured — do not second-guess these):\n"
        f"{tech_summary}\n\n"
        f"SPEC REQUIREMENTS:\n{requirements}\n\n"
        f"ACCEPTANCE CRITERIA:\n{criteria}\n\n"
        f"DELIVERED FILES:\n{files}"
    )


def _validate_functional(
    spec: Spec, technical: TechnicalChecks, delivered_files: list[str]
) -> tuple[list, list, str]:
    """Call Claude for functional coverage. Returns (findings, bugs, summary)."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=3000,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_content(spec, technical, delivered_files)}
        ],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    data = _extract_json(block.text)
    findings = [
        FunctionalFinding(
            requirement=item.get("requirement", ""),
            covered=bool(item.get("covered", False)),
            note=item.get("note", ""),
        )
        for item in data.get("findings", [])
    ]
    return findings, data.get("bugs", []), data.get("summary", "")


def _decide(technical: TechnicalChecks, findings: list, bugs: list) -> bool:
    """Apply the zero-bug rule: Go only if everything is clean.

    Any failing technical check, any uncovered requirement, or any bug => No-go.
    """
    technical_ok = (
        technical.tests_passed
        and technical.coverage_ok
        and technical.ruff_clean
        and technical.mypy_clean
        and not technical.has_print_statements
    )
    functional_ok = all(finding.covered for finding in findings)
    no_bugs = len(bugs) == 0
    return technical_ok and functional_ok and no_bugs


def validate(spec: Spec, technical: TechnicalChecks, delivered_files: list[str]) -> QAReport:
    """Produce the QA report: functional validation + verdict under the zero-bug rule."""
    findings, bugs, summary = _validate_functional(spec, technical, delivered_files)
    go = _decide(technical, findings, bugs)
    return QAReport(
        project_name=spec.project_name,
        go=go,
        technical=technical,
        functional_findings=findings,
        bugs=bugs,
        summary=summary,
    )
