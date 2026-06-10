"""The Arquiteto decider — turns a Spec into a Go/No-go ArchitectureDecision.

Needs the opportunity's value and currency too, because the implied-rate check
(value / hours) is central to the decision. Reuses the Hunter's _extract_json so
JSON parsing is consistent across the squad. Claude is mocked in tests.
"""

import os
import re

import anthropic

from src.arquiteto.models import ArchitectureDecision, Dependency
from src.arquiteto.prompt import SYSTEM_PROMPT
from src.claude_client import _extract_json
from src.models import Opportunity
from src.po.models import Spec

_MODEL = "claude-haiku-4-5"


def _as_number(value: object) -> float:
    """Extract a number from a value that may be a number or a descriptive string.

    The model sometimes returns rich strings like "500 BRL/h (~$100/h)". We pull
    the first numeric token so the pipeline never crashes on a formatted rate.
    Returns 0.0 if no number is found.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            return float(match.group(0))
    return 0.0


def _build_user_content(spec: Spec, opportunity: Opportunity) -> str:
    """Render the spec plus the commercial facts the Arquiteto needs to decide."""
    deliverables = "\n".join(f"- {item}" for item in spec.deliverables)
    requirements = "\n".join(f"- {item}" for item in spec.functional_requirements)
    return (
        f"PROJECT VALUE: {opportunity.budget} {opportunity.currency} "
        f"({opportunity.price_model})\n\n"
        f"SPEC:\n"
        f"Objective: {spec.objective}\n\n"
        f"Deliverables:\n{deliverables}\n\n"
        f"Functional requirements:\n{requirements}\n\n"
        f"Notes from PO: {spec.notes_for_architect}"
    )


def _to_decision(data: dict) -> ArchitectureDecision:
    """Translate the model's parsed JSON into an ArchitectureDecision object."""
    dependencies = [
        Dependency(
            name=dep.get("name", ""),
            reason=dep.get("reason", ""),
            risk=dep.get("risk", "baixo"),
        )
        for dep in data.get("dependencies", [])
    ]
    return ArchitectureDecision(
        project_name=data.get("project_name", ""),
        go=data.get("go", False),
        reason=data.get("reason", ""),
        estimated_hours=_as_number(data.get("estimated_hours")),
        implied_rate=_as_number(data.get("implied_rate")),
        realistic_days=int(_as_number(data.get("realistic_days"))),
        database=data.get("database", ""),
        auth_type=data.get("auth_type", ""),
        folder_structure=data.get("folder_structure", ""),
        dependencies=dependencies,
        technical_alerts=data.get("technical_alerts", []),
        architecture_notes=data.get("architecture_notes", ""),
    )


def decide(spec: Spec, opportunity: Opportunity) -> ArchitectureDecision:
    """Call Claude to assess the spec and emit a Go/No-go architecture decision."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_content(spec, opportunity)}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    if response.stop_reason == "max_tokens":
        raise ValueError(
            "Arquiteto response was truncated (hit max_tokens). "
            "Increase max_tokens or simplify the spec."
        )
    return _to_decision(_extract_json(block.text))