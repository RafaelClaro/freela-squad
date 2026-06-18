"""Render a QAReport as markdown — the validation report Rafael reads."""

from src.qa.models import QAReport


def _check(ok: bool) -> str:
    """Return a check or cross mark for a boolean."""
    return "✅" if ok else "❌"


def to_markdown(report: QAReport) -> str:
    """Render the QA report: verdict, technical checks, functional findings, bugs."""
    tech = report.technical
    verdict = "✅ GO" if report.go else "❌ NO-GO"

    findings = ""
    for finding in report.functional_findings:
        findings += f"- {_check(finding.covered)} {finding.requirement}"
        findings += f" — {finding.note}\n" if finding.note else "\n"
    if not findings:
        findings = "- (nenhum requisito avaliado)\n"

    bugs = (
        "\n".join(f"- {bug}" for bug in report.bugs)
        if report.bugs
        else "- Nenhum"
    )

    rodape = (
        "> Pronto para entrega."
        if report.go
        else "> Volta para o Dev — qualquer item ❌ bloqueia."
    )

    return (
        f"# Relatório de QA: {report.project_name}\n\n"
        f"## {verdict}\n\n"
        f"{report.summary}\n\n"
        f"## Validação técnica (objetiva)\n"
        f"- {_check(tech.tests_passed)} Testes: {tech.tests_summary}\n"
        f"- {_check(tech.coverage_ok)} Cobertura: {tech.coverage_percent:.0f}% (alvo ≥ 80%)\n"
        f"- {_check(tech.ruff_clean)} Ruff limpo\n"
        f"- {_check(tech.mypy_clean)} MyPy limpo\n"
        f"- {_check(not tech.has_print_statements)} Sem print() no código\n\n"
        f"## Validação funcional (contra a spec)\n{findings}\n"
        f"## Bugs encontrados\n{bugs}\n\n"
        f"{rodape}\n"
    )
