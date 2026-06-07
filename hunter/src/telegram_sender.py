"""Sends notifications to Telegram via the Bot API.

Credentials come from environment variables, never hardcoded.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
_TIMEOUT_SECONDS = 10.0


def send_message(text: str) -> bool:
    """Send one Markdown message to the configured Telegram chat.

    Returns True on success, False on failure (never raises — a failed
    notification must not crash the Hunter pipeline).
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error("Telegram credentials missing (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False

    url = _TELEGRAM_API_URL.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        response = httpx.post(url, json=payload, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info("Telegram notification sent")
        return True
    except Exception as error:  # noqa: BLE001 - a failed send must not crash the run
        logger.error(f"Failed to send Telegram notification: {error}")
        return False
