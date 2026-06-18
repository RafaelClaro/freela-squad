"""Tests for the QA validator and formatter — Claude mocked, zero-bug rule."""

import json
from unittest.mock import MagicMock, patch

from src.po.models import Spec
from src.qa.formatter import to_markdown
from src.qa.models import FunctionalFinding, QAReport, TechnicalChecks
from src.qa.validator import _decide, validate

_SPEC = Spec(
    project_name="Items API",
    objective="Manage items.",
    deliverables=["API"],
    functional_requirements=["POST /items", "GET /items"],
    out_of_scope=["auth"],
    acceptance_criteria=["Given item, when posted, then stored"],
    assumptions=["in-memory"],
)


def _all_green_technical() -> TechnicalChecks:
    return TechnicalChecks(
        tests_passed=True,
        tests_summary="7 passed",
        coverage_percent=92.0,
        coverage_ok=True,
        ruff_clean=True,
        mypy_clean=True,
        has_print_statements=False,
    )


def test_decide_go_quando_tudo_limpo():
    """Go only when technical is all green, requirements covered, no bugs."""
    findings = [FunctionalFinding(requirement="POST /items", covered=True)]
    assert _decide(_all_green_technical(), findings, []) is True


def test_decide_nogo_se_teste_falha():
    """A failing test blocks delivery."""
    tech = _all_green_technical()
    tech.tests_passed = False
    findings = [FunctionalFinding(requirement="x", covered=True)]
    assert _decide(tech, findings, []) is False


def test_decide_nogo_se_cobertura_baixa():
    """Coverage below 80% blocks delivery."""
    tech = _all_green_technical()
    tech.coverage_ok = False
    assert _decide(tech, [], []) is False


def test_decide_nogo_se_tem_print():
    """A stray print() blocks delivery."""
    tech = _all_green_technical()
    tech.has_print_statements = True
    assert _decide(tech, [], []) is False


def test_decide_nogo_se_requisito_nao_coberto():
    """An uncovered requirement blocks delivery."""
    findings = [FunctionalFinding(requirement="GET /items", covered=False)]
    assert _decide(_all_green_technical(), findings, []) is False


def test_decide_nogo_se_qualquer_bug():
    """Any bug — even one — blocks delivery (zero-bug rule)."""
    findings = [FunctionalFinding(requirement="x", covered=True)]
    assert _decide(_all_green_technical(), findings, ["cosmetic glitch"]) is False


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


def test_validate_go(monkeypatch):
    """A clean project with full coverage gets a Go."""
    payload = {
        "findings": [
            {"requirement": "POST /items", "covered": True, "note": "items.py"},
            {"requirement": "GET /items", "covered": True, "note": "items.py"},
        ],
        "bugs": [],
        "summary": "All requirements covered.",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.qa.validator.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(payload)):
        report = validate(_SPEC, _all_green_technical(), ["app/routes/items.py"])
    assert report.go is True


def test_validate_nogo_com_gap(monkeypatch):
    """A project with an uncovered requirement gets a No-go even if tech is green."""
    payload = {
        "findings": [{"requirement": "GET /items", "covered": False, "note": "missing"}],
        "bugs": ["GET /items not implemented"],
        "summary": "Missing an endpoint.",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.qa.validator.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(payload)):
        report = validate(_SPEC, _all_green_technical(), ["app/main.py"])
    assert report.go is False


def test_markdown_mostra_veredito_e_checks():
    """The markdown shows the verdict and the technical checks."""
    report = QAReport(
        project_name="Items API",
        go=True,
        technical=_all_green_technical(),
        functional_findings=[FunctionalFinding(requirement="POST /items", covered=True)],
        summary="ok",
    )
    md = to_markdown(report)
    assert "✅ GO" in md
    assert "Cobertura: 92%" in md
    assert "Validação funcional" in md
