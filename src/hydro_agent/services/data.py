"""Lecture validée des observations synthétiques, sans données inventées."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from hydro_agent.models import Anomaly, Asset, DomainError, Maintenance, Prediction, Telemetry

T = TypeVar("T", bound=BaseModel)


class DataService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _read(self, filename: str, model: type[T]) -> list[T]:
        try:
            rows = json.loads((self.root / filename).read_text(encoding="utf-8"))
            return [model.model_validate(row) for row in rows]
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            raise DomainError(f"Source indisponible ou invalide : {filename}.") from exc

    def get_event(self, event_id: str) -> Anomaly:
        for event in self._read("anomalies.json", Anomaly):
            if event.event_id == event_id:
                return event
        raise DomainError(f"Événement inconnu : {event_id}.")

    def get_asset(self, asset_id: str) -> Asset:
        for asset in self._read("assets.json", Asset):
            if asset.asset_id == asset_id:
                return asset
        raise DomainError(f"Actif inconnu : {asset_id}.")

    def get_telemetry(self, asset_id: str, at: datetime, hours: int = 24) -> list[Telemetry]:
        self.get_asset(asset_id)
        rows = [
            row
            for row in self._read("telemetry.json", Telemetry)
            if row.asset_id == asset_id and at - timedelta(hours=hours) <= row.timestamp <= at
        ]
        if not rows:
            raise DomainError("Télémétrie indisponible dans la fenêtre demandée.")
        return sorted(rows, key=lambda row: row.timestamp)

    def predict(self, asset_id: str) -> Prediction:
        self.get_asset(asset_id)
        for prediction in self._read("predictions.json", Prediction):
            if prediction.asset_id == asset_id:
                return prediction
        raise DomainError("Prédiction ML indisponible; ne pas en déduire une valeur.")

    def get_maintenance(self, asset_id: str, at: datetime) -> list[Maintenance]:
        self.get_asset(asset_id)
        return [
            row
            for row in self._read("maintenance_history.json", Maintenance)
            if row.asset_id == asset_id and row.date <= at.date()
        ]
