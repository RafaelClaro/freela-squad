"""Render an EngineeringGuide as markdown — the standards doc the Dev follows."""

from src.engenheiro.models import EngineeringGuide


def _bullets(items: list[str]) -> str:
    """Render a list as markdown bullets, or a placeholder if empty."""
    return "\n".join(f"- {item}" for item in items) if items else "- (nenhum)"


def to_markdown(guide: EngineeringGuide) -> str:
    """Render the engineering guide: fixed squad standards + project-specific layer."""
    exceptions = "| Exceção | Quando | HTTP |\n|---|---|---|\n"
    if guide.custom_exceptions:
        for exc in guide.custom_exceptions:
            exceptions += f"| {exc.name} | {exc.when_raised} | {exc.http_status} |\n"
    else:
        exceptions += "| AppException | erro genérico | 500 |\n"

    return (
        f"# Padrões de Engenharia: {guide.project_name}\n\n"
        f"## Padrões fixos do squad (sempre valem)\n"
        f"{_bullets(guide.squad_standards)}\n\n"
        f"## Exceções customizadas (deste projeto)\n{exceptions}\n"
        f"## Logging\n{_bullets(guide.logging_guidance)}\n\n"
        f"## Testes\n{_bullets(guide.testing_guidance)}\n\n"
        f"## Alertas de qualidade para o Dev\n{_bullets(guide.quality_alerts)}\n"
    )
