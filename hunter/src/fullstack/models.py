"""Data models for the Fullstack (Developer) step.

The Fullstack Dev does not generate a whole project at once — that is a recipe for
broken code. It works incrementally: break the spec into small, testable features,
then build and test them one at a time. These models carry the plan and the
generated artifacts.
"""

from dataclasses import dataclass, field


@dataclass
class Feature:
    """One small, independently implementable and testable unit of work.

    A feature is intentionally small — something a developer could build and test
    in one sitting (e.g. "NF-e SQLAlchemy model", "POST /nfe endpoint with
    validation"). Big features are a smell; they should be split further.
    """

    order: int  # build order (dependencies come first)
    name: str
    description: str  # what to build
    test_focus: str  # what the test for this feature must cover


@dataclass
class ImplementationPlan:
    """The ordered breakdown of a project into testable features.

    This is what the Fullstack produces first — a build plan. Each feature is
    implemented and tested before the next, so a failure is always localized.
    """

    project_name: str
    features: list[Feature] = field(default_factory=list)
    setup_notes: str = ""  # any setup the scaffold needs before features start


@dataclass
class GeneratedFile:
    """One file the Fullstack generated, with its path relative to the project root."""

    path: str  # e.g. "src/models/nfe.py"
    content: str


@dataclass
class Scaffold:
    """The initial runnable skeleton of a project.

    Not the full project — the starting point: folder structure, a FastAPI app that
    boots, a /health endpoint, and one passing test. Features build on top of this.
    """

    project_name: str
    files: list[GeneratedFile] = field(default_factory=list)


@dataclass
class FeatureImplementation:
    """The code generated for one feature: its files plus a syntax-validity flag.

    syntax_ok is False if any generated Python file failed to parse — the caller
    should not write invalid code to disk. syntax_errors explains what failed.
    """

    feature_name: str
    files: list[GeneratedFile] = field(default_factory=list)
    syntax_ok: bool = True
    syntax_errors: list[str] = field(default_factory=list)
