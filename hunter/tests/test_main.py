"""Tests for the main entrypoint — Claude is mocked, runs against the fixtures."""

from pathlib import Path
from unittest.mock import patch

from src import main
from src.collectors.manual import ManualCollector

FIXTURES = Path(__file__).parent / "fixtures" / "briefings.json"


def _fake_score():
    return {
        "score": 9.0,
        "classification": "NOTIFICAR",
        "rationale": "ok",
        "alerts": [],
        "national_flag": False,
    }


def test_run_executa_pipeline_completo(capsys):
    """run() in dry-run mode qualifies every opportunity and prints, without sending."""
    collector = ManualCollector(FIXTURES)
    with patch("src.claude_client.score_opportunity", return_value=_fake_score()):
        main.run(collector, dry_run=True)

    output = capsys.readouterr().out
    assert "Nova oportunidade" in output


def test_run_envia_quando_nao_dry_run():
    """run() without dry-run calls the Telegram sender for qualified opportunities."""
    collector = ManualCollector(FIXTURES)
    with patch("src.claude_client.score_opportunity", return_value=_fake_score()), patch(
        "src.telegram_sender.send_message"
    ) as mock_send:
        main.run(collector, dry_run=False)

    assert mock_send.called
