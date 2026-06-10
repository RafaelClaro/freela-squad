"""Tests for the Fullstack planner, scaffolder, and formatter."""

import json
from unittest.mock import MagicMock, patch

from src.arquiteto.models import ArchitectureDecision
from src.fullstack.formatter import to_markdown
from src.fullstack.planner import _to_plan, plan
from src.fullstack.scaffolder import build_scaffold
from src.po.models import Spec

_SPEC = Spec(
    project_name="NF-e API",
    objective="Receive and confirm NF-e.",
    deliverables=["FastAPI app", "Tests"],
    functional_requirements=["POST /nfe", "Telegram confirmation"],
    out_of_scope=["SEFAZ"],
    acceptance_criteria=["Given NF-e, when posted, then persisted"],
    assumptions=["PostgreSQL"],
)

_DECISION = ArchitectureDecision(
    project_name="NF-e API",
    go=True,
    reason="ok",
    database="PostgreSQL",
    auth_type="API Key",
    architecture_notes="Async Telegram.",
)

_PLAN_JSON = {
    "project_name": "NF-e API",
    "setup_notes": "Configure DATABASE_URL.",
    "features": [
        {"order": 2, "name": "POST /nfe", "description": "ep", "test_focus": "201 + persist"},
        {
            "order": 1,
            "name": "NF-e model",
            "description": "SQLAlchemy model",
            "test_focus": "insert",
        },
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


def test_to_plan_ordena_features():
    """Features are sorted by build order, regardless of JSON order."""
    result = _to_plan(_PLAN_JSON)
    assert len(result.features) == 2
    assert result.features[0].order == 1  # sorted: model before endpoint
    assert result.features[0].name == "NF-e model"


def test_plan_usa_claude(monkeypatch):
    """plan() calls Claude and returns an ordered ImplementationPlan."""
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.fullstack.planner.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(_PLAN_JSON)):
        result = plan(_SPEC, _DECISION)
    assert result.project_name == "NF-e API"
    assert len(result.features) == 2


def test_scaffold_gera_arquivos_essenciais():
    """The scaffold includes the runnable essentials."""
    scaffold = build_scaffold("NF-e API")
    paths = {f.path for f in scaffold.files}
    assert "app/main.py" in paths
    assert "tests/test_health.py" in paths
    assert "requirements.txt" in paths
    assert ".env.example" in paths


def test_scaffold_main_tem_health_e_e_python_valido():
    """The generated main.py is valid Python and defines the health endpoint."""
    import ast

    scaffold = build_scaffold("NF-e API")
    main = next(f for f in scaffold.files if f.path == "app/main.py")
    ast.parse(main.content)  # raises if invalid Python
    assert "/health" in main.content
    assert "NF-e API" in main.content


def test_scaffold_test_file_e_python_valido():
    """The generated test file is valid Python."""
    import ast

    scaffold = build_scaffold("X")
    test_file = next(f for f in scaffold.files if f.path == "tests/test_health.py")
    ast.parse(test_file.content)


def test_markdown_lista_features_em_ordem():
    """The plan markdown lists features in build order."""
    md = to_markdown(_to_plan(_PLAN_JSON))
    assert "# Plano de Implementação" in md
    assert md.index("NF-e model") < md.index("POST /nfe")  # model listed first
