"""Render a Spec as markdown, following the squad's spec-template layout.

The Spec object is what the Arquiteto consumes; this markdown is what Rafael
reads and approves. Same content, human-friendly shape.
"""

from src.po.models import Spec


def _bullets(items: list[str]) -> str:
    """Render a list as markdown bullets, or a placeholder if empty."""
    if not items:
        return "- (nenhum)"
    return "\n".join(f"- {item}" for item in items)


def to_markdown(spec: Spec) -> str:
    """Render a Spec into the squad's standard markdown spec format."""
    if spec.untranslatable:
        return (
            f"# Spec: {spec.project_name or 'BRIEFING INTRADUZÍVEL'}\n\n"
            f"⚠️ **Briefing intraduzível.** {spec.untranslatable_reason}\n\n"
            f"O Hunter deixou passar uma oportunidade sem informação técnica "
            f"aproveitável. Recomenda-se descartar."
        )

    io_table = "| Entrada | Origem | Saída | Destino |\n|---|---|---|---|\n"
    if spec.io_pairs:
        for pair in spec.io_pairs:
            io_table += f"| {pair.input} | {pair.source} | {pair.output} | {pair.destination} |\n"
    else:
        io_table += "| (a definir) | | | |\n"

    notes = (
        f"\n## Observações para o Arquiteto\n{spec.notes_for_architect}\n"
        if spec.notes_for_architect
        else ""
    )

    return (
        f"# Spec: {spec.project_name}\n\n"
        f"## Objetivo\n{spec.objective}\n\n"
        f"## Entregáveis\n{_bullets(spec.deliverables)}\n\n"
        f"## Requisitos funcionais\n{_bullets(spec.functional_requirements)}\n\n"
        f"## Fora de escopo\n{_bullets(spec.out_of_scope)}\n\n"
        f"## Entradas e saídas\n{io_table}\n"
        f"## Critérios de aceite\n{_bullets(spec.acceptance_criteria)}\n\n"
        f"## Premissas assumidas\n{_bullets(spec.assumptions)}\n"
        f"{notes}"
    )
