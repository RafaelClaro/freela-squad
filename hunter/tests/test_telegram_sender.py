"""Tests for the Telegram sender — httpx is mocked, no real network calls."""

from unittest.mock import MagicMock, patch

from src import telegram_sender


def test_send_sucesso(monkeypatch):
    """A successful POST returns True."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    with patch("src.telegram_sender.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        result = telegram_sender.send_message("hello")

    assert result is True
    mock_post.assert_called_once()


def test_send_sem_credenciais_retorna_false(monkeypatch):
    """Missing credentials returns False without calling the API."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with patch("src.telegram_sender.httpx.post") as mock_post:
        result = telegram_sender.send_message("hello")

    assert result is False
    mock_post.assert_not_called()


def test_send_falha_de_rede_retorna_false(monkeypatch):
    """A network error returns False instead of raising (pipeline must not crash)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    with patch("src.telegram_sender.httpx.post", side_effect=Exception("network down")):
        result = telegram_sender.send_message("hello")

    assert result is False
