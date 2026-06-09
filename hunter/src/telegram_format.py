"""Formats the Telegram notification message (does not send — that is Fatia 2)."""

from src.models import Opportunity, ScoreResult


def format_notification(opportunity: Opportunity, result: ScoreResult) -> str:
    """Build the Markdown notification text for a qualified opportunity."""
    header = (
        "\U0001F1E7\U0001F1F7 *OPORTUNIDADE NACIONAL"
        if result.national_flag
        else "\U0001F3AF *Nova oportunidade"
    )
    currency_symbol = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "BRL": "R$"}.get(
        opportunity.currency, opportunity.currency + " "
    )

    lines = [
        f"{header} — Score {result.score:.1f}/10*",
        "",
        f"\U0001F4CC *{opportunity.title}*",
        f"\U0001F310 Plataforma: {opportunity.platform}",
        f"\U0001F4B0 Valor: {currency_symbol}{opportunity.budget:g} ({opportunity.price_model})",
        f"\U0001F4DD *Analise:* {result.rationale}",
    ]

    if result.alerts:
        lines.append("")
        lines.append("\u26A0\uFE0F *Alertas:*")
        lines.extend(f"- {alert}" for alert in result.alerts)

    return "\n".join(lines)
