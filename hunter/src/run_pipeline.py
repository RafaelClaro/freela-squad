"""Interactive pipeline runner — test the squad end to end, locally.

Flow:
  1. Hunter qualifies every opportunity from a collector.
  2. The ones worth pursuing (NOTIFICAR / OBSERVAR) are listed.
  3. You pick one to "approve" — and the PO translates it into a spec, live.

This is the squad working end to end on the two stages built so far, without
depending on Upwork or Freelancer. Run with:  python -m src.run_pipeline
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from src import pipeline
from src.collectors.manual import ManualCollector

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    """Run the Hunter, list qualified opportunities, then PO-translate a chosen one."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    input_path = Path(args[0]) if args else Path("tests/fixtures/briefings.json")

    opportunities = ManualCollector(input_path).collect()

    # Stage 1 — Hunter qualifies everything.
    print("\n=== STAGE 1: Hunter qualifying ===\n")
    qualified = []
    total = len(opportunities)
    for number, opp in enumerate(opportunities, start=1):
        print(f"  Qualificando {number}/{total}: #{opp.id} {opp.title[:40]}... ", flush=True)
        result = pipeline.qualify_opportunity(opp)
        print(f"     -> {result.classification} (score {result.score:.1f})", flush=True)
        if result.classification in ("NOTIFICAR", "OBSERVAR"):
            qualified.append(opp)

    if not qualified:
        print("\nNo opportunities worth pursuing. Done.")
        return

    # Stage 2 — Rafael approves (here: pick one from the list).
    print("\n=== STAGE 2: Approval — opportunities worth pursuing ===\n")
    for index, opp in enumerate(qualified, start=1):
        print(f"  {index}) {opp.title}")

    choice = input(
        f"\nDigite o número (1 a {len(qualified)}) para aprovar e enviar ao PO "
        f"(ou Enter para pular): "
    ).strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(qualified)):
        print("Nada aprovado. Fim.")
        return

    # Stage 3 — PO translates the approved one into a spec.
    approved = qualified[int(choice) - 1]
    print(f"\n=== STAGE 3: PO translating #{approved.id} ===\n")
    spec = pipeline.translate_to_spec(approved)
    print(pipeline.spec_to_markdown(spec))

    if spec.untranslatable:
        print("\nSpec intraduzível — não segue para o Arquiteto.")
        return

    # Stage 4 — Arquiteto decides Go/No-go.
    print(f"\n=== STAGE 4: Arquiteto deciding on #{approved.id} ===\n")
    decision = pipeline.decide_architecture(spec, approved)
    print(pipeline.decision_to_markdown(decision))


if __name__ == "__main__":
    main()
