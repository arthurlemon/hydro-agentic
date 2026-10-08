"""Recherche Azure BM25 française, Entra ID; jamais de repli local implicite."""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import AzureCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)

from hydro_agent.models import DomainError
from hydro_agent.services.search import SearchService


def validate_configuration(endpoint: str, index: str) -> None:
    try:
        url = urlparse(endpoint)
        valid = (
            url.scheme == "https"
            and url.hostname is not None
            and url.hostname.endswith(".search.windows.net")
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
            and url.path in {"", "/"}
            and url.port in {None, 443}
        )
    except ValueError:
        valid = False
    if not valid:
        raise DomainError("AZURE_SEARCH_ENDPOINT doit désigner un service Azure Search HTTPS.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,127}", index):
        raise DomainError("AZURE_SEARCH_INDEX invalide.")


def procedure_documents(root: Path) -> list[dict[str, Any]]:
    local = SearchService(root)
    documents = [local.get(path.stem) for path in sorted(root.glob("*.md"))]
    if not documents:
        raise DomainError("Aucune procédure à indexer.")
    return documents


def procedure_index(name: str) -> SearchIndex:
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(name="procedure_id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", analyzer_name="fr.lucene"),
            SearchableField(name="content", analyzer_name="fr.lucene"),
            SimpleField(name="source", type=SearchFieldDataType.String),
            SimpleField(name="untrusted", type=SearchFieldDataType.Boolean),
        ],
    )


def index_procedures(endpoint: str, index: str, root: Path) -> dict[str, Any]:
    validate_configuration(endpoint, index)
    documents = procedure_documents(root)
    try:
        with AzureCliCredential() as credential:
            options = {"retry_total": 0, "connection_timeout": 5, "read_timeout": 20}
            with SearchIndexClient(endpoint, credential, **options) as client:
                client.create_or_update_index(procedure_index(index))
            with SearchClient(endpoint, index, credential, **options) as search:
                results = search.upload_documents(documents)
                if not all(result.succeeded for result in results) or len(results) != len(
                    documents
                ):
                    raise DomainError(
                        "Indexation Azure AI Search incomplète; vérifier chaque document."
                    )
    except AzureError:
        raise DomainError(
            "Indexation Azure AI Search impossible; vérifier Entra et les rôles."
        ) from None
    return {
        "index": index,
        "uploaded": len(documents),
        "search_type": "lexical_bm25",
        "embedding": False,
    }


class AzureSearchService:
    def __init__(self, endpoint: str, index: str, *, client: Any = None) -> None:
        validate_configuration(endpoint, index)
        self.endpoint, self.index, self.client = endpoint, index, client

    @contextmanager
    def _client(self) -> Iterator[Any]:
        if self.client is not None:
            yield self.client
        else:
            with (
                AzureCliCredential() as credential,
                SearchClient(
                    self.endpoint,
                    self.index,
                    credential,
                    retry_total=0,
                    connection_timeout=5,
                    read_timeout=20,
                ) as client,
            ):
                yield client

    @staticmethod
    def _document(row: dict[str, Any]) -> dict[str, Any]:
        procedure_id, title, content = row["procedure_id"], row["title"], row["content"]
        if (
            not isinstance(procedure_id, str)
            or not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", procedure_id)
            or not isinstance(title, str)
            or not title.strip()
            or not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError
        return {
            "procedure_id": procedure_id,
            "title": title,
            "content": content,
            "source": f"procedure:{procedure_id}",
            "untrusted": True,
        }

    def get(self, procedure_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", procedure_id):
            raise DomainError("Identifiant de procédure invalide.")
        try:
            with self._client() as client:
                document = self._document(client.get_document(procedure_id))
                if document["procedure_id"] != procedure_id:
                    raise ValueError
                return document
        except ResourceNotFoundError:
            raise DomainError(f"Procédure absente dans Azure AI Search : {procedure_id}.") from None
        except (AzureError, ValueError, KeyError, TypeError):
            raise DomainError("Lecture Azure AI Search impossible ou document invalide.") from None

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        try:
            with self._client() as client:
                rows = client.search(
                    search_text=query,
                    top=limit,
                    query_type="simple",
                    search_mode="any",
                    search_fields=["title", "content"],
                    select=["procedure_id", "title", "content"],
                )
                hits = []
                for row in rows:
                    document = self._document(row)
                    hits.append(
                        {key: value for key, value in document.items() if key != "content"}
                        | {
                            "excerpt": document["content"][:500],
                            "score": float(row["@search.score"]),
                        }
                    )
                return hits
        except (AzureError, ValueError, KeyError, TypeError):
            raise DomainError("Recherche Azure AI Search impossible ou réponse invalide.") from None
