"""Tests for the JSON extraction helper — covers the formats Claude may return."""

import pytest

from src.claude_client import _extract_json


def test_json_puro():
    """Plain JSON parses directly."""
    result = _extract_json('{"score": 9.0, "classification": "NOTIFICAR"}')
    assert result["score"] == 9.0
    assert result["classification"] == "NOTIFICAR"


def test_json_com_fences():
    """JSON wrapped in ```json fences is unwrapped and parsed."""
    text = '```json\n{"score": 7.0, "classification": "OBSERVAR"}\n```'
    result = _extract_json(text)
    assert result["score"] == 7.0


def test_json_com_fences_sem_label():
    """JSON wrapped in plain ``` fences (no json label) is parsed."""
    text = '```\n{"national_flag": true, "score": 5.5}\n```'
    result = _extract_json(text)
    assert result["national_flag"] is True


def test_json_com_texto_antes():
    """JSON preceded by prose is extracted from the first {...} block."""
    text = 'Aqui esta a analise:\n{"score": 8.0, "classification": "NOTIFICAR"}'
    result = _extract_json(text)
    assert result["score"] == 8.0


def test_texto_sem_json_levanta_erro():
    """Text with no JSON object raises, so scoring can degrade gracefully."""
    with pytest.raises(Exception):
        _extract_json("desculpe, nao consegui analisar")


def test_extract_json_tolera_trailing_comma():
    """The model sometimes emits trailing commas; _extract_json tolerates them."""
    from src.claude_client import _extract_json

    assert _extract_json('{"files": [{"path": "a.py"},]}')["files"][0]["path"] == "a.py"
    assert _extract_json('{"value": 5,}')["value"] == 5
    assert _extract_json('{"a": [1, 2,], "b": {"c": 3,},}')["b"]["c"] == 3


def test_extract_json_nao_corrompe_string_interna():
    """Trailing-comma cleanup must not touch commas inside string values."""
    from src.claude_client import _extract_json

    assert _extract_json('{"code": "items = [1, 2]"}')["code"] == "items = [1, 2]"