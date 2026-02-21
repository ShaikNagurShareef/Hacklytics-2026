"""Agentic search (DuckDuckGo or Tavily). Stub returns empty list until integrated."""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


async def search(query: str, max_results: int = 5) -> List[dict]:
    """
    Search the web for self-help or crisis resources. Returns list of {title, snippet, url}.
    Integrate DuckDuckGo or Tavily here; for now returns empty to avoid external calls.
    """
    # TODO: integrate duckduckgo-search or Tavily API
    # try:
    #     from duckduckgo_search import DDGS
    #     with DDGS() as ddgs:
    #         results = list(ddgs.text(query, max_results=max_results))
    #     return [{"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")} for r in results]
    # except Exception as e:
    #     logger.warning("Search failed: %s", e)
    return []
