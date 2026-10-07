"""Agent natif Foundry : fonctions cloud, exécution métier dans l’application."""

import json
from contextlib import suppress
from typing import Any, Self
from urllib.parse import urlparse

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition, Tool
from azure.identity.aio import AzureCliCredential

from hydro_agent.agent.loop import SYSTEM
from hydro_agent.agent.model import ModelResponse, ToolCall
from hydro_agent.models import DomainError, Recommendation
from hydro_agent.tools.registry import SPECS


def validate_endpoint(endpoint: str) -> None:
    try:
        url = urlparse(endpoint)
        port = url.port
    except ValueError:
        raise DomainError(
            "AZURE_AI_PROJECT_ENDPOINT doit être un endpoint de projet Foundry Azure."
        ) from None
    if (
        url.scheme != "https"
        or not (url.hostname or "").endswith(".services.ai.azure.com")
        or not url.path.startswith("/api/projects/")
        or not url.path.removeprefix("/api/projects/")
        or url.username
        or url.password
        or url.query
        or url.fragment
        or port not in (None, 443)
    ):
        raise DomainError(
            "AZURE_AI_PROJECT_ENDPOINT doit être un endpoint de projet Foundry Azure."
        )


def function_tools() -> list[Tool]:
    return [
        FunctionTool(
            name=name, description=description, parameters=model.model_json_schema(), strict=False
        )
        for name, (description, model) in SPECS.items()
    ]


async def publish_agent(endpoint: str, deployment: str, name: str) -> dict[str, str]:
    validate_endpoint(endpoint)
    if not deployment or not name:
        raise DomainError("Renseigner le déploiement et le nom de l’agent Foundry.")
    try:
        async with AzureCliCredential() as credential:
            async with AIProjectClient(
                endpoint=endpoint,
                credential=credential,
                retry_total=0,
                connection_timeout=10,
                read_timeout=90,
            ) as project:
                agent = await project.agents.create_version(
                    agent_name=name,
                    definition=PromptAgentDefinition(
                        model=deployment,
                        instructions=SYSTEM + json.dumps(Recommendation.model_json_schema()),
                        tools=function_tools(),
                    ),
                    description="Investigation synthétique; contrôles métier hors du modèle.",
                )
                return {"name": agent.name, "version": agent.version, "deployment": deployment}
    except Exception:
        raise DomainError(
            "Publication Foundry impossible; vérifier az login et les droits du projet."
        ) from None


class FoundryModel:
    def __init__(
        self, endpoint: str, agent_name: str, agent_version: str, *, client: Any = None
    ) -> None:
        validate_endpoint(endpoint)
        if not agent_name or not agent_version:
            raise DomainError(
                "Publier l’agent puis renseigner AZURE_AI_AGENT_NAME et AZURE_AI_AGENT_VERSION."
            )
        self.endpoint = endpoint
        self._reference = {"type": "agent_reference", "name": agent_name, "version": agent_version}
        self._client = client
        self._credential: AzureCliCredential | None = None
        self._project: AIProjectClient | None = None
        self._conversation: str | None = None
        self._cursor = 0

    async def __aenter__(self) -> Self:
        if self._client is None:
            self._credential = AzureCliCredential()
            self._project = AIProjectClient(endpoint=self.endpoint, credential=self._credential)
            self._client = self._project.get_openai_client(timeout=90, max_retries=0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        # État métier conservé dans PostgreSQL. Suppression cloud au mieux;
        # une panne du nettoyage ne doit pas masquer le résultat ou l’erreur métier.
        if self._client is not None:
            if self._conversation:
                with suppress(Exception):
                    await self._client.conversations.delete(conversation_id=self._conversation)
            with suppress(Exception):
                await self._client.close()
        if self._project is not None:
            with suppress(Exception):
                await self._project.close()
        if self._credential is not None:
            with suppress(Exception):
                await self._credential.close()

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse:
        if self._client is None:
            raise DomainError("Ouvrir la session Foundry avant l’investigation.")
        try:
            if self._conversation is None:
                conversation = await self._client.conversations.create()
                self._conversation = conversation.id
            inputs: list[dict[str, Any]] = []
            for message in messages[self._cursor :]:
                if message["role"] == "tool":
                    inputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": message["tool_call_id"],
                            "output": message["content"],
                        }
                    )
                elif message["role"] == "user":
                    inputs.append({"role": "user", "content": message["content"]})
            response = await self._client.responses.create(
                conversation=self._conversation,
                input=inputs,
                extra_body={"agent_reference": self._reference},
                max_output_tokens=5000,
            )
            if response.status != "completed":
                raise DomainError("Réponse Foundry incomplète; aucune conclusion acceptée.")
            result = ModelResponse(
                content=response.output_text or None,
                calls=[
                    ToolCall(id=item.call_id, name=item.name, arguments=item.arguments)
                    for item in response.output
                    if item.type == "function_call"
                ],
                usage=response.usage.model_dump() if response.usage else {},
            )
            # La boucle ajoutera un message assistant. Il existe déjà dans la
            # conversation cloud, y compris les items de raisonnement non textuels.
            self._cursor = len(messages) + 1
            return result
        except DomainError:
            raise
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if isinstance(status, int):
                raise DomainError(
                    f"Foundry indisponible (HTTP {status}); vérifier les droits et le quota."
                ) from None
            raise DomainError(
                "Appel Foundry impossible; vérifier la connexion, les droits et le quota."
            ) from None
