"""Adaptateur OpenRouter : appels d’outils choisis par le modèle."""

from typing import Any, Protocol

import httpx
from pydantic import Field, ValidationError

from hydro_agent.models import DomainError, Model


class ToolCall(Model):
    id: str
    name: str
    arguments: str


class ModelResponse(Model):
    content: str | None = None
    calls: list[ToolCall] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)

    def message(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.calls:
            result["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments},
                }
                for call in self.calls
            ]
        return result


class ModelClient(Protocol):
    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse: ...


class OpenRouterModel:
    def __init__(
        self, api_key: str, model: str, *, client: httpx.AsyncClient | None = None
    ) -> None:
        if not api_key.strip():
            raise DomainError("Renseigner OPENROUTER_API_KEY dans .env avant l’investigation.")
        self._api_key = api_key
        self.model = model
        self._client = client

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse:
        if self._client is not None:
            return await self._request(self._client, messages, tools)
        async with httpx.AsyncClient(timeout=90) as client:
            return await self._request(client, messages, tools)

    async def _request(
        self, client: httpx.AsyncClient, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0,
                    "max_tokens": 2500,
                },
            )
            response.raise_for_status()
            body = response.json()
            message = body["choices"][0]["message"]
            if not isinstance(message, dict):
                raise ValueError("Message fournisseur invalide.")
            return ModelResponse(
                content=message.get("content"),
                calls=[
                    ToolCall(
                        id=call["id"],
                        name=call["function"]["name"],
                        arguments=call["function"]["arguments"],
                    )
                    for call in message.get("tool_calls", [])
                ],
                usage=body.get("usage") or {},
            )
        except httpx.HTTPStatusError as exc:
            raise DomainError(
                f"OpenRouter indisponible (HTTP {exc.response.status_code})."
            ) from None
        except httpx.HTTPError:
            raise DomainError("Connexion OpenRouter indisponible ou délai dépassé.") from None
        except (KeyError, IndexError, TypeError, ValueError, ValidationError):
            raise DomainError("Réponse OpenRouter invalide.") from None
