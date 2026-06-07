"""Tests for the Telegram notification formatter — pure function, no Claude."""

from src.models import ScoreResult
from src.telegram_format import format_notification


def test_formata_oportunidade_normal(opportunities):
    """A normal opportunity shows the standard header and the score."""
    result = ScoreResult(
        score=9.0,
        classification="NOTIFICAR",
        rationale="Caso modelo, tudo alinhado.",
        alerts=[],
        national_flag=False,
    )
    text = format_notification(opportunities["1"], result)
    assert "Nova oportunidade" in text
    assert "9.0/10" in text
    assert opportunities["1"].title in text
    assert "$900" in text


def test_formata_com_alertas(opportunities):
    """When there are alerts, the alert block is included."""
    result = ScoreResult(
        score=4.5,
        classification="OBSERVAR",
        rationale="Escopo vago.",
        alerts=["cliente sem historico", "escopo vago"],
        national_flag=False,
    )
    text = format_notification(opportunities["5"], result)
    assert "Alertas" in text
    assert "cliente sem historico" in text
    assert "escopo vago" in text


def test_formata_brl_excepcional_usa_tag_nacional(opportunities):
    """The exceptional BRL case uses the national header and R$ symbol."""
    result = ScoreResult(
        score=5.5,
        classification="OBSERVAR",
        rationale="BRL excepcional.",
        alerts=[],
        national_flag=True,
    )
    text = format_notification(opportunities["6"], result)
    assert "OPORTUNIDADE NACIONAL" in text
    assert "R$" in text


def test_sem_alertas_nao_inclui_bloco(opportunities):
    """With no alerts, the alert block is omitted entirely."""
    result = ScoreResult(
        score=9.0,
        classification="NOTIFICAR",
        rationale="Tudo certo.",
        alerts=[],
        national_flag=False,
    )
    text = format_notification(opportunities["1"], result)
    assert "Alertas" not in text
