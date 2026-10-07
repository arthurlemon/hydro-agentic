import json
from collections import deque

import httpx
import pytest

from hydro_agent.models import DomainError, Recommendation


class ScriptedModel:
    """Double déterministe uniquement pour les tests, pas un agent autonome."""

    def __init__(self, responses):
        self.responses = deque(responses)
        self.messages = []

    async def complete(self, messages, tools):
        self.messages = list(messages)
        return self.responses.popleft()


def response(content=None, calls=()):
    from hydro_agent.agent.model import ModelResponse, ToolCall

    return ModelResponse(
        content=content,
        calls=[
            ToolCall(id=f"call-{i}", name=name, arguments=json.dumps(args))
            for i, (name, args) in enumerate(calls)
        ],
    )


async def test_agent_iterates_search_and_uses_model_selected_order(registry):
    from hydro_agent.agent.loop import investigate

    final = Recommendation(
        outcome="recommendation_ready",
        summary="Inspection P1 sous 24 heures.",
        action="inspection",
        priority="P1",
        deadline_hours=24,
        citations=["asset:TR-1042", "telemetry:TR-1042:24h", "procedure:TR-MAINT-004"],
    )
    model = ScriptedModel(
        [
            response(calls=[("search_procedures", {"query": "surchauffe"})]),
            response(
                calls=[
                    ("get_recent_telemetry", {"asset_id": "TR-1042"}),
                    ("get_asset", {"asset_id": "TR-1042"}),
                ]
            ),
            response(calls=[("search_procedures", {"query": "huile confirmation"})]),
            response(
                calls=[
                    ("get_procedure", {"procedure_id": "TR-OIL-002"}),
                    ("get_procedure", {"procedure_id": "TR-MAINT-004"}),
                ]
            ),
            response(final.model_dump_json()),
        ]
    )
    result = await investigate(model, registry, registry.repository, registry.incident_id)
    assert result == final
    assert registry.repository.get(registry.incident_id)["status"] == "recommendation_ready"
    names = [m["name"] for m in model.messages if m["role"] == "tool"]
    assert names[:3] == ["search_procedures", "get_recent_telemetry", "get_asset"]
    assert names.count("search_procedures") == 2


async def test_prepared_draft_ends_investigation_without_reformulation_loop(registry):
    import psycopg

    from hydro_agent.agent.loop import investigate

    citations = ["asset:TR-1042", "telemetry:TR-1042:24h", "procedure:TR-MAINT-004"]
    model = ScriptedModel(
        [
            response(
                calls=[
                    ("get_asset", {"asset_id": "TR-1042"}),
                    ("get_recent_telemetry", {"asset_id": "TR-1042"}),
                    ("get_procedure", {"procedure_id": "TR-MAINT-004"}),
                ]
            ),
            response(
                calls=[
                    (
                        "draft_work_order",
                        {
                            "incident_id": registry.incident_id,
                            "action": "inspection",
                            "priority": "P1",
                            "justification": "Inspection P1 requise.",
                            "citations": citations,
                        },
                    ),
                    ("create_work_order", {"incident_id": registry.incident_id}),
                ]
            ),
            response(
                Recommendation(
                    outcome="recommendation_ready",
                    summary="Reformulation différente.",
                    action="inspection",
                    priority="P1",
                    deadline_hours=24,
                    citations=citations,
                ).model_dump_json()
            ),
        ]
    )
    result = await investigate(
        model, registry, registry.repository, registry.incident_id, prepare=True, max_steps=3
    )
    assert result.summary == "Inspection P1 requise."
    assert len(model.responses) == 1  # Pas de troisième appel payant après le brouillon validé.
    state = registry.repository.get(registry.incident_id)
    assert state["status"] == "awaiting_approval"
    assert state["approval"] is state["work_order"] is None
    with psycopg.connect(registry.repository.database_url) as connection:
        denied = connection.execute(
            "SELECT payload FROM audit WHERE incident_id=%s "
            "AND payload->>'name'='create_work_order'",
            (registry.incident_id,),
        ).fetchone()[0]
    assert not denied["ok"]  # Tout le lot d’outils est exécuté avant l’arrêt.


async def test_agent_returns_tool_failure_to_model_without_invention(registry, monkeypatch):
    from hydro_agent.agent.loop import investigate

    def unavailable(asset_id):
        raise DomainError("Prédiction ML indisponible.")

    monkeypatch.setattr(registry.data, "predict", unavailable)
    final = Recommendation(
        outcome="insufficient_evidence",
        summary="Prédiction indisponible.",
        missing_evidence=["prédiction ML"],
    )
    model = ScriptedModel(
        [
            response(calls=[("predict_failure_risk", {"asset_id": "TR-1042"})]),
            response(final.model_dump_json()),
        ]
    )
    result = await investigate(model, registry, registry.repository, registry.incident_id)
    assert result.outcome == "insufficient_evidence"
    assert '"ok":false' in model.messages[-1]["content"]
    assert "prediction:TR-1042" not in registry.repository.get(registry.incident_id)["evidence"]


async def test_malformed_or_unsubstantiated_final_is_not_accepted(registry):
    from hydro_agent.agent.loop import investigate

    forged = Recommendation(
        outcome="recommendation_ready",
        summary="Inventé",
        action="inspection",
        priority="P1",
        deadline_hours=24,
        citations=["procedure:INVENTEE"],
    )
    model = ScriptedModel([response("pas du JSON"), response(forged.model_dump_json())])
    result = await investigate(
        model, registry, registry.repository, registry.incident_id, max_steps=2
    )
    assert result.outcome == "insufficient_evidence"
    assert registry.repository.get(registry.incident_id)["work_order"] is None


async def test_model_outage_marks_failed_and_can_resume(registry):
    from hydro_agent.agent.loop import investigate

    class Broken:
        async def complete(self, messages, tools):
            raise DomainError("Modèle indisponible.")

    with pytest.raises(DomainError, match="indisponible"):
        await investigate(Broken(), registry, registry.repository, registry.incident_id)
    assert registry.repository.get(registry.incident_id)["status"] == "failed"
    final = Recommendation(
        outcome="insufficient_evidence",
        summary="Reprise sans preuve.",
        missing_evidence=["contexte"],
    )
    result = await investigate(
        ScriptedModel([response(final.model_dump_json())]),
        registry,
        registry.repository,
        registry.incident_id,
    )
    assert result.outcome == "insufficient_evidence"


async def test_openrouter_adapter_sends_tools_and_parses_usage():
    from hydro_agent.agent.model import OpenRouterModel

    def handler(request):
        payload = json.loads(request.content)
        assert payload["model"] == "modele-test"
        assert payload["tools"][0]["function"]["name"] == "get_asset"
        assert request.headers["Authorization"] == "Bearer cle-test"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "abc",
                                    "type": "function",
                                    "function": {
                                        "name": "get_asset",
                                        "arguments": '{"asset_id":"TR-1042"}',
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = OpenRouterModel("cle-test", "modele-test", client=client)
        result = await model.complete([], [{"type": "function", "function": {"name": "get_asset"}}])
    assert result.calls[0].name == "get_asset"
    assert result.usage["total_tokens"] == 30


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_openrouter_errors_never_expose_key(status):
    from hydro_agent.agent.model import OpenRouterModel

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(status, text="secret-ne-pas-afficher")
        )
    ) as client:
        model = OpenRouterModel("secret-ne-pas-afficher", "modele-test", client=client)
        with pytest.raises(DomainError) as error:
            await model.complete([], [])
    assert "secret-ne-pas-afficher" not in str(error.value)


async def test_missing_key_is_actionable_and_no_network():
    from hydro_agent.agent.model import OpenRouterModel

    with pytest.raises(DomainError, match="OPENROUTER_API_KEY"):
        OpenRouterModel("", "modele-test")


@pytest.mark.parametrize(
    "event_id,expected",
    [
        ("EVT-LOW", "no_action"),
        ("EVT-TEMP", "insufficient_evidence"),
        ("EVT-UNKNOWN", "insufficient_evidence"),
    ],
)
async def test_alternative_scenarios(registry, event_id, expected):
    from hydro_agent.agent.loop import investigate
    from hydro_agent.tools.registry import ToolRegistry

    event = registry.data.get_event(event_id)
    state = registry.repository.begin(event)
    tools = ToolRegistry(
        registry.data, registry.search, registry.repository, registry.identity, state["incident_id"]
    )
    citations = (
        []
        if expected == "insufficient_evidence"
        else [
            f"asset:{event.asset_id}",
            f"telemetry:{event.asset_id}:24h",
            f"prediction:{event.asset_id}",
            "procedure:TR-MAINT-004",
        ]
    )
    final = Recommendation(
        outcome=expected,
        summary="Pas d’urgence."
        if expected == "no_action"
        else "Investigation complémentaire nécessaire.",
        citations=citations,
        missing_evidence=[] if expected == "no_action" else ["confirmation"],
    )
    model = ScriptedModel(
        [
            response(
                calls=[
                    (name, {"asset_id": event.asset_id})
                    for name in ("get_asset", "get_recent_telemetry", "predict_failure_risk")
                ]
            ),
            response(calls=[("get_procedure", {"procedure_id": "TR-MAINT-004"})]),
            response(final.model_dump_json()),
        ]
    )
    result = await investigate(model, tools, registry.repository, state["incident_id"])
    assert result.outcome == expected
    assert registry.repository.get(state["incident_id"])["work_order"] is None


async def test_missing_procedure_prevents_recommendation(registry, tmp_path):
    from hydro_agent.services.search import SearchService

    registry.search = SearchService(tmp_path)
    assert not (await registry.call("get_procedure", {"procedure_id": "TR-MAINT-004"})).ok
    assert (await registry.call("search_procedures", {"query": "surchauffe"})).data == {
        "results": []
    }


async def test_historical_oil_does_not_satisfy_p1(registry):
    from hydro_agent.tools.registry import ToolRegistry

    event = registry.data.get_event("EVT-TEMP")
    state = registry.repository.begin(event)
    tools = ToolRegistry(
        registry.data,
        registry.search,
        registry.repository,
        registry.identity,
        state["incident_id"],
        allow_draft=True,
    )
    for name in ("get_asset", "get_recent_telemetry", "get_maintenance_history"):
        assert (await tools.call(name, {"asset_id": "TR-1044"})).ok
    await tools.call("get_procedure", {"procedure_id": "TR-MAINT-004"})
    result = await tools.call(
        "draft_work_order",
        {
            "incident_id": state["incident_id"],
            "action": "inspection",
            "priority": "P1",
            "justification": "Ancien constat.",
            "citations": [
                "asset:TR-1044",
                "telemetry:TR-1044:24h",
                "maintenance:TR-1044",
                "procedure:TR-MAINT-004",
            ],
        },
    )
    assert not result.ok
