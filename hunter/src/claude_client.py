"""Isolated wrapper around the Claude API.

Kept separate so tests can mock this single seam instead of the whole network.
"""

import json
import os
import re

import anthropic

from src.models import Opportunity


def _extract_json(text: str) -> dict:
    """Extract a JSON object from the model's reply, tolerating extra text.

    Handles plain JSON, JSON wrapped in ```json fences, and JSON with
    surrounding prose by grabbing the first {...} block.
    """
    stripped = text.strip()
    # Remove markdown code fences if present.
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        # Fallback: grab the first {...} block anywhere in the text.
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """You are the Hunter, qualifying freelance opportunities for a Python dev squad.
Score the opportunity on a 0-10 scale and classify it.

Apply these rules IN ORDER. Earlier rules override later ones.

RULE 1 — BRL exceptional (overrides everything below):
BRL is normally rejected. EXCEPT when a BRL opportunity is exceptional: high value,
very clear scope, comfortable deadline, strong client, profitability above the
international average. In that exceptional case you MUST set classification to
OBSERVAR and national_flag to true, REGARDLESS of how high the score is. A high
score does NOT turn an exceptional BRL into NOTIFICAR — it stays OBSERVAR so the
human decides. Score it on merit (it can be 7+), but the label is OBSERVAR.

RULE 2 — Vague scope:
If the scope is vague ("explain after we connect", "maybe an API", "more tasks
later", no concrete deliverables), you MUST raise alerts describing each red flag.
If it is vague but has SOME usable technical hint, classify as OBSERVAR (let the
human decide). If it is so vague there is nothing to build, classify as DESCARTAR.

RULE 3 — Score-based classification (only when rules above do not apply):
6-10 NOTIFICAR, 4-5.9 OBSERVAR, 0-3.9 DESCARTAR.

Respond with ONLY a JSON object, no markdown, no preamble:
{"score": <float>, "classification": "<NOTIFICAR|OBSERVAR|DESCARTAR>",
 "rationale": "<one or two lines>", "alerts": ["<alert>", ...], "national_flag": <bool>}"""


def score_opportunity(opportunity: Opportunity) -> dict:
    """Call Claude to score one opportunity. Returns the parsed JSON dict."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    user_content = (
        f"Title: {opportunity.title}\n"
        f"Platform: {opportunity.platform}\n"
        f"Price model: {opportunity.price_model}\n"
        f"Budget: {opportunity.budget} {opportunity.currency}\n"
        f"Deadline (days): {opportunity.deadline_days}\n"
        f"Client reviews: {opportunity.client_reviews}\n"
        f"Payment verified: {opportunity.payment_verified}\n"
        f"Description: {opportunity.description}"
    )
    response = client.messages.create(
        model=_MODEL,
        max_tokens=500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    return _extract_json(block.text)
