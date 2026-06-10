"""The Engenheiro definer — turns an architecture decision into an EngineeringGuide.

The fixed squad standards are attached in code (always). Claude only fills the
project-specific layer. Reuses the Hunter's _extract_json for consistent parsing.
"""

import os

import anthropic

from src.arquiteto.models import ArchitectureDecision
from src.claude_client import _extract_json
from src.engenheiro.models import CustomException, EngineeringGuide
from src.engenheiro.prompt import SYSTEM_PROMPT

_MODEL = "claude-haiku-4-5"


def _build_user_content(decision: ArchitectureDecision) -> str:
    """Render the architecture decision into the input the Engenheiro reasons over."""
    deps = "\n".join(f"- {dep.name} ({dep.risk})" for dep in decision.dependencies)
    alerts = "\n".join(f"- {alert}" for alert in decision.technical_alerts)
    return (
        f"PROJECT: {decision.project_name}\n\n"
        f"Database: {decision.database}\n"
        f"Auth: {decision.auth_type}\n\n"
        f"Dependencies:\n{deps}\n\n"
        f"Architecture notes:\n{decision.architecture_notes}\n\n"
        f"Technical alerts from the Arquiteto:\n{alerts}"
    )


def _to_guide(data: dict) -> EngineeringGuide:
    """Translate the model's parsed JSON into an EngineeringGuide.

    The fixed squad_standards default is applied by the dataclass, so a partial
    response still yields a guide carrying the squad's non-negotiable standards.
    """
    exceptions = [
        CustomException(
            name=exc.get("name", ""),
            when_raised=exc.get("when_raised", ""),
            http_status=int(exc.get("http_status", 500) or 500),
        )
        for exc in data.get("custom_exceptions", [])
    ]
    return EngineeringGuide(
        project_name=data.get("project_name", ""),
        custom_exceptions=exceptions,
        logging_guidance=data.get("logging_guidance", []),
        testing_guidance=data.get("testing_guidance", []),
        quality_alerts=data.get("quality_alerts", []),
    )


def define(decision: ArchitectureDecision) -> EngineeringGuide:
    """Call Claude to define the project-specific engineering guidance."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_content(decision)}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    if response.stop_reason == "max_tokens":
        raise ValueError(
            "Engenheiro response was truncated (hit max_tokens). Increase max_tokens."
        )
    return _to_guide(_extract_json(block.text))
