"""Tests for the main entrypoint — Claude is mocked, runs against the fixtures."""

from pathlib import Path
from unittest.mock import patch

from src import main

FIXTURES = Path(__file__).parent / "fixtures" / "briefings.json"


def test_load_opportunities_le_os_seis():
    """load_opportunities reads all 6 briefings into Opportunity objects."""
    opportunities = main.load_opportunities(FIXTURES)
    assert len(opportunities) == 6
    assert opportunities[0].id == "1"


def test_run_executa_pipeline_completo(capsys):
    """run() in dry-run mode qualifies every opportunity and prints, without sending."""
    fake = {
        "score": 9.0,
        "classification": "NOTIFICAR",
        "rationale": "ok",
        "alerts": [],
        "national_flag": False,
    }
    with patch("src.claude_client.score_opportunity", return_value=fake):
        main.run(FIXTURES, dry_run=True)

    output = capsys.readouterr().out
    # At least the clean USD project should produce a printed notification.
    assert "Nova oportunidade" in output


def test_run_envia_quando_nao_dry_run():
    """run() without dry-run calls the Telegram sender for qualified opportunities."""
    fake = {
        "score": 9.0,
        "classification": "NOTIFICAR",
        "rationale": "ok",
        "alerts": [],
        "national_flag": False,
    }
    with (
        patch("src.claude_client.score_opportunity", return_value=fake),
        patch("src.telegram_sender.send_message") as mock_send,
    ):
        main.run(FIXTURES, dry_run=False)

    # Sender was called at least once for the qualified opportunities.
    assert mock_send.called
