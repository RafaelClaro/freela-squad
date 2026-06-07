"""Tests for classifier orchestration and scoring — Claude is mocked."""

from unittest.mock import patch

from src import classifier, scoring


def test_eliminado_na_camada1_nao_chama_claude(opportunities):
    """#2 is cut in Camada 1, so Claude must NOT be called (cost protection)."""
    with patch("src.claude_client.score_opportunity") as mock_claude:
        result = classifier.qualify(opportunities["2"])
        assert result.classification == "DESCARTAR"
        mock_claude.assert_not_called()


def test_sobrevivente_chama_claude(opportunities):
    """#1 survives Camada 1, so Claude IS called for scoring."""
    fake = {
        "score": 9.0,
        "classification": "NOTIFICAR",
        "rationale": "Caso modelo, tudo alinhado.",
        "alerts": [],
        "national_flag": False,
    }
    with patch("src.claude_client.score_opportunity", return_value=fake) as mock_claude:
        result = classifier.qualify(opportunities["1"])
        assert result.classification == "NOTIFICAR"
        assert result.score == 9.0
        mock_claude.assert_called_once()


def test_brl_excepcional_recebe_flag(opportunities):
    """#6 (exceptional BRL) gets national_flag from Claude."""
    fake = {
        "score": 5.0,
        "classification": "OBSERVAR",
        "rationale": "BRL excepcional: valor alto, stack alinhada.",
        "alerts": [],
        "national_flag": True,
    }
    with patch("src.claude_client.score_opportunity", return_value=fake):
        result = classifier.qualify(opportunities["6"])
        assert result.classification == "OBSERVAR"
        assert result.national_flag is True


def test_resposta_malformada_degrada_para_observar(opportunities):
    """Malformed Claude output must degrade to OBSERVAR, not crash."""
    with patch("src.claude_client.score_opportunity", side_effect=ValueError("bad json")):
        result = scoring.score(opportunities["1"])
        assert result.classification == "OBSERVAR"
        assert result.alerts  # has a warning alert
