"""Adaptateur de la boucle d’agent vers un vrai sous-processus MCP."""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from pydantic import ValidationError

from hydro_agent.config import Settings
from hydro_agent.models import DomainError, ToolResult
from hydro_agent.observability.tracing import carrier


class MCPTools:
    def __init__(self, session: ClientSession) -> None:
        self.session = session

    async def definitions(self) -> list[dict[str, Any]]:
        result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in result.tools
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        try:
            result = await self.session.call_tool(
                name, arguments, read_timeout_seconds=timedelta(seconds=30), meta=carrier()
            )
            if result.structuredContent is None:
                return ToolResult(ok=False, error="Réponse MCP non structurée ou appel refusé.")
            parsed = ToolResult.model_validate(result.structuredContent)
            if result.isError and parsed.ok:
                return ToolResult(ok=False, error="Erreur de transport MCP.")
            return parsed
        except (McpError, ValidationError):
            return ToolResult(ok=False, error="Outil MCP indisponible ou réponse invalide.")


@asynccontextmanager
async def connect(
    settings: Settings, incident_id: str, *, prepare: bool = False
) -> AsyncIterator[MCPTools]:
    # Ne transmet pas la clé OpenRouter au serveur d’outils.
    env = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "SYSTEMROOT", "TMPDIR"}
    }
    env.update(
        HYDRO_DATA_DIR=str(settings.data_dir.resolve()),
        HYDRO_DATABASE_URL=settings.database_url.get_secret_value(),
        HYDRO_ACTOR=settings.actor,
        HYDRO_ROLE=settings.role.value,
        OPENROUTER_API_KEY="",
        HYDRO_SEARCH_BACKEND=settings.search_backend,
        AZURE_SEARCH_ENDPOINT=settings.azure_search_endpoint,
        AZURE_SEARCH_INDEX=settings.azure_search_index,
        HYDRO_TRACE_PATH=str(settings.trace_path.resolve()),
        HYDRO_OTLP_ENDPOINT=settings.otlp_endpoint,
    )
    args = ["-m", "hydro_agent.mcp.server", "--incident", incident_id]
    if prepare:
        args.append("--prepare")
    parameters = StdioServerParameters(command=sys.executable, args=args, env=env)
    consumer_error: DomainError | None = None
    try:
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=30)
            ) as session:
                await session.initialize()
                try:
                    yield MCPTools(session)
                except DomainError as exc:
                    consumer_error = exc
                    raise
    except ExceptionGroup:
        if consumer_error is not None:
            raise consumer_error from None
        raise DomainError(
            "Session MCP interrompue; consulter l’état de l’incident avant de reprendre."
        ) from None
