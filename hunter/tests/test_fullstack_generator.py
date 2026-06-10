"""Tests for the Fullstack feature generator — Claude mocked, syntax validation."""

import json
from unittest.mock import MagicMock, patch

from src.engenheiro.models import CustomException, EngineeringGuide
from src.fullstack.generator import _validate_syntax, generate_feature
from src.fullstack.models import Feature, GeneratedFile

_FEATURE = Feature(
    order=1,
    name="NF-e model",
    description="SQLAlchemy model for NF-e",
    test_focus="insert and fetch by id",
)

_GUIDE = EngineeringGuide(
    project_name="NF-e API",
    custom_exceptions=[
        CustomException(name="NFeValidationError", when_raised="invalid", http_status=400)
    ],
)

_VALID_CODE = "def add(a: int, b: int) -> int:\n    return a + b\n"
_INVALID_CODE = "def broken(:\n    return"  # syntax error on purpose


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


def test_validate_syntax_aceita_codigo_valido():
    """Valid Python files produce no syntax errors."""
    files = [GeneratedFile(path="app/m.py", content=_VALID_CODE)]
    assert _validate_syntax(files) == []


def test_validate_syntax_detecta_codigo_invalido():
    """A Python file with a syntax error is detected and reported."""
    files = [GeneratedFile(path="app/bad.py", content=_INVALID_CODE)]
    errors = _validate_syntax(files)
    assert len(errors) == 1
    assert "app/bad.py" in errors[0]


def test_validate_syntax_ignora_nao_python():
    """Non-Python files are not syntax-checked."""
    files = [GeneratedFile(path="README.md", content="# not python :(")]
    assert _validate_syntax(files) == []


def test_generate_feature_codigo_valido(monkeypatch):
    """A feature whose generated code is valid returns syntax_ok=True."""
    payload = {
        "files": [
            {"path": "app/models/nfe.py", "content": _VALID_CODE},
            {"path": "tests/test_nfe.py", "content": _VALID_CODE},
        ]
    }
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.fullstack.generator.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(payload)):
        result = generate_feature(_FEATURE, _GUIDE, ["app/main.py"])
    assert result.syntax_ok is True
    assert len(result.files) == 2
    assert result.syntax_errors == []


def test_generate_feature_codigo_invalido_e_sinalizado(monkeypatch):
    """If the model emits invalid Python, syntax_ok is False and errors are listed.

    This is the critical safeguard: broken code is flagged, never silently passed on.
    """
    payload = {"files": [{"path": "app/bad.py", "content": _INVALID_CODE}]}
    monkeypatch.setenv("CLAUDE_API_KEY", "fake")
    target = "src.fullstack.generator.anthropic.Anthropic"
    with patch(target, return_value=_mock_claude(payload)):
        result = generate_feature(_FEATURE, _GUIDE, ["app/main.py"])
    assert result.syntax_ok is False
    assert len(result.syntax_errors) == 1
