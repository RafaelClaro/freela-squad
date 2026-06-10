"""The Fullstack feature planner — breaks a project into small, testable features.

This is step one of incremental implementation: instead of generating a whole
project, the Dev first plans an ordered list of small features. Each will be built
and tested on its own. Reuses the Hunter's _extract_json for consistent parsing.
"""

import os

import anthropic

from src.arquiteto.models import ArchitectureDecision
from src.claude_client import _extract_json
from src.fullstack.models import Feature, ImplementationPlan
from src.po.models import Spec

_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """You are the Fullstack Developer of an autonomous Python squad.
You do NOT implement the whole project at once — that produces broken code. Instead,
you break the project into an ORDERED list of small, independently testable features.

Given the spec and architecture, produce a build plan where:
- Each feature is small enough to build and test in one sitting.
- Features are ordered so dependencies come first (models before endpoints that use
  them; auth before protected routes; etc.).
- Each feature names what to build AND what its test must cover.
- The scaffold (FastAPI app booting, /health, DB session, one passing test) is
  assumed to already exist — do NOT include it as a feature; start from the first
  real piece of functionality.

Keep it focused: most projects are 4-8 features. Do not over-split into trivial steps.

Respond with ONLY a JSON object, no markdown, no preamble:
{
  "project_name": "<name>",
  "setup_notes": "<anything the scaffold needs before features start, or empty>",
  "features": [
    {
      "order": 1,
      "name": "<short feature name>",
      "description": "<what to build>",
      "test_focus": "<what the test must cover>"
    }
  ]
}"""


def _build_user_content(spec: Spec, decision: ArchitectureDecision) -> str:
    """Render spec + architecture into the planner's input."""
    deliverables = "\n".join(f"- {item}" for item in spec.deliverables)
    requirements = "\n".join(f"- {item}" for item in spec.functional_requirements)
    return (
        f"PROJECT: {spec.project_name}\n\n"
        f"Objective: {spec.objective}\n\n"
        f"Deliverables:\n{deliverables}\n\n"
        f"Functional requirements:\n{requirements}\n\n"
        f"Database: {decision.database} | Auth: {decision.auth_type}\n"
        f"Architecture notes: {decision.architecture_notes}"
    )


def _to_plan(data: dict) -> ImplementationPlan:
    """Translate parsed JSON into an ImplementationPlan."""
    features = [
        Feature(
            order=int(feature.get("order", index + 1) or index + 1),
            name=feature.get("name", ""),
            description=feature.get("description", ""),
            test_focus=feature.get("test_focus", ""),
        )
        for index, feature in enumerate(data.get("features", []))
    ]
    features.sort(key=lambda f: f.order)
    return ImplementationPlan(
        project_name=data.get("project_name", ""),
        features=features,
        setup_notes=data.get("setup_notes", ""),
    )


def plan(spec: Spec, decision: ArchitectureDecision) -> ImplementationPlan:
    """Call Claude to break the project into an ordered list of testable features."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=4000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_content(spec, decision)}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    if response.stop_reason == "max_tokens":
        raise ValueError("Fullstack planner response was truncated. Increase max_tokens.")
    return _to_plan(_extract_json(block.text))
