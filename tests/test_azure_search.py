from pathlib import Path

import pytest
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from conftest import DATA

from hydro_agent.models import DomainError


class SearchClientDouble:
    def __init__(self, documents):
        self.documents = {doc["procedure_id"]: doc for doc in documents}
        self.failure = None

    def get_document(self, key):
        if self.failure:
            raise self.failure
        if key not in self.documents:
            raise ResourceNotFoundError("secret serveur")
        return self.documents[key]

    def search(self, search_text, **kwargs):
        if self.failure:
            raise self.failure
        assert kwargs["query_type"] == "simple"
        assert kwargs["search_fields"] == ["title", "content"]
        return [dict(doc, **{"@search.score": 2.5}) for doc in self.documents.values()][
            : kwargs["top"]
        ]


def service():
    from hydro_agent.services.azure_search import AzureSearchService, procedure_documents

    documents = procedure_documents(DATA / "procedures")
    client = SearchClientDouble(documents)
    return AzureSearchService("https://example.search.windows.net", "procedures-v1", client=client)


def test_index_preserves_all_seven_full_documents_and_french_analyzer():
    from hydro_agent.services.azure_search import procedure_documents, procedure_index

    documents = procedure_documents(DATA / "procedures")
    assert len(documents) == 7
    attack = next(doc for doc in documents if doc["procedure_id"] == "ATTACK-001")
    assert attack["untrusted"] is True
    assert "approbation" in attack["content"]
    assert attack["source"] == "procedure:ATTACK-001"
    index = procedure_index("procedures-v1")
    assert next(field for field in index.fields if field.name == "procedure_id").key
    assert all(
        field.analyzer_name == "fr.lucene"
        for field in index.fields
        if field.name in {"title", "content"}
    )


def test_azure_search_returns_excerpt_then_full_document_with_same_citation():
    search = service()
    hits = search.search("surchauffe de transformateur avec dégradation d’huile", limit=2)
    assert len(hits) == 2
    assert hits[0]["score"] == 2.5
    assert "content" not in hits[0]
    document = search.get("TR-MAINT-004")
    assert document["source"] == "procedure:TR-MAINT-004"
    assert document["untrusted"] is True
    assert document["content"] == (DATA / "procedures/TR-MAINT-004.md").read_text().strip()
    assert search.search("  ") == []
    with pytest.raises(DomainError, match="Identifiant"):
        search.get("../config")
    with pytest.raises(DomainError, match="absente"):
        search.get("TR-UNKNOWN-999")


def test_cloud_failure_never_uses_local_documents_or_exposes_response_body():
    search = service()
    search.client.failure = HttpResponseError("secret serveur et jeton")
    for operation in (lambda: search.search("huile"), lambda: search.get("TR-MAINT-004")):
        with pytest.raises(DomainError, match="Azure AI Search") as error:
            operation()
        assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "endpoint",
    ["", "http://example.search.windows.net", "https://evil.test", "https://x:bad", "https://["],
)
def test_search_endpoint_must_be_trusted_https(endpoint):
    from hydro_agent.services.azure_search import AzureSearchService

    with pytest.raises(DomainError, match="AZURE_SEARCH_ENDPOINT"):
        AzureSearchService(endpoint, "procedures-v1")


def test_unreadable_procedure_stops_indexation(tmp_path: Path):
    from hydro_agent.services.azure_search import procedure_documents

    (tmp_path / "TR-EMPTY-001.md").write_text(" ")
    with pytest.raises(DomainError, match="vide"):
        procedure_documents(tmp_path)


async def test_configured_azure_backend_does_not_silently_fall_back_in_mcp(registry, monkeypatch):
    from hydro_agent.config import Settings
    from hydro_agent.mcp.client import connect

    monkeypatch.setenv("HYDRO_SEARCH_BACKEND", "azure")
    settings = Settings(
        HYDRO_DATA_DIR=DATA,
        HYDRO_DATABASE_URL=registry.repository.database_url,
        AZURE_SEARCH_ENDPOINT="",
    )
    with pytest.raises(DomainError):
        async with connect(settings, registry.incident_id) as tools:
            await tools.call("get_procedure", {"procedure_id": "TR-MAINT-004"})
