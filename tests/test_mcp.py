import os
import sys

from conftest import DATA
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_real_stdio_schemas_binding_and_approval(registry):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "hydro_agent.mcp.server", "--incident", registry.incident_id],
        env={
            **os.environ,
            "HYDRO_DB_PATH": str(registry.repository.path),
            "HYDRO_DATA_DIR": str(DATA),
            "HYDRO_ROLE": "operator",
            "HYDRO_ACTOR": "test-mcp",
        },
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 10
            assert "approve" not in {tool.name for tool in tools}
            assert all(tool.inputSchema["additionalProperties"] is False for tool in tools)
            assert all(tool.outputSchema for tool in tools)
            asset = await session.call_tool("get_asset", {"asset_id": "TR-1042"})
            assert not asset.isError
            assert asset.structuredContent["data"]["asset_id"] == "TR-1042"
            denied = await session.call_tool(
                "create_work_order", {"incident_id": registry.incident_id}
            )
            assert denied.isError
            assert not denied.structuredContent["ok"]
            forged = await session.call_tool("get_asset", {"asset_id": "TR-1042", "role": "admin"})
            assert forged.isError
            wrong = await session.call_tool("get_asset", {"asset_id": "TR-1043"})
            assert wrong.isError


async def test_mcp_client_matches_direct_tool_results(registry):
    from hydro_agent.config import Settings
    from hydro_agent.mcp.client import connect

    settings = Settings(HYDRO_DATA_DIR=DATA, HYDRO_DB_PATH=registry.repository.path)
    async with connect(settings, registry.incident_id) as tools:
        assert len(await tools.definitions()) == 10
        remote = await tools.call("get_recent_telemetry", {"asset_id": "TR-1042"})
        direct = await registry.call("get_recent_telemetry", {"asset_id": "TR-1042"})
        assert remote == direct
        denied = await tools.call("create_work_order", {"incident_id": registry.incident_id})
        assert not denied.ok


async def test_full_investigation_draft_approval_and_restart_over_mcp(registry):
    from test_agent import ScriptedModel, response

    from hydro_agent.agent.loop import investigate
    from hydro_agent.config import Settings
    from hydro_agent.mcp.client import connect
    from hydro_agent.models import Identity, Recommendation, Role

    settings = Settings(HYDRO_DATA_DIR=DATA, HYDRO_DB_PATH=registry.repository.path)
    citations = ["asset:TR-1042", "telemetry:TR-1042:24h", "procedure:TR-MAINT-004"]
    final = Recommendation(
        outcome="recommendation_ready",
        summary="Inspection P1 sous 24 heures.",
        action="inspection",
        priority="P1",
        deadline_hours=24,
        citations=citations,
    )
    model = ScriptedModel(
        [
            response(
                calls=[
                    ("get_asset", {"asset_id": "TR-1042"}),
                    ("get_recent_telemetry", {"asset_id": "TR-1042"}),
                ]
            ),
            response(calls=[("search_procedures", {"query": "surchauffe huile"})]),
            response(calls=[("get_procedure", {"procedure_id": "TR-MAINT-004"})]),
            response(
                calls=[
                    (
                        "draft_work_order",
                        {
                            "incident_id": registry.incident_id,
                            "action": "inspection",
                            "priority": "P1",
                            "justification": final.summary,
                            "citations": citations,
                        },
                    )
                ]
            ),
            response(final.model_dump_json()),
        ]
    )
    async with connect(settings, registry.incident_id, prepare=True) as tools:
        assert (
            await investigate(model, tools, registry.repository, registry.incident_id, prepare=True)
            == final
        )
        assert not (await tools.call("create_work_order", {"incident_id": registry.incident_id})).ok
    assert registry.repository.get(registry.incident_id)["status"] == "awaiting_approval"
    registry.repository.approve(
        registry.incident_id, Identity(actor="superviseure", role=Role.SUPERVISOR)
    )
    async with connect(settings, registry.incident_id) as tools:
        first = await tools.call("create_work_order", {"incident_id": registry.incident_id})
    async with connect(settings, registry.incident_id) as tools:
        repeated = await tools.call("create_work_order", {"incident_id": registry.incident_id})
    assert first.ok and first == repeated
    assert first.data["simulated"] is True
