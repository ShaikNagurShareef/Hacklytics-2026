"""
Orchestrator Agent
==================
Central routing hub that registers all specialist agents, determines
which agent is best suited for a user query, and delegates accordingly.

Routing strategy (two layers):
1. **Keyword-first** — fast deterministic check for obvious domain keywords.
2. **LLM fallback** — when keywords are ambiguous the Gemini model reads
   every agent's description and picks the best match.

The orchestrator also:
• Maintains per-session conversation context so follow-ups stay with the
  same agent unless the user explicitly switches topic.
• Supports multi-agent collaboration (agent A can request info from agent B
  through the orchestrator).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

# ── Import all implemented agents ──────────────────────────────────
from app.agents.dietary.agent import DietaryAgent
from app.agents.virtual_doctor.agent import VirtualDoctorAgent

logger = logging.getLogger(__name__)


# ===================================================================
# Keyword routing table
# ===================================================================
AGENT_KEYWORDS: Dict[str, List[str]] = {
    "DietaryAgent": [
        "diet", "meal plan", "calorie", "calories", "nutrition",
        "macro", "protein", "carbs", "fat", "fats", "fibre", "fiber",
        "bmr", "tdee", "eat", "food", "vegetarian", "vegan",
        "keto", "allergy", "allergies", "intolerant", "intolerance",
        "breakfast", "lunch", "dinner", "snack", "recipe",
        "weight loss", "weight gain", "nutritional", "healthy eating",
    ],
    "VirtualDoctorAgent": [
        "symptom", "symptoms", "pain", "ache", "fever", "cough",
        "doctor", "medical", "medicine", "diagnosis", "emergency",
        "hospital", "clinic", "first aid", "cpr", "choking",
        "bleeding", "seizure", "heart attack", "stroke", "injury",
        "rash", "infection", "vomiting", "nausea", "dizziness",
        "headache", "blood pressure", "diabetes", "asthma",
        "breathing", "health advice", "health concern",
        "prescription", "check-up", "triage",
    ],
}


class OrchestratorAgent:
    """
    Central hub that routes queries to the correct specialist agent.

    Usage:
        orchestrator = OrchestratorAgent()
        response = await orchestrator.handle("session-1", "Plan my meals for today")
    """

    def __init__(self):
        # ── Register agents ───────────────────────────────────────
        self._agents: Dict[str, BaseAgent] = {}
        self._register_agent(DietaryAgent())
        self._register_agent(VirtualDoctorAgent())

        # ── Per-session state ─────────────────────────────────────
        # Tracks which agent is currently handling each session
        self._session_agent: Dict[str, str] = {}
        # Conversation history per session
        self._session_history: Dict[str, List[Dict[str, str]]] = {}

        logger.info(
            "Orchestrator initialised with %d agent(s): %s",
            len(self._agents),
            list(self._agents.keys()),
        )

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------
    def _register_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the registry."""
        self._agents[agent.name] = agent
        logger.info("Registered agent: %s", agent.name)

    @property
    def registered_agents(self) -> Dict[str, str]:
        """Return {name: description} for every registered agent."""
        return {name: agent.description for name, agent in self._agents.items()}

    # ------------------------------------------------------------------
    # Keyword-based routing (fast path)
    # ------------------------------------------------------------------
    def _route_by_keywords(self, query: str) -> Optional[str]:
        """
        Score each agent by how many domain keywords appear in the query.
        Returns the agent name with the highest score, or None if tied / 0.
        """
        q = query.lower()
        scores: Dict[str, int] = {}

        for agent_name, keywords in AGENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q)
            if score > 0:
                scores[agent_name] = score

        if not scores:
            return None

        # Return highest-scoring agent; if tied, return None → fall through to LLM
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_agents) >= 2 and sorted_agents[0][1] == sorted_agents[1][1]:
            return None  # ambiguous — let LLM decide
        return sorted_agents[0][0]

    # ------------------------------------------------------------------
    # LLM-based routing (fallback)
    # ------------------------------------------------------------------
    async def _route_by_llm(self, query: str) -> str:
        """
        Ask the Gemini model which agent should handle this query.
        Falls back to general response if LLM is unavailable.
        """
        agent_descriptions = "\n".join(
            f"- **{name}**: {desc}"
            for name, desc in self.registered_agents.items()
        )

        routing_prompt = (
            "You are an intelligent medical orchestrator. Given the user query below, "
            "decide which specialist agent should handle it.\n\n"
            f"Available agents:\n{agent_descriptions}\n\n"
            f"User query: \"{query}\"\n\n"
            "Respond with ONLY the agent name (e.g., 'DietaryAgent' or "
            "'VirtualDoctorAgent'). If the query doesn't clearly match any agent, "
            "respond with 'VirtualDoctorAgent' as the default medical agent."
        )

        try:
            from app.services.llm_client import get_llm_client
            llm = get_llm_client()
            response = await llm.generate([
                {"role": "system", "content": "You are a routing classifier. Respond with only the agent name."},
                {"role": "user", "content": routing_prompt},
            ])

            # Extract agent name from response
            response_text = response.strip()
            for agent_name in self._agents:
                if agent_name.lower() in response_text.lower():
                    return agent_name

        except Exception as exc:
            logger.warning("LLM routing failed (falling back to default): %s", exc)

        # Default to VirtualDoctorAgent as the general medical agent
        return "VirtualDoctorAgent"

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    def _get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for a session."""
        return self._session_history.get(session_id, [])

    def _update_session_history(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
        agent_name: str,
    ) -> None:
        """Append a turn to the session history."""
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        self._session_history[session_id].append(
            {"role": "user", "content": user_query}
        )
        self._session_history[session_id].append(
            {"role": "assistant", "content": agent_response, "agent": agent_name}
        )

    # ------------------------------------------------------------------
    # Core: handle a user query
    # ------------------------------------------------------------------
    async def handle(
        self,
        session_id: str,
        query: str,
        context: Optional[List[Dict]] = None,
    ) -> AgentResponse:
        """
        Main entry point.  Routes the query → the right agent → returns
        the agent's response wrapped in an AgentResponse.

        Parameters
        ----------
        session_id : str
            Unique identifier for the conversation session.
        query : str
            The user's natural-language query.
        context : list[dict], optional
            Additional context (e.g. prior turns from the frontend).

        Returns
        -------
        AgentResponse
        """
        # 1. Check if session already has an active agent (follow-up handling)
        active_agent_name = self._session_agent.get(session_id)

        # 2. Route the query
        routed_agent_name = self._route_by_keywords(query)

        if routed_agent_name is None:
            # Keywords didn't give a clear answer
            if active_agent_name:
                # Stick with the current agent for follow-ups
                routed_agent_name = active_agent_name
                logger.info(
                    "Session %s: no clear keyword match, staying with %s",
                    session_id, active_agent_name,
                )
            else:
                # First message with no keywords — ask LLM
                routed_agent_name = await self._route_by_llm(query)
                logger.info(
                    "Session %s: LLM routed to %s", session_id, routed_agent_name,
                )
        else:
            logger.info(
                "Session %s: keyword-routed to %s", session_id, routed_agent_name,
            )

        # 3. Get the agent
        agent = self._agents.get(routed_agent_name)
        if agent is None:
            return AgentResponse(
                agent_name="Orchestrator",
                content="I'm sorry, I couldn't find a suitable specialist for your query. Could you rephrase?",
                metadata={
                    "routed_to": None,
                    "session_id": session_id,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                },
            )

        # 4. Build context (merge frontend context + session history)
        history = self._get_session_history(session_id)
        merged_context = (context or []) + history

        # 5. Invoke the agent
        try:
            response = await agent.invoke(session_id, query, merged_context)
        except Exception as exc:
            logger.error(
                "Agent %s failed for session %s: %s",
                routed_agent_name, session_id, exc,
            )
            return AgentResponse(
                agent_name="Orchestrator",
                content=(
                    f"I tried to connect you with our {agent.name} specialist, "
                    f"but encountered an issue. Please try again."
                ),
                metadata={
                    "error": str(exc),
                    "routed_to": routed_agent_name,
                    "session_id": session_id,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                },
            )

        # 6. Update session state
        self._session_agent[session_id] = routed_agent_name
        self._update_session_history(
            session_id, query, response.content, routed_agent_name,
        )

        # 7. Enrich metadata with routing info
        response.metadata["routed_by"] = "orchestrator"
        response.metadata["routed_to"] = routed_agent_name

        return response

    # ------------------------------------------------------------------
    # Cross-agent collaboration
    # ------------------------------------------------------------------
    async def ask_agent(
        self,
        agent_name: str,
        session_id: str,
        query: str,
        context: Optional[List[Dict]] = None,
    ) -> AgentResponse:
        """
        Allow one agent to request information from another agent
        through the orchestrator (cross-agent communication).

        Example: The DietaryAgent might ask the VirtualDoctorAgent
        about a patient's medical condition before planning meals.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            return AgentResponse(
                agent_name="Orchestrator",
                content=f"Agent '{agent_name}' is not registered.",
                metadata={"error": "agent_not_found"},
            )

        logger.info(
            "Cross-agent request: session %s → %s", session_id, agent_name,
        )
        return await agent.invoke(session_id, query, context or [])

    # ------------------------------------------------------------------
    # Session utilities
    # ------------------------------------------------------------------
    def reset_session(self, session_id: str) -> None:
        """Clear all state for a session."""
        self._session_agent.pop(session_id, None)
        self._session_history.pop(session_id, None)
        logger.info("Session %s reset.", session_id)

    def get_active_agent(self, session_id: str) -> Optional[str]:
        """Return the name of the agent currently handling a session."""
        return self._session_agent.get(session_id)
