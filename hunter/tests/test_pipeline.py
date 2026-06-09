"""Tests for the pipeline orchestration — Claude and classifier mocked."""

import json
from unittest.mock import MagicMock, patch

from src import pipeline
from src.models import Opportunity, ScoreResult

_OPP = Opportunity(
    id="1",
    platform="Upwork",
    title="Build a REST API",
    price_model="fixed",
    budget=800.0,
    currency="USD",
    deadline_days=4,
    client_reviews=10,
    payment_verified=True,
    description="Need a Python API to manage orders.",
)

_SPEC_JSON = {
    "project_name": "Orders API",
    "objective": "Create a REST API to manage orders.",
    "deliverables": ["Working API"],
    "functional_requirements": ["CRUD orders"],
    "out_of_scope": ["Frontend"],
    "acceptance_criteria": ["Given an order, when created, then it persists"],
    "assumptions": ["PostgreSQL (default)"],
    "io_pairs": [],
    "notes_for_architect": "",
    "untranslatable": False,
    "untranslatable_reason": "",
}


def test_qualify_opportunity_delega_ao_classifier():
    """qualify_opportunity returns whatever the Hunter classifier decides."""
    fake = ScoreResult(score=8.0, classification="NOTIFICAR", rationale="ok", alerts=[])
    with patch("src.pipeline.classifier.qualify", return_value=fake) as mock_qualify:
        result = pipeline.qualify_opportunity(_OPP)
    assert result.classification == "NOTIFICAR"
    assert mock_qualify.called


def _mock_claude(payload: dict):
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(payload)
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "end_turn"
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_translate_to_spec_usa_po(monkeypatch):
    """translate_to_spec runs the PO translator and returns a Spec."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.po.translator.anthropic.Anthropic", return_value=_mock_claude(_SPEC_JSON)):
        spec = pipeline.translate_to_spec(_OPP)
    assert spec.project_name == "Orders API"


def test_spec_to_markdown_renderiza():
    """spec_to_markdown produces the markdown spec layout."""
    from src.po.translator import _to_spec

    spec = _to_spec(_SPEC_JSON)
    md = pipeline.spec_to_markdown(spec)
    assert "# Spec: Orders API" in md
    assert "## Objetivo" in md
