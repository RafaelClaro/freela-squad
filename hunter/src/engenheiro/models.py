"""Data models for the Engenheiro (Senior Engineer) step.

The Engenheiro produces an EngineeringGuide: the binding technical standards the
Dev must follow. It has two layers — the squad's fixed standards (constant across
every project) and project-specific guidance derived from the architecture.
"""

from dataclasses import dataclass, field

# The squad's fixed engineering standards. These never change per project — they
# are the squad's DNA. The Engenheiro always enforces them; Claude only adds the
# project-specific layer on top.
SQUAD_STANDARDS: list[str] = [
    "Type hints obrigatórios em todas as funções públicas (MyPy valida)",
    "Docstrings em funções públicas e classes",
    "Sem print() — apenas logging estruturado",
    "Nenhuma credencial hardcoded — tudo em variáveis de ambiente (.env)",
    "Máximo 100 caracteres por linha",
    "Imports organizados, sem imports não utilizados",
    "Nomes descritivos (get_user_by_id, não get_user)",
    "Funções pequenas, responsabilidade única",
    "Cobertura de testes ≥ 80% (Pytest + Pytest-cov)",
    "Tratamento de erro com HTTP status semântico (400, 401, 404, 409, 500)",
    "Black, Ruff e MyPy devem passar sem erro antes de entregar",
]


@dataclass
class CustomException:
    """A project-specific custom exception the Dev should implement."""

    name: str
    when_raised: str
    http_status: int


@dataclass
class EngineeringGuide:
    """The binding engineering standards for one project.

    squad_standards is the fixed layer (always present). Everything else is the
    project-specific layer the Engenheiro derives from the architecture decision.
    """

    project_name: str
    squad_standards: list[str] = field(default_factory=lambda: list(SQUAD_STANDARDS))

    # Project-specific layer (derived from the architecture).
    custom_exceptions: list[CustomException] = field(default_factory=list)
    logging_guidance: list[str] = field(default_factory=list)
    testing_guidance: list[str] = field(default_factory=list)
    quality_alerts: list[str] = field(default_factory=list)
