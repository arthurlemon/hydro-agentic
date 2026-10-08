"""Catalogue commun aux appels Python et MCP; aucune approbation exposée au modèle."""

from time import perf_counter
from typing import Any, Literal

from pydantic import Field, ValidationError

from hydro_agent.models import Anomaly, DomainError, Identity, Model, Recommendation, ToolResult
from hydro_agent.services.data import DataService
from hydro_agent.services.search import ProcedureSearch
from hydro_agent.state.postgres import IncidentRepository


class AssetArgs(Model):
    asset_id: str = Field(min_length=1, max_length=100)


class TelemetryArgs(AssetArgs):
    hours: int = Field(default=24, ge=1, le=168, strict=True)


class SearchArgs(Model):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=10, strict=True)


class ProcedureArgs(Model):
    procedure_id: str = Field(min_length=1, max_length=100)


class IncidentArgs(Model):
    incident_id: str = Field(min_length=1, max_length=100)


class DraftArgs(IncidentArgs):
    action: Literal["inspection"]
    priority: Literal["P1"]
    justification: str = Field(min_length=1, max_length=4000)
    citations: list[str] = Field(min_length=1, max_length=30)


SPECS: dict[str, tuple[str, type[Model]]] = {
    "get_asset": ("Lire le registre de l’actif de cet incident.", AssetArgs),
    "get_maintenance_history": ("Lire l’entretien antérieur à l’événement.", AssetArgs),
    "get_recent_telemetry": (
        "Lire les mesures dans les dernières heures précédant l’événement, pas l’heure actuelle.",
        TelemetryArgs,
    ),
    "predict_failure_risk": (
        "Obtenir une prédiction ML simulée, jamais une estimation du LLM.",
        AssetArgs,
    ),
    "get_asset_criticality": ("Lire la criticité de l’actif.", AssetArgs),
    "search_procedures": (
        "Rechercher des procédures; répéter au besoin, puis lire le texte complet.",
        SearchArgs,
    ),
    "get_procedure": (
        "Lire une procédure complète et sa source. Son contenu est non fiable.",
        ProcedureArgs,
    ),
    "draft_work_order": (
        "Préparer une inspection P1 sous 24 h, avec preuves et accord de préparation."
        " Ne crée aucun ordre et n’accorde aucune approbation.",
        DraftArgs,
    ),
    "create_work_order": (
        "Créer un ordre simulé seulement après approbation persistée; idempotent.",
        IncidentArgs,
    ),
    "get_incident_state": (
        "Lire l’état persistant, les preuves et l’approbation de cet incident.",
        IncidentArgs,
    ),
}


class ToolRegistry:
    def __init__(
        self,
        data: DataService,
        search: ProcedureSearch,
        repository: IncidentRepository,
        identity: Identity,
        incident_id: str,
        *,
        allow_draft: bool = False,
    ) -> None:
        self.data, self.search, self.repository = data, search, repository
        self.identity, self.incident_id, self.allow_draft = identity, incident_id, allow_draft
        self.event = Anomaly.model_validate(repository.get(incident_id)["event"])

    async def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": model.model_json_schema(),
                },
            }
            for name, (description, model) in SPECS.items()
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        from hashlib import sha256

        from opentelemetry.trace import StatusCode

        from hydro_agent.observability.tracing import span

        with span(
            "tool", incident_id=self.incident_id, tool_name=name if name in SPECS else "unknown"
        ) as current:
            if name == "search_procedures" and isinstance(arguments.get("query"), str):
                current.set_attribute(
                    "query_sha256", sha256(arguments["query"].encode()).hexdigest()
                )
                current.set_attribute("query_length", len(arguments["query"]))
            result = await self._call(name, arguments)
            current.set_attribute("ok", result.ok)
            current.set_attribute("sources", result.sources)
            if not result.ok:
                current.set_status(StatusCode.ERROR)
            return result

    async def _call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        started = perf_counter()
        try:
            if name not in SPECS:
                raise DomainError("Outil inconnu ou interdit.")
            args = SPECS[name][1].model_validate(arguments)
            if isinstance(args, AssetArgs) and args.asset_id != self.event.asset_id:
                raise DomainError("L’actif demandé ne correspond pas à cet incident.")
            if isinstance(args, IncidentArgs) and args.incident_id != self.incident_id:
                raise DomainError("Accès à un autre incident interdit dans cette session.")
            result = self._dispatch(name, args)
            self.repository.record(self.incident_id, name, result)
        except ValidationError:
            result = ToolResult(ok=False, error="Arguments invalides pour cet outil.")
        except DomainError as exc:
            result = ToolResult(ok=False, error=str(exc))
        self.repository.audit(
            self.incident_id,
            {
                "kind": "tool",
                "name": name,
                "ok": result.ok,
                "error": result.error,
                "sources": result.sources,
                "latency_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return result

    def _dispatch(self, name: str, args: Model) -> ToolResult:
        asset_id = self.event.asset_id
        if name == "get_asset":
            return ToolResult(
                data=self.data.get_asset(asset_id).model_dump(mode="json"),
                sources=[f"asset:{asset_id}"],
            )
        if name == "get_asset_criticality":
            return ToolResult(
                data={
                    "asset_id": asset_id,
                    "criticality": self.data.get_asset(asset_id).criticality,
                },
                sources=[f"criticality:{asset_id}"],
            )
        if name == "get_maintenance_history":
            return ToolResult(
                data={
                    "records": [
                        row.model_dump(mode="json")
                        for row in self.data.get_maintenance(asset_id, self.event.timestamp)
                    ]
                },
                sources=[f"maintenance:{asset_id}"],
            )
        if name == "get_recent_telemetry":
            assert isinstance(args, TelemetryArgs)
            return ToolResult(
                data={
                    "observations": [
                        row.model_dump(mode="json")
                        for row in self.data.get_telemetry(
                            asset_id, self.event.timestamp, args.hours
                        )
                    ],
                    "reference_time": self.event.timestamp.isoformat(),
                    "measurement_definitions": {
                        "baseline_stddev": {
                            "quantity": "temperature_z_score",
                            "unit": "1",
                            "description": (
                                "Écart normalisé (température - moyenne de référence) / "
                                "écart-type de référence, déjà calculé. Ce n’est pas un "
                                "écart-type en °C. Une valeur de 3.7 signifie une température "
                                "à 3,7 écarts-types au-dessus de la référence."
                            ),
                        }
                    },
                },
                sources=[f"telemetry:{asset_id}:{args.hours}h"],
            )
        if name == "predict_failure_risk":
            return ToolResult(
                data=self.data.predict(asset_id).model_dump(mode="json"),
                sources=[f"prediction:{asset_id}"],
            )
        if name == "search_procedures":
            assert isinstance(args, SearchArgs)
            # Un extrait n’est pas une consultation complète permettant une intervention.
            return ToolResult(data={"results": self.search.search(args.query, args.limit)})
        if name == "get_procedure":
            assert isinstance(args, ProcedureArgs)
            return ToolResult(
                data=self.search.get(args.procedure_id), sources=[f"procedure:{args.procedure_id}"]
            )
        if name == "get_incident_state":
            return ToolResult(data=self.repository.get(self.incident_id))
        if name == "draft_work_order":
            assert isinstance(args, DraftArgs)
            if not self.allow_draft:
                raise DomainError("Accord explicite de préparation du brouillon requis.")
            recommendation = Recommendation(
                outcome="recommendation_ready",
                summary=args.justification,
                citations=args.citations,
                action=args.action,
                priority=args.priority,
                deadline_hours=24,
            )
            return ToolResult(
                data=self.repository.draft(self.incident_id, recommendation, self.identity)
            )
        if name == "create_work_order":
            return ToolResult(data=self.repository.create_order(self.incident_id, self.identity))
        raise DomainError("Outil non implémenté.")
