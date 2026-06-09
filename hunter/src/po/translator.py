"""The PO translator — turns an Opportunity into a Spec using Claude.

Reuses the Hunter's Claude seam (_extract_json) so JSON parsing behaves
identically across the squad. The model is mocked in tests, so this module is
never hit by the network during testing.
"""

import os

import anthropic

from src.claude_client import _extract_json
from src.models import Opportunity
from src.po.models import IOPair, Spec
from src.po.prompt import SYSTEM_PROMPT

_MODEL = "claude-haiku-4-5"


def _build_user_content(opportunity: Opportunity) -> str:
    """Render the opportunity into the briefing text the PO will translate."""
    return (
        f"Title: {opportunity.title}\n"
        f"Platform: {opportunity.platform}\n"
        f"Price model: {opportunity.price_model}\n"
        f"Budget: {opportunity.budget} {opportunity.currency}\n"
        f"Briefing / description:\n{opportunity.description}"
    )


def _to_spec(data: dict) -> Spec:
    """Translate the model's parsed JSON into a Spec object.

    Missing fields fall back to safe empty defaults so a partial response never
    crashes the pipeline — the Arquiteto can still see what the PO produced.
    """
    io_pairs = [
        IOPair(
            input=pair.get("input", ""),
            source=pair.get("source", ""),
            output=pair.get("output", ""),
            destination=pair.get("destination", ""),
        )
        for pair in data.get("io_pairs", [])
    ]
    return Spec(
        project_name=data.get("project_name", ""),
        objective=data.get("objective", ""),
        deliverables=data.get("deliverables", []),
        functional_requirements=data.get("functional_requirements", []),
        out_of_scope=data.get("out_of_scope", []),
        acceptance_criteria=data.get("acceptance_criteria", []),
        assumptions=data.get("assumptions", []),
        io_pairs=io_pairs,
        notes_for_architect=data.get("notes_for_architect", ""),
        untranslatable=data.get("untranslatable", False),
        untranslatable_reason=data.get("untranslatable_reason", ""),
    )


def translate(opportunity: Opportunity) -> Spec:
    """Call Claude to translate one Opportunity into a lean technical Spec."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_content(opportunity)}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    return _to_spec(_extract_json(block.text))
