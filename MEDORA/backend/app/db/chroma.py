"""ChromaDB client for agent memory. In-memory stub when chromadb is not installed."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# In-memory store: collection_name -> { "ids": [], "documents": [], "metadatas": [] }
_memory: Dict[str, Dict[str, List]] = {}


class _StubCollection:
    """Minimal collection interface for add/query used by VirtualDoctor and Dietary agents."""

    def __init__(self, name: str) -> None:
        self._name = name
        if name not in _memory:
            _memory[name] = {"ids": [], "documents": [], "metadatas": []}

    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        store = _memory[self._name]
        store["ids"].extend(ids)
        store["documents"].extend(documents)
        store["metadatas"].extend(metadatas)

    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Dict[str, Any] | None = None,
    ) -> Dict[str, List[List[Any]]]:
        store = _memory[self._name]
        documents = store["documents"]
        metadatas = store["metadatas"]
        if where:
            key = list(where.keys())[0] if where else None
            val = where.get(key) if key else None
            filtered = [
                (doc, meta)
                for doc, meta in zip(documents, metadatas)
                if key and meta.get(key) == val
            ]
            docs = [d for d, _ in filtered[-n_results:]]
        else:
            docs = documents[-n_results:]
        return {"documents": [docs]}


class _StubChromaClient:
    def get_or_create_collection(self, name: str) -> _StubCollection:
        return _StubCollection(name)


_client: _StubChromaClient | None = None


def get_chroma_client() -> _StubChromaClient:
    """Return a Chroma-like client (in-memory stub). Replace with real chromadb when needed."""
    global _client
    if _client is None:
        _client = _StubChromaClient()
    return _client
