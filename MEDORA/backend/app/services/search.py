"""Agentic search (DuckDuckGo or Tavily). Stub returns empty list until integrated."""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


async def search(query: str, max_results: int = 5) -> List[dict]:
    """Search the web; returns list of {title, snippet, url}. Stub returns empty until integrated."""
    return await _search_impl(query, max_results=max_results)


async def _search_impl(query: str, max_results: int = 5) -> List[dict]:
    return []


class _SearchClientWrapper:
    async def search(self, query: str, max_results: int = 5) -> List[dict]:
        return await _search_impl(query, max_results=max_results)


def get_search_client() -> _SearchClientWrapper:
    return _SearchClientWrapper()
