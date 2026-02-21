"""
Dietary Agent – MEDORA
======================
Communicates with the user in a natural, conversational tone to:
  • Understand dietary preferences, restrictions, allergies & health goals.
  • Provide personalised meal plans with calorie / macro breakdowns.
  • Generate detailed nutritional reports (calories, protein, fats, carbs,
    fibre, micro-nutrients).
  • Leverage web search (DuckDuckGo) for up-to-date nutritional data.
  • Store conversation context in ChromaDB for long-term memory.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent
from app.agents.dietary.prompts import (
    DIETARY_SYSTEM_PROMPT,
    MEAL_PLAN_PROMPT,
    NUTRITIONAL_REPORT_PROMPT,
)
from app.agents.dietary.tools import (
    calculate_bmr,
    calculate_tdee,
    build_macro_split,
    format_nutritional_report,
)
from app.agents.dietary.schemas import (
    UserProfile,
    MealPlanRequest,
    NutritionalReport,
)

logger = logging.getLogger(__name__)


class DietaryAgent(BaseAgent):
    """Personalised dietary counselling agent."""

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return "DietaryAgent"

    @property
    def description(self) -> str:
        return (
            "A dietary counselling agent that communicates naturally to "
            "understand user requirements and provides personalised meal "
            "plans, dietary restrictions, and detailed nutritional reports "
            "with calorie & macro metrics."
        )

    # ------------------------------------------------------------------
    # LLM / Search helpers  (lazy-loaded so imports stay optional during
    # tests; actual clients are injected via the service layer)
    # ------------------------------------------------------------------
    def _get_llm_client(self):
        """Return the shared Gemini LLM client."""
        from app.services.llm_client import get_llm_client
        return get_llm_client()

    def _get_search_client(self):
        """Return the shared search client (DuckDuckGo / Tavily)."""
        from app.services.search import get_search_client
        return get_search_client()

    def _get_chroma_collection(self):
        """Return a ChromaDB collection scoped to the dietary agent."""
        from app.db.chroma import get_chroma_client
        client = get_chroma_client()
        return client.get_or_create_collection("dietary_agent_memory")

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------
    def _store_context(self, session_id: str, role: str, content: str) -> None:
        """Persist a turn in ChromaDB for long-term memory."""
        try:
            collection = self._get_chroma_collection()
            doc_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
            collection.add(
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": datetime.utcnow().isoformat(),
                }],
                ids=[doc_id],
            )
        except Exception as exc:
            logger.warning("ChromaDB store failed (non-fatal): %s", exc)

    def _retrieve_context(self, session_id: str, query: str, n: int = 5) -> List[str]:
        """Retrieve relevant past turns from ChromaDB."""
        try:
            collection = self._get_chroma_collection()
            results = collection.query(
                query_texts=[query],
                n_results=n,
                where={"session_id": session_id},
            )
            return results.get("documents", [[]])[0]
        except Exception as exc:
            logger.warning("ChromaDB retrieval failed (non-fatal): %s", exc)
            return []

    # ------------------------------------------------------------------
    # Web search enrichment
    # ------------------------------------------------------------------
    async def _search_nutrition_info(self, query: str) -> str:
        """Search the web for nutrition facts / dietary information."""
        try:
            search = self._get_search_client()
            results = await search.search(query)
            if results:
                snippets = [r.get("snippet", r.get("body", "")) for r in results[:3]]
                return "\n".join(snippets)
        except Exception as exc:
            logger.warning("Search failed (non-fatal): %s", exc)
        return ""

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------
    def _detect_intent(self, query: str) -> str:
        """Simple keyword-based intent detection."""
        q = query.lower()
        if any(kw in q for kw in ["meal plan", "plan my meals", "what should i eat", "weekly plan", "daily plan"]):
            return "meal_plan"
        if any(kw in q for kw in ["calorie", "calories", "macro", "nutrition report", "nutritional report", "breakdown"]):
            return "nutritional_report"
        if any(kw in q for kw in ["bmr", "tdee", "metabolic rate", "maintenance calories"]):
            return "calorie_calculation"
        if any(kw in q for kw in ["allergy", "allergies", "intolerant", "intolerance", "restriction", "avoid"]):
            return "dietary_restriction"
        return "general_conversation"

    # ------------------------------------------------------------------
    # Core invocation
    # ------------------------------------------------------------------
    async def invoke(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
    ) -> AgentResponse:
        """
        Main entry-point called by the Orchestrator.

        Parameters
        ----------
        session_id : str
            Unique session / conversation identifier.
        query : str
            The user's latest message.
        context : List[Dict]
            Recent conversation history supplied by the Orchestrator
            (list of {"role": ..., "content": ...} dicts).
        """
        intent = self._detect_intent(query)
        logger.info("[DietaryAgent] session=%s  intent=%s", session_id, intent)

        # Retrieve long-term memory from ChromaDB
        memory_snippets = self._retrieve_context(session_id, query)

        # Optionally enrich with live web search
        web_context = ""
        if intent in ("meal_plan", "nutritional_report", "dietary_restriction"):
            web_context = await self._search_nutrition_info(
                f"nutrition facts: {query}"
            )

        # Build the full prompt for the LLM
        system_prompt = self._build_system_prompt(intent)
        messages = self._build_messages(
            system_prompt=system_prompt,
            context=context,
            memory_snippets=memory_snippets,
            web_context=web_context,
            user_query=query,
            intent=intent,
        )

        # Call Gemini
        llm = self._get_llm_client()
        response_text = await llm.generate(messages)

        # If intent is calorie_calculation, augment response with tool output
        if intent == "calorie_calculation":
            tool_output = self._handle_calorie_calculation(query)
            if tool_output:
                response_text = f"{tool_output}\n\n{response_text}"

        # Persist both turns
        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": intent,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def _build_system_prompt(self, intent: str) -> str:
        if intent == "meal_plan":
            return MEAL_PLAN_PROMPT
        if intent == "nutritional_report":
            return NUTRITIONAL_REPORT_PROMPT
        return DIETARY_SYSTEM_PROMPT

    def _build_messages(
        self,
        system_prompt: str,
        context: List[Dict],
        memory_snippets: List[str],
        web_context: str,
        user_query: str,
        intent: str,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Inject long-term memory
        if memory_snippets:
            mem_block = "\n---\n".join(memory_snippets)
            messages.append({
                "role": "system",
                "content": (
                    "[Long-term memory – previous interactions with this user]\n"
                    f"{mem_block}"
                ),
            })

        # Inject web search context
        if web_context:
            messages.append({
                "role": "system",
                "content": (
                    "[Web search results – latest nutritional data]\n"
                    f"{web_context}"
                ),
            })

        # Inject recent conversation context from Orchestrator
        for turn in context[-10:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })

        # Current user query
        messages.append({"role": "user", "content": user_query})
        return messages

    # ------------------------------------------------------------------
    # Tool helpers
    # ------------------------------------------------------------------
    def _handle_calorie_calculation(self, query: str) -> Optional[str]:
        """
        Attempt to extract numbers from query and compute BMR/TDEE.
        Falls back to None so LLM handles the conversation gracefully.
        """
        try:
            # Very lightweight extraction – the LLM will do the heavy
            # lifting if this fails.
            import re
            nums = [float(n) for n in re.findall(r"[\d.]+", query)]
            if len(nums) >= 3:
                weight, height, age = nums[0], nums[1], nums[2]
                # Default to male if not specified
                gender = "male" if "female" not in query.lower() else "female"
                bmr = calculate_bmr(weight, height, age, gender)
                tdee = calculate_tdee(bmr, activity_level="moderate")
                macros = build_macro_split(tdee)
                report = format_nutritional_report(
                    NutritionalReport(
                        bmr=round(bmr, 1),
                        tdee=round(tdee, 1),
                        macros=macros,
                    )
                )
                return report
        except Exception as exc:
            logger.debug("Calorie calc extraction failed: %s", exc)
        return None
