"""Render an ImplementationPlan as markdown — the build plan for the Dev to follow."""

from src.fullstack.models import ImplementationPlan


def to_markdown(plan: ImplementationPlan) -> str:
    """Render the implementation plan: ordered features with what to build and test."""
    if not plan.features:
        return f"# Plano de Implementação: {plan.project_name}\n\n- (nenhuma feature)"

    setup = f"\n**Setup:** {plan.setup_notes}\n" if plan.setup_notes else ""

    lines = [f"# Plano de Implementação: {plan.project_name}\n", setup]
    lines.append(f"\n{len(plan.features)} features, construídas e testadas em ordem:\n")
    for feature in plan.features:
        lines.append(
            f"\n### {feature.order}. {feature.name}\n"
            f"**Construir:** {feature.description}\n\n"
            f"**Testar:** {feature.test_focus}\n"
        )
    return "".join(lines)
