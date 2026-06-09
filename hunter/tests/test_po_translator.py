"""Tests for the PO translator and formatter — Claude mocked, no network."""

import json
from unittest.mock import MagicMock, patch

from src.models import Opportunity
from src.po.formatter import to_markdown
from src.po.models import Spec
from src.po.translator import _to_spec, translate

_SAMPLE_OPP = Opportunity(
    id="1",
    platform="Upwork",
    title="Build a REST API for inventory",
    price_model="fixed",
    budget=850.0,
    currency="USD",
    deadline_days=4,
    client_reviews=12,
    payment_verified=True,
    description="Need a Python API to manage products and stock with low-stock alerts.",
)

_GOOD_JSON = {
    "project_name": "Inventory API",
    "objective": "Create a REST API to manage product stock with low-stock alerts.",
    "deliverables": ["Working REST API", "PostgreSQL schema", "Pytest suite"],
    "functional_requirements": ["CRUD products", "Register stock movements", "Low-stock alert"],
    "out_of_scope": ["Frontend", "External ERP integration"],
    "acceptance_criteria": ["Given stock below min, when updated, then alert flag is returned"],
    "assumptions": ["PostgreSQL (client did not specify; squad default)"],
    "io_pairs": [
        {
            "input": "Product data",
            "source": "API client",
            "output": "Persisted product",
            "destination": "PostgreSQL",
        }
    ],
    "notes_for_architect": "Client mentioned future growth — consider pagination.",
    "untranslatable": False,
    "untranslatable_reason": "",
}


def _mock_claude(payload: dict):
    """Build a mocked Anthropic client returning the given payload as JSON text."""
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(payload)
    response = MagicMock()
    response.content = [block]
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_to_spec_mapeia_todos_os_campos():
    """A well-formed JSON maps into a complete Spec."""
    spec = _to_spec(_GOOD_JSON)
    assert spec.project_name == "Inventory API"
    assert len(spec.deliverables) == 3
    assert len(spec.io_pairs) == 1
    assert spec.io_pairs[0].destination == "PostgreSQL"
    assert spec.untranslatable is False


def test_to_spec_campos_faltando_usa_defaults():
    """A partial JSON does not crash; missing fields become safe defaults."""
    spec = _to_spec({"project_name": "X"})
    assert spec.objective == ""
    assert spec.deliverables == []
    assert spec.io_pairs == []


def test_translate_usa_claude_mockado(monkeypatch):
    """translate() calls Claude and returns a Spec built from the response."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.po.translator.anthropic.Anthropic", return_value=_mock_claude(_GOOD_JSON)):
        spec = translate(_SAMPLE_OPP)
    assert isinstance(spec, Spec)
    assert spec.objective.startswith("Create a REST API")


def test_translate_caso_intraduzivel(monkeypatch):
    """An untranslatable briefing is flagged, not invented into a project."""
    payload = {
        "project_name": "",
        "objective": "",
        "deliverables": [],
        "functional_requirements": [],
        "out_of_scope": [],
        "acceptance_criteria": [],
        "assumptions": [],
        "io_pairs": [],
        "notes_for_architect": "",
        "untranslatable": True,
        "untranslatable_reason": "No technical info in the briefing.",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.po.translator.anthropic.Anthropic", return_value=_mock_claude(payload)):
        spec = translate(_SAMPLE_OPP)
    assert spec.untranslatable is True


def test_markdown_contem_secoes_do_template():
    """The rendered markdown includes the standard spec sections."""
    spec = _to_spec(_GOOD_JSON)
    md = to_markdown(spec)
    assert "# Spec: Inventory API" in md
    assert "## Objetivo" in md
    assert "## Entregáveis" in md
    assert "## Fora de escopo" in md
    assert "## Critérios de aceite" in md
    assert "## Premissas assumidas" in md


def test_markdown_caso_intraduzivel():
    """Untranslatable specs render a clear warning instead of empty sections."""
    spec = Spec(
        project_name="",
        objective="",
        deliverables=[],
        functional_requirements=[],
        out_of_scope=[],
        acceptance_criteria=[],
        assumptions=[],
        untranslatable=True,
        untranslatable_reason="Nothing to build.",
    )
    md = to_markdown(spec)
    assert "intraduzível" in md.lower()
