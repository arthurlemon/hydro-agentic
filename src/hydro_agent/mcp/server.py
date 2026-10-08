"""Serveur MCP lié à une identité et à un incident par le processus hôte."""

import argparse
import asyncio
import sys
from typing import Any

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from hydro_agent.config import Settings
from hydro_agent.models import DomainError, ToolResult
from hydro_agent.services.azure_search import AzureSearchService
from hydro_agent.services.data import DataService
from hydro_agent.services.search import SearchService
from hydro_agent.state.postgres import IncidentRepository
from hydro_agent.tools.registry import SPECS, ToolRegistry


def build_registry(settings: Settings, incident_id: str, *, prepare: bool = False) -> ToolRegistry:
    return ToolRegistry(
        DataService(settings.data_dir),
        AzureSearchService(settings.azure_search_endpoint, settings.azure_search_index)
        if settings.search_backend == "azure"
        else SearchService(settings.data_dir / "procedures"),
        IncidentRepository(settings.database_url.get_secret_value()),
        settings.identity,
        incident_id,
        allow_draft=prepare,
    )


def build_server(registry: ToolRegistry) -> Server[Any, Any]:
    server: Server[Any, Any] = Server("hydro-agentic")

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=name,
                description=description,
                inputSchema=model.model_json_schema(),
                outputSchema=ToolResult.model_json_schema(),
            )
            for name, (description, model) in SPECS.items()
        ]

    @server.call_tool(validate_input=False)  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        # Une validation commune produit les mêmes erreurs françaises en Python et en MCP.
        result = await registry.call(name, arguments)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=result.model_dump_json())],
            structuredContent=result.model_dump(mode="json"),
            isError=not result.ok,
        )

    return server


async def serve(registry: ToolRegistry) -> None:
    server = build_server(registry)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP local d’investigation synthétique.")
    parser.add_argument("--incident", required=True, help="Incident persistant autorisé.")
    parser.add_argument(
        "--prepare", action="store_true", help="Autoriser la préparation d’un brouillon."
    )
    args = parser.parse_args()
    try:
        asyncio.run(serve(build_registry(Settings(), args.incident, prepare=args.prepare)))
    except DomainError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
