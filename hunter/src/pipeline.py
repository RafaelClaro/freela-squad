"""Pipeline orchestration — connects the squad's stages in sequence.

The flow mirrors the squad's real process:

    Hunter qualifies  ->  Rafael approves  ->  PO translates to spec

Rafael's approval sits between qualification and translation on purpose: the PO
(which costs Claude API calls) only runs on opportunities Rafael actually wants,
never automatically on everything the Hunter surfaces.
"""

import logging

from src import classifier
from src.arquiteto import decider
from src.arquiteto import formatter as arq_formatter
from src.arquiteto.models import ArchitectureDecision
from src.engenheiro import definer
from src.engenheiro import formatter as eng_formatter
from src.engenheiro.models import EngineeringGuide
from src.fullstack import formatter as fs_formatter
from src.fullstack import generator, planner, scaffolder
from src.fullstack.models import (
    Feature,
    FeatureImplementation,
    ImplementationPlan,
    Scaffold,
)
from src.models import Opportunity
from src.po import formatter, translator
from src.po.models import Spec

logger = logging.getLogger(__name__)


def qualify_opportunity(opportunity: Opportunity):
    """Stage 1 — Hunter qualifies a raw opportunity. Returns the ScoreResult."""
    result = classifier.qualify(opportunity)
    logger.info(
        f"Hunter: #{opportunity.id} -> {result.classification} (score {result.score:.1f})"
    )
    return result


def translate_to_spec(opportunity: Opportunity) -> Spec:
    """Stage 3 — PO translates an APPROVED opportunity into a technical spec.

    This runs only after Rafael's approval (stage 2), so it is a separate call,
    not chained automatically onto qualification.
    """
    logger.info(f"PO: translating #{opportunity.id} into a spec")
    spec = translator.translate(opportunity)
    if spec.untranslatable:
        logger.warning(f"PO: #{opportunity.id} is untranslatable — {spec.untranslatable_reason}")
    return spec


def spec_to_markdown(spec: Spec) -> str:
    """Render an approved spec as markdown for Rafael to read and hand to the Arquiteto."""
    return formatter.to_markdown(spec)


def decide_architecture(spec: Spec, opportunity: Opportunity) -> ArchitectureDecision:
    """Stage 4 — Arquiteto assesses the spec and emits a binding Go/No-go.

    The Arquiteto can veto an opportunity the Hunter approved (e.g. implied rate
    below the squad's floor), so this is the real viability gate.
    """
    logger.info(f"Arquiteto: deciding on #{opportunity.id}")
    decision = decider.decide(spec, opportunity)
    verdict = "GO" if decision.go else "NO-GO"
    logger.info(
        f"Arquiteto: #{opportunity.id} -> {verdict} "
        f"({decision.estimated_hours:.0f}h, ${decision.implied_rate:.0f}/h)"
    )
    return decision


def decision_to_markdown(decision: ArchitectureDecision) -> str:
    """Render the architecture decision as markdown for Rafael."""
    return arq_formatter.to_markdown(decision)


def define_standards(decision: ArchitectureDecision) -> EngineeringGuide:
    """Stage 5 — Engenheiro defines the binding engineering standards for the Dev.

    Runs only on a Go decision. Carries the squad's fixed standards plus the
    project-specific guidance derived from the architecture.
    """
    logger.info(f"Engenheiro: defining standards for {decision.project_name}")
    guide = definer.define(decision)
    logger.info(
        f"Engenheiro: {len(guide.custom_exceptions)} custom exceptions, "
        f"{len(guide.testing_guidance)} testing guidelines"
    )
    return guide


def guide_to_markdown(guide: EngineeringGuide) -> str:
    """Render the engineering guide as markdown for the Dev."""
    return eng_formatter.to_markdown(guide)


def plan_implementation(spec: Spec, decision: ArchitectureDecision) -> ImplementationPlan:
    """Stage 6a — Fullstack breaks the project into ordered, testable features."""
    logger.info(f"Fullstack: planning features for {spec.project_name}")
    implementation_plan = planner.plan(spec, decision)
    logger.info(f"Fullstack: {len(implementation_plan.features)} features planned")
    return implementation_plan


def plan_to_markdown(implementation_plan: ImplementationPlan) -> str:
    """Render the implementation plan as markdown."""
    return fs_formatter.to_markdown(implementation_plan)


def build_project_scaffold(project_name: str) -> Scaffold:
    """Stage 6b — Fullstack generates the runnable skeleton (deterministic)."""
    logger.info(f"Fullstack: scaffolding {project_name}")
    return scaffolder.build_scaffold(project_name)


def write_scaffold_to_disk(scaffold: Scaffold, target_dir: str) -> list[str]:
    """Write the scaffold files under target_dir. Returns the paths written.

    This materializes a client project on disk — separate from the squad's own
    code. Creates parent folders as needed.
    """
    import os

    written = []
    for generated in scaffold.files:
        full_path = os.path.join(target_dir, generated.path)
        os.makedirs(os.path.dirname(full_path) or target_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as handle:
            handle.write(generated.content)
        written.append(full_path)
    logger.info(f"Fullstack: wrote {len(written)} files to {target_dir}")
    return written


def implement_feature(
    feature: "Feature",
    guide: "EngineeringGuide",
    existing_files: list[str],
) -> FeatureImplementation:
    """Stage 6c — Fullstack generates the code for one feature (syntax-validated)."""
    logger.info(f"Fullstack: implementing feature '{feature.name}'")
    result = generator.generate_feature(feature, guide, existing_files)
    if result.syntax_ok:
        logger.info(f"Fullstack: '{feature.name}' generated {len(result.files)} valid files")
    else:
        logger.warning(f"Fullstack: '{feature.name}' has syntax errors: {result.syntax_errors}")
    return result


def write_feature_to_disk(
    implementation: FeatureImplementation, target_dir: str
) -> list[str]:
    """Write a feature's files to disk — only if syntax is valid.

    Refuses to write invalid Python, so broken code never lands in the project.
    """
    import os

    if not implementation.syntax_ok:
        raise ValueError(
            f"Refusing to write '{implementation.feature_name}': syntax errors "
            f"{implementation.syntax_errors}"
        )
    written = []
    for generated in implementation.files:
        full_path = os.path.join(target_dir, generated.path)
        os.makedirs(os.path.dirname(full_path) or target_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as handle:
            handle.write(generated.content)
        written.append(full_path)
    logger.info(f"Fullstack: wrote feature '{implementation.feature_name}' ({len(written)} files)")
    return written
