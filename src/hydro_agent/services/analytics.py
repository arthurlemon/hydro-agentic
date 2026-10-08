"""Contrat analytique étroit; une panne ne produit jamais une valeur de secours."""

import json
import re
from contextlib import nullcontext
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from hydro_agent.models import DomainError, Prediction


class AnalyticsService(Protocol):
    def predict(self, asset_id: str) -> Prediction: ...


class JsonAnalyticsService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def predict(self, asset_id: str) -> Prediction:
        try:
            rows = json.loads((self.root / "predictions.json").read_text(encoding="utf-8"))
            predictions = [Prediction.model_validate(row) for row in rows]
        except (OSError, ValueError, TypeError, ValidationError):
            raise DomainError("Source indisponible ou invalide : predictions.json.") from None
        for prediction in predictions:
            if prediction.asset_id == asset_id:
                return prediction
        raise DomainError("Prédiction ML indisponible; ne pas en déduire une valeur.")


class DatabricksAnalyticsService:
    def __init__(self, endpoint: str, token: str, *, client: httpx.Client | None = None) -> None:
        try:
            parsed = urlparse(endpoint)
            valid = (
                parsed.scheme == "https"
                and parsed.hostname is not None
                and parsed.hostname.endswith((".cloud.databricks.com", ".azuredatabricks.net"))
                and not parsed.username
                and not parsed.password
                and not parsed.query
                and not parsed.fragment
                and parsed.port in {None, 443}
                and re.fullmatch(r"/serving-endpoints/[A-Za-z0-9_-]+/invocations", parsed.path)
            )
        except ValueError:
            valid = False
        if not valid:
            raise DomainError("Endpoint Databricks invalide; HTTPS et domaine de workspace requis.")
        if not token:
            raise DomainError("DATABRICKS_TOKEN requis pour l’analytique distante.")
        self.endpoint = endpoint
        self._token = token
        self._client = client

    def predict(self, asset_id: str) -> Prediction:
        try:
            # Sans redirection ni reprise automatique : ne pas diffuser le jeton
            # et ne pas répéter involontairement un appel facturable.
            with nullcontext(self._client) if self._client else httpx.Client() as client:
                response = client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={"dataframe_records": [{"asset_id": asset_id}]},
                    timeout=httpx.Timeout(20, connect=5),
                    follow_redirects=False,
                )
                response.raise_for_status()
                body = response.json()
                rows = body["predictions"]
                if not isinstance(rows, list) or len(rows) != 1:
                    raise ValueError
                prediction = Prediction.model_validate(rows[0], strict=True)
                if prediction.asset_id != asset_id:
                    raise ValueError
                return prediction
        except httpx.HTTPStatusError as exc:
            raise DomainError(
                f"Prédiction Databricks indisponible (HTTP {exc.response.status_code})."
            ) from None
        except httpx.HTTPError:
            raise DomainError(
                "Prédiction Databricks indisponible; réseau ou délai dépassé."
            ) from None
        except (ValueError, TypeError, KeyError, ValidationError):
            raise DomainError(
                "Prédiction Databricks invalide; aucune valeur de remplacement."
            ) from None
