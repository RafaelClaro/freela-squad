"""Generate ONE feature's code into an existing scaffolded project.

This is the incremental implementation loop: pick a feature, generate its code
(syntax-validated), write it to the project, then YOU run pytest to confirm it
works before moving to the next. Run with:

    python -m src.run_feature <project_dir>

It uses a small demo feature + guide so you can see the generator working end to
end. In real use, the feature and guide come from the pipeline (plan + Engenheiro).
"""

import os
import sys

from dotenv import load_dotenv

from src import pipeline
from src.engenheiro.models import CustomException, EngineeringGuide
from src.fullstack.models import Feature

load_dotenv()


def main() -> None:
    """Generate a demo feature's code into the given project directory."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Uso: python -m src.run_feature <pasta_do_projeto>")
        return
    project_dir = args[0]

    # Demo feature + guide (in real use these come from the pipeline).
    feature = Feature(
        order=1,
        name="Items CRUD endpoint",
        description=(
            "Add a simple in-memory Items resource: a Pydantic Item schema "
            "(id: int, name: str), an in-memory list, and FastAPI routes "
            "POST /items (create) and GET /items (list). Wire the router into "
            "app.main. No database — keep it in memory for this feature."
        ),
        test_focus="POST /items creates an item; GET /items returns the created items.",
    )
    guide = EngineeringGuide(
        project_name="Demo",
        custom_exceptions=[
            CustomException(name="ValidationError", when_raised="invalid input", http_status=400)
        ],
    )

    # Existing files: list what's already in the scaffold so the generator fits in.
    existing = []
    for root, _dirs, files in os.walk(project_dir):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), project_dir)
            existing.append(rel.replace(os.sep, "/"))

    print(f"\nGerando feature '{feature.name}' em {project_dir}...\n")
    implementation = pipeline.implement_feature(feature, guide, existing)

    if not implementation.syntax_ok:
        print("Código gerado tem erros de sintaxe — NÃO foi escrito:")
        for error in implementation.syntax_errors:
            print(f"  - {error}")
        print("\nTente rodar de novo (o modelo varia) ou simplifique a feature.")
        return

    written = pipeline.write_feature_to_disk(implementation, project_dir)
    print(f"{len(written)} arquivos escritos:")
    for path in written:
        print(f"  - {path}")
    print(f"\nAgora rode os testes no projeto:\n  cd {project_dir}\n  pytest")


if __name__ == "__main__":
    main()
