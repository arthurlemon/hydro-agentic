import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hydro_agent.models import Identity

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(autouse=True)
def no_cloud_search_by_default(monkeypatch):
    # La suite normale reste hors ligne, même lorsque .env choisit Azure.
    monkeypatch.setenv("HYDRO_SEARCH_BACKEND", "local")


@pytest.fixture
def database_url():
    # Chaque test possède uniquement son propre schéma; aucune table applicative supprimée.
    url = os.environ.get(
        "HYDRO_TEST_DATABASE_URL", "postgresql://hydro:hydro-local@127.0.0.1:55432/hydro"
    )
    schema = f"hydro_test_{uuid4().hex}"
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            yield make_conninfo(url, options=f"-csearch_path={schema}")
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def registry(database_url):
    from hydro_agent.services.data import DataService
    from hydro_agent.services.search import SearchService
    from hydro_agent.state.postgres import IncidentRepository
    from hydro_agent.tools.registry import ToolRegistry

    data = DataService(DATA)
    repository = IncidentRepository(database_url)
    incident = repository.begin(data.get_event("EVT-48392"))
    return ToolRegistry(
        data,
        SearchService(DATA / "procedures"),
        repository,
        Identity(actor="operateur-test"),
        incident["incident_id"],
        allow_draft=True,
    )


async def collect_evidence(registry):
    for name in (
        "get_asset",
        "get_recent_telemetry",
        "predict_failure_risk",
        "get_maintenance_history",
        "get_asset_criticality",
    ):
        result = await registry.call(name, {"asset_id": "TR-1042"})
        assert result.ok, result.error
    result = await registry.call("get_procedure", {"procedure_id": "TR-MAINT-004"})
    assert result.ok
    return [
        "asset:TR-1042",
        "telemetry:TR-1042:24h",
        "prediction:TR-1042",
        "maintenance:TR-1042",
        "procedure:TR-MAINT-004",
    ]


async def draft(registry):
    citations = await collect_evidence(registry)
    return await registry.call(
        "draft_work_order",
        {
            "incident_id": registry.incident_id,
            "action": "inspection",
            "priority": "P1",
            "justification": "Inspection sous 24 heures selon les preuves citées.",
            "citations": citations,
        },
    )
