"""Isolated wrapper around the Claude API.

Kept separate so tests can mock this single seam instead of the whole network.
"""

import json
import re
import os

import anthropic


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

from src.models import Opportunity

_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """You are the Hunter, qualifying freelance opportunities for a Python dev squad.
Score the opportunity on a 0-10 scale and classify it.

Rules you must apply:
- Strong currencies (USD/EUR/GBP) are normal. BRL is normally rejected, EXCEPT when
  the BRL opportunity is exceptional: high value, very clear scope, comfortable deadline,
  strong client, profitability above the international average. In that exceptional case,
  classify as OBSERVAR and set national_flag true.
- Vague scope ("explain after we connect", "maybe an API", "more tasks later") lowers
  clarity and must raise alerts.
- Classification by final score: 6-10 NOTIFICAR, 4-5.9 OBSERVAR, 0-3.9 DESCARTAR.

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
