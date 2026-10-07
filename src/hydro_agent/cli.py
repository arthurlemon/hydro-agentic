"""Commandes humaines : l’approbation n’est jamais un outil de l’agent."""

import argparse
import asyncio
import json
import sys
from typing import Any

from pydantic import ValidationError

from hydro_agent.agent.loop import investigate
from hydro_agent.agent.model import OpenRouterModel
from hydro_agent.config import Settings
from hydro_agent.mcp.client import connect
from hydro_agent.mcp.server import build_registry
from hydro_agent.models import DomainError
from hydro_agent.services.data import DataService
from hydro_agent.state.postgres import IncidentRepository


async def run(args: argparse.Namespace, settings: Settings) -> dict[str, Any]:
    repository = IncidentRepository(settings.database_url.get_secret_value())
    if args.command == "investigate":
        model = OpenRouterModel(
            settings.openrouter_api_key.get_secret_value(), settings.openrouter_model
        )
        state = repository.begin(DataService(settings.data_dir).get_event(args.event_id))
        incident_id = state["incident_id"]
        if args.transport == "mcp":
            async with connect(settings, incident_id, prepare=args.prepare) as remote:
                await investigate(
                    model,
                    remote,
                    repository,
                    incident_id,
                    max_steps=settings.max_steps,
                    prepare=args.prepare,
                )
        else:
            tools = build_registry(settings, incident_id, prepare=args.prepare)
            await investigate(
                model,
                tools,
                repository,
                incident_id,
                max_steps=settings.max_steps,
                prepare=args.prepare,
            )
        return repository.get(incident_id)
    incident_id = args.incident_id
    if args.command == "approve":
        return repository.approve(incident_id, settings.identity)
    if args.command == "reject":
        return repository.reject(incident_id, settings.identity)
    if args.command == "resume":
        # Reprise déterministe : le brouillon approuvé existe déjà; aucun LLM nécessaire.
        return repository.create_order(incident_id, settings.identity)
    return repository.get(incident_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigation d’actifs synthétiques — PoC local.")
    commands = parser.add_subparsers(dest="command", required=True)
    investigation = commands.add_parser("investigate", help="Investiguer avec OpenRouter.")
    investigation.add_argument("event_id", help="Identifiant d’événement, par exemple EVT-48392.")
    investigation.add_argument(
        "--prepare", action="store_true", help="Demander un brouillon si justifié."
    )
    investigation.add_argument(
        "--transport",
        choices=["python", "mcp"],
        default="python",
        help="Transport d’outils : python (défaut) ou mcp.",
    )
    for name, description in {
        "state": "Lire l’état de l’incident.",
        "approve": "Approuver comme superviseur (identité locale simulée).",
        "reject": "Rejeter comme superviseur.",
        "resume": "Créer l’ordre simulé approuvé, sans doublon.",
    }.items():
        command = commands.add_parser(name, help=description)
        command.add_argument("incident_id", help="Identifiant d’incident, par exemple INC-1001.")
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args, Settings()))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except DomainError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except ValidationError:
        print(
            "Erreur : configuration invalide; vérifier les valeurs du fichier .env.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
