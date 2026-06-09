"""Render an ArchitectureDecision as markdown for Rafael to read.

A No-go renders short and clear (the blocking reason). A Go renders the full
decision: estimate, validated rate, and architecture.
"""

from src.arquiteto.models import ArchitectureDecision


def to_markdown(decision: ArchitectureDecision) -> str:
    """Render an ArchitectureDecision into readable markdown."""
    if not decision.go:
        rate_line = ""
        if decision.implied_rate:
            rate_line = (
                f"\n**Taxa implícita:** ${decision.implied_rate:.2f}/h "
                f"({decision.estimated_hours:.0f}h estimadas)\n"
            )
        return (
            f"# Decisão Arquitetural: {decision.project_name}\n\n"
            f"## ❌ NO-GO\n\n"
            f"**Motivo:** {decision.reason}\n"
            f"{rate_line}"
        )

    deps = "| Dependência | Justificativa | Risco |\n|---|---|---|\n"
    if decision.dependencies:
        for dep in decision.dependencies:
            deps += f"| {dep.name} | {dep.reason} | {dep.risk} |\n"
    else:
        deps += "| (padrão do squad) | | baixo |\n"

    alerts = (
        "\n".join(f"- {alert}" for alert in decision.technical_alerts)
        if decision.technical_alerts
        else "- (nenhum)"
    )

    notes = (
        f"\n## Notas de arquitetura\n{decision.architecture_notes}\n"
        if decision.architecture_notes
        else ""
    )

    return (
        f"# Decisão Arquitetural: {decision.project_name}\n\n"
        f"## ✅ GO\n\n"
        f"{decision.reason}\n\n"
        f"## Estimativa\n"
        f"- Horas estimadas: {decision.estimated_hours:.0f}h\n"
        f"- Taxa implícita: ${decision.implied_rate:.2f}/h\n"
        f"- Prazo realista: {decision.realistic_days} dias úteis\n\n"
        f"## Stack\n"
        f"- Banco: {decision.database}\n"
        f"- Autenticação: {decision.auth_type}\n\n"
        f"## Estrutura de pastas\n```\n{decision.folder_structure}\n```\n\n"
        f"## Dependências críticas\n{deps}\n"
        f"## Alertas para o Engenheiro\n{alerts}\n"
        f"{notes}"
    )
