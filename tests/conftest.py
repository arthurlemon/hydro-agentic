from pathlib import Path

import pytest

from hydro_agent.models import Identity

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def registry(tmp_path):
    from hydro_agent.services.data import DataService
    from hydro_agent.services.search import SearchService
    from hydro_agent.state.sqlite import IncidentRepository
    from hydro_agent.tools.registry import ToolRegistry

    data = DataService(DATA)
    repository = IncidentRepository(tmp_path / "state.sqlite3")
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
