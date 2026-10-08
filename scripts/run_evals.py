"""Rapport reproductible; sortie non nulle si une vérification échoue."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluations.runner import run_suite  # noqa: E402
from hydro_agent.config import Settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Dix évaluations isolées du PoC.")
    parser.add_argument(
        "--provider", choices=["regression", "openrouter", "foundry"], default="regression"
    )
    parser.add_argument("--output", type=Path, default=Path(".hydro/evaluations"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="hydro-evals-", dir=args.output) as directory:
        report = asyncio.run(run_suite(Settings(), Path(directory), provider=args.provider))
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    lines = [
        f"# Évaluations — {report['provider']}",
        "",
        f"Résultats observés : {report['passed']}/{report['total']}.",
        "",
        "| Cas | Résultat | Réussite |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        f"| {row['case']} | {row['outcome']} | {row['passed']} |" for row in report["cases"]
    )
    lines += [
        "",
        "Régression programmée ≠ mesure de performance d’un LLM autonome.",
        "Contrôles structurels, sans vérification sémantique de chaque phrase.",
    ]
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(f"{report['passed']}/{report['total']} — {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] == report["total"] else 1)


if __name__ == "__main__":
    main()
