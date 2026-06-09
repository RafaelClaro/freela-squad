"""Formats the Telegram notification message (does not send — that is Fatia 2)."""

from src.models import Opportunity, ScoreResult


def format_notification(opportunity: Opportunity, result: ScoreResult) -> str:
    """Build the Markdown notification text for a qualified opportunity."""
    header = (
        "\U0001f1e7\U0001f1f7 *OPORTUNIDADE NACIONAL"
        if result.national_flag
        else "\U0001f3af *Nova oportunidade"
    )
    currency_symbol = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "BRL": "R$"}.get(
        opportunity.currency, opportunity.currency + " "
    )

    lines = [
        f"{header} — Score {result.score:.1f}/10*",
        "",
        f"\U0001f4cc *{opportunity.title}*",
        f"\U0001f310 Plataforma: {opportunity.platform}",
        f"\U0001f4b0 Valor: {currency_symbol}{opportunity.budget:g} ({opportunity.price_model})",
        f"\U0001f4dd *Analise:* {result.rationale}",
    ]

    if result.alerts:
        lines.append("")
        lines.append("\u26a0\ufe0f *Alertas:*")
        lines.extend(f"- {alert}" for alert in result.alerts)

    return "\n".join(lines)
