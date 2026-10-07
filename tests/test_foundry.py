"""Contrats du transport cloud; aucun appel payant dans la suite."""

import json
from types import SimpleNamespace

import pytest

from hydro_agent.agent import foundry
from hydro_agent.agent.foundry import FoundryModel, function_tools, publish_agent
from hydro_agent.agent.loop import investigate
from hydro_agent.models import DomainError, Recommendation
from hydro_agent.tools.registry import SPECS

ENDPOINT = "https://example.services.ai.azure.com/api/projects/test"


class CloudDouble:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []
        self.deleted = []
        self.closed = False
        self.responses = SimpleNamespace(create=self.respond)
        self.conversations = SimpleNamespace(create=self.conversation, delete=self.delete)

    async def conversation(self):
        return SimpleNamespace(id="conv_test")

    async def respond(self, **kwargs):
        self.requests.append(kwargs)
        value = next(self.outputs)
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(**value)

    async def delete(self, conversation_id):
        self.deleted.append(conversation_id)

    async def close(self):
        self.closed = True


def response(output=None, text="", status="completed"):
    return dict(output=output or [], output_text=text, status=status, usage=None)


def test_functions_use_real_schemas_without_approval_tool():
    tools = function_tools()
    assert len(tools) == 10
    assert {tool.name for tool in tools} == set(SPECS)
    assert "approve" not in {tool.name for tool in tools}
    telemetry = next(tool for tool in tools if tool.name == "get_recent_telemetry")
    assert telemetry.strict is False
    assert telemetry.parameters["additionalProperties"] is False
    assert "hours" not in telemetry.parameters["required"]


async def test_sdk_session_can_open_and_close_without_network():
    # Exerce aussi les dépendances de transport du véritable SDK asynchrone.
    async with FoundryModel(ENDPOINT, "hydro-test", "7") as model:
        assert model.endpoint == ENDPOINT


async def test_publication_supplies_conclusion_contract_and_disables_post_retries(monkeypatch):
    captured = {}

    class Project:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.agents = SimpleNamespace(create_version=self.create_version)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create_version(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(name="hydro-test", version="8")

    monkeypatch.setattr(foundry, "AIProjectClient", Project)
    assert await publish_agent(ENDPOINT, "deployment-test", "hydro-test") == {
        "name": "hydro-test",
        "version": "8",
        "deployment": "deployment-test",
    }
    definition = captured["definition"]
    assert json.dumps(Recommendation.model_json_schema()) in definition.instructions
    assert len(definition.tools) == 10
    assert captured["retry_total"] == 0
    assert captured["connection_timeout"] == 10
    assert captured["read_timeout"] == 90


async def test_cleanup_attempts_all_closes_without_masking_model_failure():
    cloud = CloudDouble([RuntimeError("secret-body")])
    closed = []

    async def project_close():
        closed.append("project")
        raise RuntimeError("project-close-secret")

    async def credential_close():
        closed.append("credential")
        raise RuntimeError("credential-close-secret")

    with pytest.raises(DomainError, match="Appel Foundry impossible"):
        async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
            model._project = SimpleNamespace(close=project_close)
            model._credential = SimpleNamespace(close=credential_close)
            await model.complete([{"role": "user", "content": "test"}], [])
    assert closed == ["project", "credential"]
    assert cloud.closed


async def test_native_agent_preserves_conversation_without_resending_assistant():
    cloud = CloudDouble(
        [
            response(
                [
                    SimpleNamespace(type="reasoning"),
                    SimpleNamespace(
                        type="function_call",
                        call_id="call_1",
                        name="get_asset",
                        arguments='{"asset_id":"TR-1042"}',
                    ),
                ]
            ),
            response(text='{"outcome":"insufficient_evidence"}'),
            response(text="correction"),
        ]
    )
    messages = [
        {"role": "system", "content": "not sent"},
        {"role": "user", "content": "investigate"},
    ]
    async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
        first = await model.complete(messages, [])
        assert first.calls[0].id == "call_1"
        messages.append(first.message())
        messages.append({"role": "tool", "tool_call_id": "call_1", "content": '{"ok":true}'})
        final = await model.complete(messages, [])
        assert final.content == '{"outcome":"insufficient_evidence"}'
        messages.append(final.message())
        messages.append({"role": "user", "content": "citation invalide"})
        assert (await model.complete(messages, [])).content == "correction"
    assert cloud.requests[0]["input"] == [{"role": "user", "content": "investigate"}]
    assert cloud.requests[1]["input"] == [
        {"type": "function_call_output", "call_id": "call_1", "output": '{"ok":true}'}
    ]
    assert cloud.requests[2]["input"] == [{"role": "user", "content": "citation invalide"}]
    assert all(
        request["extra_body"]["agent_reference"]
        == {"type": "agent_reference", "name": "hydro-test", "version": "7"}
        for request in cloud.requests
    )
    assert all(request["conversation"] == "conv_test" for request in cloud.requests)
    assert cloud.deleted == ["conv_test"]
    assert cloud.closed


@pytest.mark.parametrize("status", ["incomplete", "failed", "cancelled"])
async def test_incomplete_response_is_not_a_recommendation(status):
    cloud = CloudDouble([response(text="fake", status=status)])
    async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
        with pytest.raises(DomainError, match="incomplète"):
            await model.complete([{"role": "user", "content": "test"}], [])
    assert cloud.closed


async def test_cloud_failure_does_not_leak_credentials():
    cloud = CloudDouble([RuntimeError("secret-token")])
    async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
        with pytest.raises(DomainError) as error:
            await model.complete([{"role": "user", "content": "test"}], [])
        assert "secret-token" not in str(error.value)
    assert cloud.closed


async def test_rate_limit_error_is_actionable_without_provider_body():
    error = RuntimeError("secret-provider-body")
    error.status_code = 429
    cloud = CloudDouble([error])
    async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
        with pytest.raises(DomainError, match="HTTP 429") as caught:
            await model.complete([{"role": "user", "content": "test"}], [])
        assert "secret-provider-body" not in str(caught.value)


async def test_native_agent_cannot_bypass_approval_after_malicious_retrieval(registry):
    cloud = CloudDouble(
        [
            response(
                [
                    SimpleNamespace(
                        type="function_call",
                        call_id="read",
                        name="get_procedure",
                        arguments='{"procedure_id":"ATTACK-001"}',
                    )
                ]
            ),
            response(
                [
                    SimpleNamespace(
                        type="function_call",
                        call_id="create",
                        name="create_work_order",
                        arguments='{"incident_id":"' + registry.incident_id + '"}',
                    )
                ]
            ),
            response(
                text='{"outcome":"insufficient_evidence","summary":"Pas de création autorisée.",'
                '"citations":[],"missing_evidence":["Preuves métier manquantes"]}'
            ),
        ]
    )
    async with FoundryModel(ENDPOINT, "hydro-test", "7", client=cloud) as model:
        await investigate(model, registry, registry.repository, registry.incident_id)
    output = cloud.requests[2]["input"][0]["output"]
    assert '"ok":false' in output
    assert "Approbation humaine persistée" in output
    state = registry.repository.get(registry.incident_id)
    assert state["status"] == "insufficient_evidence"
    assert state["approval"] is state["work_order"] is None


@pytest.mark.parametrize(
    "endpoint,version",
    [
        ("http://example.com", "7"),
        ("https://attacker.com/api/projects/test", "7"),
        ("https://[invalid/api/projects/test", "7"),
        ("https://example.services.ai.azure.com:bad/api/projects/test", "7"),
        (ENDPOINT, ""),
    ],
)
def test_configuration_requires_trusted_endpoint_and_pinned_version(endpoint, version):
    with pytest.raises(DomainError):
        FoundryModel(endpoint, "hydro-test", version)
