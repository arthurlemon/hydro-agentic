"""Recherche lexicale française; documents traités comme données non fiables."""

import re
import unicodedata
from pathlib import Path
from typing import Any, Protocol

from hydro_agent.models import DomainError


class ProcedureSearch(Protocol):
    def get(self, procedure_id: str) -> dict[str, Any]: ...
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


def tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return set(
        re.findall(r"[a-z0-9]+", "".join(c for c in normalized if not unicodedata.combining(c)))
    )


class SearchService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, procedure_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", procedure_id):
            raise DomainError("Identifiant de procédure invalide.")
        path = self.root / f"{procedure_id}.md"
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise DomainError(f"Procédure absente ou illisible : {procedure_id}.") from exc
        content = content.strip()
        if not content:
            raise DomainError(f"Procédure vide : {procedure_id}.")
        return {
            "procedure_id": procedure_id,
            "title": content.splitlines()[0].lstrip("# "),
            "content": content,
            "source": f"procedure:{procedure_id}",
            "untrusted": True,
        }

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = tokens(query)
        hits = []
        for path in sorted(self.root.glob("*.md")):
            document = self.get(path.stem)
            score = len(terms & tokens(document["content"]))
            score += 2 * len(terms & tokens(document["title"]))
            if score:
                hits.append(
                    {
                        "procedure_id": path.stem,
                        "title": document["title"],
                        "excerpt": document["content"][:500],
                        "score": score,
                        "source": document["source"],
                        "untrusted": True,
                    }
                )
        return sorted(hits, key=lambda hit: (-hit["score"], hit["procedure_id"]))[:limit]
