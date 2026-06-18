"""QA technical checker — runs the tooling on the generated project for hard facts.

This layer is deterministic: it shells out to pytest, ruff, and mypy in the target
project and reads the results. No Claude, no opinion — just what the tools report.
Coverage below 80%, a failing test, a stray print(), or a lint/type error are all
blockers under the squad's zero-bug rule.
"""

import logging
import re
import subprocess  # noqa: S404 - needed to run the project's own tooling

from src.qa.models import TechnicalChecks

logger = logging.getLogger(__name__)

_TIMEOUT = 300  # seconds; generated test suites are small


def _run(command: list[str], cwd: str) -> tuple[int, str]:
    """Run a command in cwd; return (returncode, combined output). Never raises."""
    try:
        result = subprocess.run(  # noqa: S603 - commands are squad tooling, not user input
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        return -1, f"command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return -1, f"timeout running: {' '.join(command)}"


def _has_print(project_dir: str) -> bool:
    """Return True if any non-test .py file under app/ contains a print( call."""
    import os

    pattern = re.compile(r"\bprint\s*\(")
    for root, _dirs, files in os.walk(os.path.join(project_dir, "app")):
        for name in files:
            if name.endswith(".py"):
                content = open(os.path.join(root, name), encoding="utf-8").read()
                if pattern.search(content):
                    return True
    return False


def run_checks(project_dir: str) -> TechnicalChecks:
    """Run pytest (with coverage), ruff, and mypy on the project; collect the facts."""
    checks = TechnicalChecks()

    # Tests + coverage in one run.
    code, output = _run(
        ["python", "-m", "pytest", "--cov=app", "--cov-report=term", "-q"], project_dir
    )
    checks.tests_passed = code == 0
    summary_match = re.search(r"(\d+ passed[^\n]*)", output)
    checks.tests_summary = summary_match.group(1) if summary_match else "no test summary"
    coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if coverage_match:
        checks.coverage_percent = float(coverage_match.group(1))
        checks.coverage_ok = checks.coverage_percent >= 80
    else:
        checks.notes.append("coverage not detected in pytest output")

    # Ruff.
    ruff_code, _ruff_out = _run(["python", "-m", "ruff", "check", "app", "tests"], project_dir)
    checks.ruff_clean = ruff_code == 0

    # MyPy.
    mypy_code, _mypy_out = _run(["python", "-m", "mypy", "app"], project_dir)
    checks.mypy_clean = mypy_code == 0

    # print() scan.
    checks.has_print_statements = _has_print(project_dir)

    logger.info(
        f"QA checks: tests={checks.tests_passed} cov={checks.coverage_percent}% "
        f"ruff={checks.ruff_clean} mypy={checks.mypy_clean} print={checks.has_print_statements}"
    )
    return checks
