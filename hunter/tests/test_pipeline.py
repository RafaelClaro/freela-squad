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


def test_decide_architecture_usa_arquiteto(monkeypatch):
    """decide_architecture runs the Arquiteto and returns a decision."""
    from src.po.models import Spec

    spec = Spec(
        project_name="Orders API",
        objective="x",
        deliverables=["a"],
        functional_requirements=["b"],
        out_of_scope=["c"],
        acceptance_criteria=["d"],
        assumptions=["e"],
    )
    go_json = {
        "project_name": "Orders API",
        "go": True,
        "reason": "ok",
        "estimated_hours": 18,
        "implied_rate": 44.0,
        "realistic_days": 3,
        "database": "PostgreSQL",
        "auth_type": "API Key",
        "folder_structure": "src/",
        "dependencies": [],
        "technical_alerts": [],
        "architecture_notes": "",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.arquiteto.decider.anthropic.Anthropic", return_value=_mock_claude(go_json)):
        decision = pipeline.decide_architecture(spec, _OPP)
    assert decision.go is True
    assert "# Decisão Arquitetural" in pipeline.decision_to_markdown(decision)


# ── Stage 7: QA ──────────────────────────────────────────────────────────────

def _make_spec():
    from src.po.models import Spec

    return Spec(
        project_name="Orders API",
        objective="x",
        deliverables=["a"],
        functional_requirements=["CRUD orders"],
        out_of_scope=[],
        acceptance_criteria=["Given order, when created, then persists"],
        assumptions=[],
    )


def _all_green():
    from src.qa.models import TechnicalChecks

    return TechnicalChecks(
        tests_passed=True,
        tests_summary="5 passed",
        coverage_percent=88.0,
        coverage_ok=True,
        ruff_clean=True,
        mypy_clean=True,
        has_print_statements=False,
    )


def test_run_technical_checks_delega_ao_checker():
    """run_technical_checks delegates to checker.run_checks and returns TechnicalChecks."""
    with patch("src.pipeline.checker.run_checks", return_value=_all_green()) as mock_check:
        result = pipeline.run_technical_checks("/tmp/proj")
    assert result.tests_passed is True
    mock_check.assert_called_once_with("/tmp/proj")


def test_validate_quality_go(monkeypatch):
    """validate_quality returns a Go report when everything is clean."""
    import json

    payload = {
        "findings": [{"requirement": "CRUD orders", "covered": True, "note": "orders.py"}],
        "bugs": [],
        "summary": "All good.",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.qa.validator.anthropic.Anthropic", return_value=_mock_claude(payload)):
        report = pipeline.validate_quality(_make_spec(), _all_green(), ["app/routes/orders.py"])
    assert report.go is True
    assert report.project_name == "Orders API"


def test_validate_quality_nogo_com_bug(monkeypatch):
    """validate_quality returns No-go when Claude reports a bug."""
    payload = {
        "findings": [{"requirement": "CRUD orders", "covered": False, "note": "missing"}],
        "bugs": ["DELETE /orders not implemented"],
        "summary": "Missing endpoint.",
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    with patch("src.qa.validator.anthropic.Anthropic", return_value=_mock_claude(payload)):
        report = pipeline.validate_quality(_make_spec(), _all_green(), ["app/main.py"])
    assert report.go is False


def test_qa_report_to_markdown_renderiza():
    """qa_report_to_markdown produces the verdict header and technical section."""
    from src.qa.models import QAReport

    report = QAReport(
        project_name="Orders API",
        go=True,
        technical=_all_green(),
        summary="All good.",
    )
    md = pipeline.qa_report_to_markdown(report)
    assert "✅ GO" in md
    assert "Orders API" in md
    assert "Cobertura" in md
