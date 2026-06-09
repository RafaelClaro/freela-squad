"""Pipeline orchestration — connects the squad's stages in sequence.

The flow mirrors the squad's real process:

    Hunter qualifies  ->  Rafael approves  ->  PO translates to spec

Rafael's approval sits between qualification and translation on purpose: the PO
(which costs Claude API calls) only runs on opportunities Rafael actually wants,
never automatically on everything the Hunter surfaces.
"""

import logging

from src import classifier
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
