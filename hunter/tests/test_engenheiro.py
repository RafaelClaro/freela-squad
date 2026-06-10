"""Tests for the Engenheiro definer and formatter — Claude mocked, no network."""

import json
from unittest.mock import MagicMock, patch

from src.arquiteto.models import ArchitectureDecision, Dependency
from src.engenheiro.definer import _to_guide, define
from src.engenheiro.formatter import to_markdown
from src.engenheiro.models import SQUAD_STANDARDS

_DECISION = ArchitectureDecision(
    project_name="NF-e API",
    go=True,
    reason="ok",
    estimated_hours=36,
    implied_rate=39,
    realistic_days=4,
    database="PostgreSQL",
    auth_type="API Key",
    dependencies=[Dependency(name="python-telegram-bot", reason="telegram", risk="médio")],
    technical_alerts=["Mock Telegram in tests", "Test state machine"],
    architecture_notes="Async Telegram, JSONB storage.",
)

_GUIDE_JSON = {
    "project_name": "NF-e API",
    "custom_exceptions": [
        {"name": "NFeValidationError", "when_raised": "invalid NF-e payload", "http_status": 400},
        {"name": "NFeNotFoundError", "when_raised": "NF-e id not found", "http_status": 404},
    ],
    "logging_guidance": [
        "INFO when NF-e persisted",
        "WARNING when Telegram notification fails",
        "ERROR on database failure",
    ],
    "testing_guidance": [
        "Unit test the NF-e validator with valid and invalid payloads",
        "Mock the Telegram API in all notification tests",
        "Integration test POST /nf-e happy path and 400 path",
    ],
    "quality_alerts": [
        "Telegram failure must not block NF-e persistence",
        "Test the pending->confirmed->rejected state machine explicitly",
    ],
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


def test_to_guide_inclui_padroes_fixos_do_squad():
    """Every guide carries the fixed squad standards, even from a partial JSON."""
    guide = _to_guide({"project_name": "X"})
    assert guide.squad_standards == SQUAD_STANDARDS
    assert len(guide.squad_standards) > 0


def test_to_guide_mapeia_camada_do_projeto():
    """The project-specific layer is mapped from the JSON."""
    guide = _to_guide(_GUIDE_JSON)
    assert len(guide.custom_exceptions) == 2
    assert guide.custom_exceptions[0].name == "NFeValidationError"
    assert guide.custom_exceptions[0].http_status == 400
    assert len(guide.testing_guidance) == 3


def test_define_usa_claude(monkeypatch):
    """define() calls Claude and returns a guide with both layers."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.engenheiro.definer.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(_GUIDE_JSON)):
        guide = define(_DECISION)
    assert guide.project_name == "NF-e API"
    assert len(guide.squad_standards) > 0  # fixed layer always present
    assert len(guide.custom_exceptions) == 2  # project layer from Claude


def test_markdown_contem_as_duas_camadas():
    """The markdown shows both the fixed standards and the project-specific layer."""
    md = to_markdown(_to_guide(_GUIDE_JSON))
    assert "## Padrões fixos do squad" in md
    assert "Type hints obrigatórios" in md  # a fixed standard
    assert "NFeValidationError" in md  # a project-specific exception
    assert "## Testes" in md
