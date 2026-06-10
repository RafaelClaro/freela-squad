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
