"""Personal Wellbeing Counsellor Agent: stress, anxiety, depression detection and natural counselling."""
import logging
from typing import Any, Dict, List

from app.agents.base import AgentResponse, BaseAgent
from app.agents.wellbeing.prompts import (
    build_counselling_messages,
    build_detection_messages,
)
from app.agents.wellbeing.schemas import (
    AnxietyLevel,
    DepressionLevel,
    StressLevel,
    WellbeingIndicators,
)
from app.services.llm_client import chat as llm_chat
from app.services.llm_client import chat_stream
from app.services.llm_client import parse_json_from_text

logger = logging.getLogger(__name__)

# In-memory session store: session_id -> list of {role, content} (last N turns)
_sessions: Dict[str, List[Dict[str, Any]]] = {}
MAX_HISTORY = 10


def _conversation_to_text(context: List[Dict], query: str) -> str:
    """Turn context + current query into a single text block for detection."""
    lines = []
    for msg in context[-MAX_HISTORY:]:
        role = msg.get("role", "user")
        content = msg.get("content") or msg.get("text", "")
        lines.append(f"{role}: {content}")
    lines.append(f"user: {query}")
    return "\n".join(lines)


def _indicators_to_str(indicators: WellbeingIndicators) -> str:
    return f"stress={indicators.stress.value}, anxiety={indicators.anxiety.value}, depression={indicators.depression.value}"


def _needs_disclaimer(indicators: WellbeingIndicators) -> bool:
    if indicators.stress == StressLevel.HIGH:
        return True
    if indicators.anxiety in (AnxietyLevel.MODERATE, AnxietyLevel.SEVERE):
        return True
    if indicators.depression in (
        DepressionLevel.MODERATE,
        DepressionLevel.MODERATELY_SEVERE,
        DepressionLevel.SEVERE,
    ):
        return True
    return False


class WellbeingCounsellorAgent(BaseAgent):
    """Agent that detects stress/anxiety/depression from conversation and provides supportive counselling."""

    @property
    def name(self) -> str:
        return "Personal Wellbeing Counsellor"

    @property
    def description(self) -> str:
        return (
            "Handles conversations about mood, stress, anxiety, depression, and general wellbeing. "
            "Provides supportive counselling and motivation; recognizes signs of stress, anxiety, or low mood."
        )

    async def invoke(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        **kwargs: Any,
    ) -> AgentResponse:
        # Ensure session exists
        if session_id not in _sessions:
            _sessions[session_id] = []
        history = _sessions[session_id]

        # 1) Detection: get stress/anxiety/depression from conversation
        conversation_text = _conversation_to_text(context, query)
        detection_messages = build_detection_messages(conversation_text)
        try:
            detection_raw = await llm_chat(detection_messages, model=None, timeout_sec=30.0)
            parsed = parse_json_from_text(detection_raw)
            if parsed:
                indicators = WellbeingIndicators.from_parsed(parsed)
            else:
                indicators = WellbeingIndicators()
                logger.warning("Detection LLM did not return valid JSON; using defaults")
        except Exception as e:
            logger.exception("Detection failed: %s", e)
            indicators = WellbeingIndicators()

        # 2) Counselling reply (use Pro when indicators are moderate+ for more care)
        # When user has already answered at least once, ask 3 follow-up questions.
        user_turns_in_history = sum(1 for m in history if m.get("role") == "user")
        is_follow_up = user_turns_in_history >= 1
        use_pro = _needs_disclaimer(indicators)
        counselling_messages = build_counselling_messages(
            history,
            query,
            _indicators_to_str(indicators),
            use_pro=use_pro,
            is_follow_up=is_follow_up,
        )
        try:
            reply = await llm_chat(
                counselling_messages,
                model="pro" if use_pro else None,
                timeout_sec=45.0,
            )
        except Exception as e:
            logger.exception("Counselling LLM failed: %s", e)
            reply = (
                "I'm here for you. I'm having a small technical moment—please try again in a bit, "
                "or reach out to someone you trust or a helpline if you need to talk right now."
            )

        # 3) Update session history (append user + assistant)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": reply})
        if len(history) > MAX_HISTORY * 2:
            _sessions[session_id] = history[-MAX_HISTORY * 2 :]

        metadata = indicators.to_metadata()

        return AgentResponse(
            agent_name=self.name,
            content=reply or "I hear you. Would you like to share a bit more?",
            metadata=metadata,
        )

    async def invoke_stream(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        **kwargs: Any,
    ):
        """
        Same as invoke() but streams the counselling reply as text chunks.
        Yields: {"type": "meta", "metadata": dict}, then {"type": "text", "content": str}, then {"type": "done", "content": full_reply}.
        """
        if session_id not in _sessions:
            _sessions[session_id] = []
        history = _sessions[session_id]
        conversation_text = _conversation_to_text(context, query)
        detection_messages = build_detection_messages(conversation_text)
        try:
            detection_raw = await llm_chat(detection_messages, model=None, timeout_sec=30.0)
            parsed = parse_json_from_text(detection_raw)
            indicators = WellbeingIndicators.from_parsed(parsed) if parsed else WellbeingIndicators()
        except Exception as e:
            logger.exception("Detection failed: %s", e)
            indicators = WellbeingIndicators()
        user_turns_in_history = sum(1 for m in history if m.get("role") == "user")
        is_follow_up = user_turns_in_history >= 1
        use_pro = _needs_disclaimer(indicators)
        counselling_messages = build_counselling_messages(
            history,
            query,
            _indicators_to_str(indicators),
            use_pro=use_pro,
            is_follow_up=is_follow_up,
        )
        yield {"type": "meta", "metadata": indicators.to_metadata()}
        full_reply = []
        try:
            async for chunk in chat_stream(
                counselling_messages,
                model="pro" if use_pro else None,
                timeout_sec=45.0,
            ):
                full_reply.append(chunk)
                yield {"type": "text", "content": chunk}
        except Exception as e:
            logger.exception("Counselling stream failed: %s", e)
            fallback = (
                "I'm here for you. I'm having a small technical moment—please try again in a bit, "
                "or reach out to someone you trust or a helpline if you need to talk right now."
            )
            full_reply = [fallback]
            yield {"type": "text", "content": fallback}
        reply = "".join(full_reply).strip() or "I hear you. Would you like to share a bit more?"
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": reply})
        if len(history) > MAX_HISTORY * 2:
            _sessions[session_id] = history[-MAX_HISTORY * 2 :]
        yield {"type": "done", "content": reply}
