import json

import psycopg
import pytest
from conftest import DATA


@pytest.mark.asyncio
async def test_traces_correlate_tools_and_audit_without_sensitive_arguments(registry, tmp_path):
    from hydro_agent.observability.tracing import configure, span

    path = tmp_path / "traces.jsonl"
    configure(path)
    with span("investigation", incident_id=registry.incident_id):
        await registry.call("search_procedures", {"query": "SECRET-TOKEN surchauffe"})
        await registry.call("get_procedure", {"procedure_id": "TR-MAINT-004"})
        denied = await registry.call("create_work_order", {"incident_id": registry.incident_id})
        assert not denied.ok
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    root = next(row for row in rows if row["name"] == "investigation")
    tools = [row for row in rows if row["name"] == "tool"]
    assert len(tools) == 3
    assert all(row["trace_id"] == root["trace_id"] for row in tools)
    assert all(row["parent_span_id"] == root["span_id"] for row in tools)
    assert tools[0]["attributes"]["query_sha256"]
    assert tools[1]["attributes"]["sources"] == ["procedure:TR-MAINT-004"]
    assert tools[2]["status"] == "ERROR"
    assert "SECRET-TOKEN" not in path.read_text()
    assert "postgresql://" not in path.read_text()
    with psycopg.connect(registry.repository.database_url) as connection:
        audit = connection.execute("SELECT payload FROM audit ORDER BY id").fetchall()
    assert all(row[0]["trace_id"] == root["trace_id"] for row in audit)


@pytest.mark.asyncio
async def test_real_stdio_propagates_trace_metadata_without_tool_arguments(registry, tmp_path):
    from hydro_agent.config import Settings
    from hydro_agent.mcp.client import connect
    from hydro_agent.observability.tracing import configure, span

    path = tmp_path / "mcp.jsonl"
    configure(path)
    settings = Settings(
        _env_file=None,
        HYDRO_DATA_DIR=DATA,
        HYDRO_DATABASE_URL=registry.repository.database_url,
        HYDRO_TRACE_PATH=path,
    )
    with span("investigation", incident_id=registry.incident_id):
        async with connect(settings, registry.incident_id) as tools:
            result = await tools.call("get_asset", {"asset_id": "TR-1042"})
            assert result.ok
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    root = next(row for row in rows if row["name"] == "investigation")
    remote = next(row for row in rows if row["name"] == "tool")
    request = next(row for row in rows if row["name"] == "mcp.request")
    assert remote["trace_id"] == root["trace_id"]
    assert remote["parent_span_id"] == request["span_id"]
    assert request["parent_span_id"] == root["span_id"]


def test_exception_details_are_not_exported(tmp_path):
    from hydro_agent.observability.tracing import configure, span

    path = tmp_path / "failure.jsonl"
    configure(path)
    with pytest.raises(ValueError), span("model"):
        raise ValueError("credential=SECRET")
    row = json.loads(path.read_text())
    assert row["status"] == "ERROR"
    assert "SECRET" not in path.read_text()
