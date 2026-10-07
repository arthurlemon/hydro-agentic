"""Transactions SQLite : preuves, approbation et ordre unique par incident."""

import fcntl
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from hydro_agent.models import Anomaly, DomainError, Identity, Recommendation, Role, ToolResult

FROZEN = {"awaiting_approval", "approved", "rejected", "work_order_created"}


def authorize(identity: Identity, *, supervisor: bool = False) -> None:
    roles = (
        {Role.SUPERVISOR, Role.ADMIN}
        if supervisor
        else {Role.OPERATOR, Role.SUPERVISOR, Role.ADMIN}
    )
    if identity.role not in roles:
        raise DomainError("Utilisateur non autorisé pour cette opération.")


class IncidentRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL,
                timestamp TEXT NOT NULL, payload TEXT NOT NULL)""")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _number(incident_id: str) -> int:
        try:
            if not incident_id.startswith("INC-"):
                raise ValueError
            return int(incident_id[4:]) - 1000
        except ValueError as exc:
            raise DomainError("Identifiant d’incident invalide.") from exc

    def _get(self, connection: sqlite3.Connection, incident_id: str) -> dict[str, Any]:
        row = connection.execute(
            "SELECT payload FROM incidents WHERE id=?", (self._number(incident_id),)
        ).fetchone()
        if row is None:
            raise DomainError(f"Incident inconnu : {incident_id}.")
        return cast(dict[str, Any], json.loads(row[0]))

    def _save(self, connection: sqlite3.Connection, state: dict[str, Any]) -> None:
        connection.execute(
            "UPDATE incidents SET payload=? WHERE id=?",
            (json.dumps(state, ensure_ascii=False), self._number(state["incident_id"])),
        )

    def begin(self, event: Anomaly) -> dict[str, Any]:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT payload FROM incidents WHERE event_id=?", (event.event_id,)
            ).fetchone()
            if row:
                return cast(dict[str, Any], json.loads(row[0]))
            cursor = connection.execute(
                "INSERT INTO incidents(event_id,payload) VALUES(?,?)", (event.event_id, "{}")
            )
            assert cursor.lastrowid is not None
            state: dict[str, Any] = {
                "incident_id": f"INC-{1000 + cursor.lastrowid}",
                "event_id": event.event_id,
                "asset_id": event.asset_id,
                "event": event.model_dump(mode="json"),
                "status": "new",
                "evidence": {},
                "recommendation": None,
                "draft": None,
                "approval": None,
                "work_order": None,
                "error": None,
            }
            self._save(connection, state)
            return state

    def get(self, incident_id: str) -> dict[str, Any]:
        with self._transaction() as connection:
            return self._get(connection, incident_id)

    @contextmanager
    def investigation(self, incident_id: str) -> Iterator[None]:
        """Verrou local macOS/Linux libéré même si le processus s’arrête."""
        number = self._number(incident_id)
        path = self.path.with_name(f"{self.path.name}.incident-{number}.lock")
        with path.open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise DomainError(
                    "Une investigation est déjà en cours pour cet incident."
                ) from None
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def start(self, incident_id: str) -> dict[str, Any]:
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] in FROZEN:
                raise DomainError(
                    "Cet incident possède déjà un brouillon figé; consulter son état."
                )
            state.update(status="investigating", evidence={}, recommendation=None, error=None)
            self._save(connection, state)
            return state

    def record(self, incident_id: str, name: str, result: ToolResult) -> None:
        if not result.ok:
            return
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] in FROZEN:
                return
            for source in result.sources:
                state["evidence"][source] = {"tool": name, "data": result.data}
            self._save(connection, state)

    @staticmethod
    def _validate(state: dict[str, Any], recommendation: Recommendation) -> None:
        evidence = state["evidence"]
        if any(source not in evidence for source in recommendation.citations):
            raise DomainError("Citation inconnue : récupérer la source avant de la citer.")
        if recommendation.outcome == "insufficient_evidence":
            if not recommendation.missing_evidence:
                raise DomainError("Préciser les preuves manquantes.")
            if recommendation.action or recommendation.priority or recommendation.deadline_hours:
                raise DomainError("Une preuve insuffisante ne peut autoriser une intervention.")
            return
        asset_id = state["asset_id"]
        citations = set(recommendation.citations)
        if f"asset:{asset_id}" not in citations:
            raise DomainError("Contexte de l’actif manquant.")
        # Règle métier approuvée de cette démonstration, jamais extraite d’un texte non fiable.
        if "procedure:TR-MAINT-004" not in citations:
            raise DomainError("Consulter et citer la procédure TR-MAINT-004 complète.")
        telemetry = [
            entry["data"]["observations"]
            for source, entry in evidence.items()
            if source in citations and entry["tool"] == "get_recent_telemetry"
        ]
        if not telemetry:
            raise DomainError("Télémétrie citée manquante.")
        latest = max(
            (row for rows in telemetry for row in rows),
            key=lambda row: datetime.fromisoformat(row["timestamp"]),
        )
        qualifies = latest["baseline_stddev"] > 3 and latest["oil_degradation_confirmed"]
        if recommendation.outcome == "no_action":
            prediction = evidence.get(f"prediction:{asset_id}", {}).get("data", {})
            if (
                latest["baseline_stddev"] > 3
                or prediction.get("risk_level") != "low"
                or f"prediction:{asset_id}" not in citations
            ):
                raise DomainError("Une absence d’urgence exige des preuves de faible risque.")
            if recommendation.action or recommendation.priority or recommendation.deadline_hours:
                raise DomainError("Aucune intervention attendue pour ce résultat.")
        elif not qualifies or (
            recommendation.action,
            recommendation.priority,
            recommendation.deadline_hours,
        ) != ("inspection", "P1", 24):
            raise DomainError(
                "Conditions P1 non démontrées : température et huile confirmée requises."
            )

    def recommend(self, incident_id: str, recommendation: Recommendation) -> dict[str, Any]:
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            self._validate(state, recommendation)
            if state["status"] in FROZEN:
                if state["recommendation"] == recommendation.model_dump(mode="json"):
                    return state
                raise DomainError("La recommandation est figée avec le brouillon.")
            state["recommendation"] = recommendation.model_dump(mode="json")
            state["status"] = (
                "insufficient_evidence"
                if recommendation.outcome == "insufficient_evidence"
                else "recommendation_ready"
            )
            self._save(connection, state)
            return state

    def draft(
        self, incident_id: str, recommendation: Recommendation, identity: Identity
    ) -> dict[str, Any]:
        authorize(identity)
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] in FROZEN:
                raise DomainError("Le brouillon est déjà figé; aucune modification autorisée.")
            self._validate(state, recommendation)
            if recommendation.outcome != "recommendation_ready":
                raise DomainError("Une recommandation d’intervention est requise.")
            state["recommendation"] = recommendation.model_dump(mode="json")
            state["draft"] = {
                "asset_id": state["asset_id"],
                **state["recommendation"],
                "prepared_by": identity.actor,
            }
            state["status"] = "awaiting_approval"
            self._save(connection, state)
            return cast(dict[str, Any], state["draft"])

    def approve(self, incident_id: str, identity: Identity) -> dict[str, Any]:
        authorize(identity, supervisor=True)
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] in {"approved", "work_order_created"}:
                return state
            if state["status"] != "awaiting_approval" or not state["draft"]:
                raise DomainError("Aucun brouillon en attente d’approbation.")
            state["approval"] = {
                "approved_by": identity.actor,
                "role": identity.role.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "draft": state["draft"],
            }
            state["status"] = "approved"
            self._save(connection, state)
            return state

    def reject(self, incident_id: str, identity: Identity) -> dict[str, Any]:
        authorize(identity, supervisor=True)
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] not in {"awaiting_approval", "approved"}:
                raise DomainError("Cet incident ne peut pas être rejeté dans son état actuel.")
            state.update(status="rejected", approval=None, rejected_by=identity.actor)
            self._save(connection, state)
            return state

    def create_order(self, incident_id: str, identity: Identity) -> dict[str, Any]:
        authorize(identity)
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["work_order"]:
                return cast(dict[str, Any], state["work_order"])
            approval = state["approval"]
            if state["status"] != "approved" or not approval or approval["draft"] != state["draft"]:
                raise DomainError("Approbation humaine persistée requise avant toute création.")
            order = {
                "work_order_id": f"WO-{88370 + self._number(incident_id)}",
                "incident_id": incident_id,
                "asset_id": state["asset_id"],
                "priority": state["draft"]["priority"],
                "action": state["draft"]["action"],
                "deadline_hours": 24,
                "status": "created",
                "simulated": True,
                "approved_by": approval["approved_by"],
            }
            state.update(status="work_order_created", work_order=order)
            self._save(connection, state)
            return order

    def fail(self, incident_id: str, message: str) -> None:
        with self._transaction() as connection:
            state = self._get(connection, incident_id)
            if state["status"] not in FROZEN:
                state.update(status="failed", error=message)
                self._save(connection, state)

    def audit(self, incident_id: str, payload: dict[str, Any]) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO audit(incident_id,timestamp,payload) VALUES(?,?,?)",
                (
                    incident_id,
                    datetime.now(UTC).isoformat(),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
