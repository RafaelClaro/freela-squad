"""The Fullstack feature generator — generates the code for ONE feature.

This is the hardest step in the squad: producing code that actually runs. The
safeguard is mandatory syntax validation — every generated Python file is parsed
with ast before being returned, so invalid code never reaches disk. The caller
then runs the tests to confirm the feature actually works.
"""

import ast
import os

import anthropic

from src.claude_client import _extract_json
from src.engenheiro.models import EngineeringGuide
from src.fullstack.models import Feature, FeatureImplementation, GeneratedFile

_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = """You are the Fullstack Developer of an autonomous Python squad.
You implement ONE feature at a time, generating working code that fits the existing
project. You do not redesign — you follow the architecture and standards given.

You receive: the feature to build, the engineering standards, and the list of files
that already exist in the project. Generate ONLY the files needed for THIS feature
(new files, or full replacements of existing ones). Each file must be complete and
runnable — never a fragment or a "..." placeholder.

Rules:
- Python 3.11+, FastAPI, SQLAlchemy, Pydantic, Pytest — the squad stack.
- Use modern built-in generics: list[int], dict[str, int], str | None. NEVER import
  List, Dict, Optional from typing — and NEVER write "from typing import list"
  (list/dict are built-ins, not importable from typing).
- Follow the engineering standards: type hints, docstrings, no print (use logging),
  no hardcoded secrets, semantic HTTP codes, lines under 100 chars.
- Every feature includes its test file. Tests must be runnable with pytest.
- Imports must be correct and consistent with existing files (app.* layout).
- Each file must be valid, complete Python — it will be parsed and must not error.

Respond with ONLY a JSON object, no markdown, no preamble:
{
  "files": [
    {"path": "app/models/nfe.py", "content": "<complete file content>"},
    {"path": "tests/test_nfe_model.py", "content": "<complete test file>"}
  ]
}"""


def _build_user_content(
    feature: Feature, guide: EngineeringGuide, existing_files: list[str]
) -> str:
    """Render the feature, standards, and existing files into the generator input."""
    existing = "\n".join(f"- {path}" for path in existing_files)
    exceptions = "\n".join(
        f"- {exc.name} ({exc.http_status}): {exc.when_raised}"
        for exc in guide.custom_exceptions
    )
    return (
        f"FEATURE TO BUILD:\n{feature.name}\n{feature.description}\n\n"
        f"TEST MUST COVER:\n{feature.test_focus}\n\n"
        f"CUSTOM EXCEPTIONS AVAILABLE:\n{exceptions}\n\n"
        f"FILES ALREADY IN THE PROJECT:\n{existing}\n\n"
        f"Generate the files for this feature, including its test."
    )


def _validate_syntax(files: list[GeneratedFile]) -> list[str]:
    """Parse every Python file; return a list of error messages (empty if all valid)."""
    errors = []
    for generated in files:
        if generated.path.endswith(".py") and generated.content.strip():
            try:
                ast.parse(generated.content)
            except SyntaxError as error:
                errors.append(f"{generated.path}: {error.msg} (line {error.lineno})")
    return errors


def generate_feature(
    feature: Feature, guide: EngineeringGuide, existing_files: list[str]
) -> FeatureImplementation:
    """Generate the code for one feature, validating Python syntax before returning."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=8000,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_content(feature, guide, existing_files)}
        ],
    )
    block = response.content[0]
    if block.type != "text":
        raise ValueError(f"Unexpected response block type: {block.type}")
    if response.stop_reason == "max_tokens":
        raise ValueError(
            f"Feature '{feature.name}' code was truncated (hit max_tokens). "
            "The feature may be too large; split it further."
        )

    data = _extract_json(block.text)
    files = [
        GeneratedFile(path=item.get("path", ""), content=item.get("content", ""))
        for item in data.get("files", [])
    ]
    errors = _validate_syntax(files)
    return FeatureImplementation(
        feature_name=feature.name,
        files=files,
        syntax_ok=not errors,
        syntax_errors=errors,
    )
