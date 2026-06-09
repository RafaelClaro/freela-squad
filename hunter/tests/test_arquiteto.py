"""Tests for the Arquiteto decider and formatter — Claude mocked, no network."""

import json
from unittest.mock import MagicMock, patch

from src.arquiteto.decider import _to_decision, decide
from src.arquiteto.formatter import to_markdown
from src.models import Opportunity
from src.po.models import Spec

_OPP = Opportunity(
    id="1",
    platform="Upwork",
    title="Inventory API",
    price_model="fixed",
    budget=800.0,
    currency="USD",
    deadline_days=4,
    client_reviews=10,
    payment_verified=True,
    description="Python API for inventory.",
)

_SPEC = Spec(
    project_name="Inventory API",
    objective="Create a REST API to manage stock.",
    deliverables=["Working API", "Tests"],
    functional_requirements=["CRUD products", "Low-stock alert"],
    out_of_scope=["Frontend"],
    acceptance_criteria=["Given low stock, when updated, then alert"],
    assumptions=["PostgreSQL"],
)

_GO_JSON = {
    "project_name": "Inventory API",
    "go": True,
    "reason": "Clear spec, standard stack, rate within range.",
    "estimated_hours": 18,
    "implied_rate": 44.44,
    "realistic_days": 3,
    "database": "PostgreSQL",
    "auth_type": "API Key",
    "folder_structure": "src/\n  main.py\n  models/",
    "dependencies": [{"name": "fastapi", "reason": "standard", "risk": "baixo"}],
    "technical_alerts": ["Validate stock alert threshold with client"],
    "architecture_notes": "Standard CRUD with alert service.",
}

_NOGO_JSON = {
    "project_name": "Tiny job",
    "go": False,
    "reason": "Rate abaixo do range: $18/h.",
    "estimated_hours": 20,
    "implied_rate": 18.0,
    "realistic_days": 0,
    "database": "",
    "auth_type": "",
    "folder_structure": "",
    "dependencies": [],
    "technical_alerts": [],
    "architecture_notes": "",
}


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


def test_to_decision_go_mapeia_campos():
    """A Go JSON maps into a complete ArchitectureDecision."""
    decision = _to_decision(_GO_JSON)
    assert decision.go is True
    assert decision.estimated_hours == 18.0
    assert decision.implied_rate == 44.44
    assert decision.database == "PostgreSQL"
    assert len(decision.dependencies) == 1


def test_to_decision_nogo():
    """A No-go JSON is mapped with go=False and the blocking reason."""
    decision = _to_decision(_NOGO_JSON)
    assert decision.go is False
    assert "Rate abaixo" in decision.reason


def test_decide_go(monkeypatch):
    """decide() returns a Go decision built from Claude's response."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.arquiteto.decider.anthropic.Anthropic", return_value=_mock_claude(_GO_JSON)):
        decision = decide(_SPEC, _OPP)
    assert decision.go is True
    assert decision.implied_rate == 44.44


def test_decide_nogo(monkeypatch):
    """decide() can return a No-go even though the Hunter approved."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.arquiteto.decider.anthropic.Anthropic", return_value=_mock_claude(_NOGO_JSON)):
        decision = decide(_SPEC, _OPP)
    assert decision.go is False


def test_markdown_go_contem_estimativa():
    """The Go markdown shows estimate, rate, and architecture sections."""
    md = to_markdown(_to_decision(_GO_JSON))
    assert "✅ GO" in md
    assert "Taxa implícita: $44.44/h" in md
    assert "## Estrutura de pastas" in md


def test_markdown_nogo_curto_e_claro():
    """The No-go markdown is short and states the blocking reason."""
    md = to_markdown(_to_decision(_NOGO_JSON))
    assert "❌ NO-GO" in md
    assert "Rate abaixo" in md
    assert "## Estrutura de pastas" not in md  # architecture omitted on No-go
