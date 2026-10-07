import asyncio
from datetime import datetime

import httpx
import pytest
from conftest import collect_evidence, draft
from test_agent import ScriptedModel, response

from hydro_agent.agent.loop import investigate
from hydro_agent.agent.model import OpenRouterModel
from hydro_agent.models import DomainError, Recommendation, Telemetry
from hydro_agent.services.search import SearchService


async def test_latest_measurement_compares_instants_not_strings(registry, monkeypatch):
    observations = [
        Telemetry(
            asset_id="TR-1042",
            timestamp=datetime.fromisoformat(timestamp),
            temperature_c=temperature,
            load_pct=92,
            baseline_stddev=stddev,
            oil_degradation_confirmed=oil,
        )
        for timestamp, temperature, stddev, oil in [
            ("2026-10-07T14:00:00+02:00", 90, 3.7, True),
            ("2026-10-07T13:00:00+00:00", 65, 0.5, False),
        ]
    ]
    monkeypatch.setattr(registry.data, "get_telemetry", lambda *args: observations)
    await collect_evidence(registry)
    assert not (await draft(registry)).ok


@pytest.mark.parametrize(
    "body",
    [{"choices": [{"message": None}]}, {"choices": [{"message": []}]}, [], {"choices": None}],
)
async def test_malformed_provider_reply_becomes_persisted_failure(registry, body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    ) as client:
        model = OpenRouterModel("test", "test", client=client)
        with pytest.raises(DomainError, match="invalide"):
            await investigate(model, registry, registry.repository, registry.incident_id)
    assert registry.repository.get(registry.incident_id)["status"] == "failed"


@pytest.mark.parametrize("content", [b"", b"  \n ", b"\xff"])
async def test_invalid_procedure_is_structured_failure(registry, tmp_path, content):
    (tmp_path / "TR-MAINT-004.md").write_bytes(content)
    registry.search = SearchService(tmp_path)
    for name, args in [
        ("get_procedure", {"procedure_id": "TR-MAINT-004"}),
        ("search_procedures", {"query": "huile"}),
    ]:
        result = await registry.call(name, args)
        assert not result.ok
        assert "procédure" in result.error.lower()


async def test_concurrent_investigation_is_refused_without_reset_then_retry_works(registry):
    entered = asyncio.Event()
    release = asyncio.Event()

    class WaitingModel:
        async def complete(self, messages, tools):
            entered.set()
            await release.wait()
            raise DomainError("Modèle indisponible.")

    first = asyncio.create_task(
        investigate(WaitingModel(), registry, registry.repository, registry.incident_id)
    )
    await entered.wait()
    await collect_evidence(registry)
    before = registry.repository.get(registry.incident_id)
    final = Recommendation(
        outcome="insufficient_evidence", summary="Reprise.", missing_evidence=["prédiction"]
    )
    try:
        with pytest.raises(DomainError, match="cours"):
            await investigate(
                ScriptedModel([response(final.model_dump_json())]),
                registry,
                registry.repository,
                registry.incident_id,
            )
        assert registry.repository.get(registry.incident_id) == before
    finally:
        release.set()
        with pytest.raises(DomainError, match="indisponible"):
            await first
    result = await investigate(
        ScriptedModel([response(final.model_dump_json())]),
        registry,
        registry.repository,
        registry.incident_id,
    )
    assert result == final
