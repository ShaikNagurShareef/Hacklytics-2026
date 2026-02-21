from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from app.agents.base import AgentResponse, BaseAgent
from app.agents.visualization.prompts import (
    VISUALIZATION_SYSTEM_PROMPT,
    TUTORIAL_GENERATION_PROMPT,
)
from app.agents.visualization.schemas import VisualizationTutorial
from app.services.llm_client import parse_json_from_text

logger = logging.getLogger(__name__)


class VisualizationAgent(BaseAgent):
    """
    Visualization agent that creates step-by-step visual tutorials for patients
    to understand their diagnostic reports or medical conditions out loud using
    the Nano Banana model exclusively.
    """

    @property
    def name(self) -> str:
        return "VisualizationAgent"

    @property
    def description(self) -> str:
        return (
            "Creates visually-driven, easy-to-understand tutorials for patients "
            "struggling to understand standard diagnostic reports or conditions."
        )

    async def invoke(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        report_text: str = "",
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Takes the user's query and an optional diagnostic report (from context
        or passed directly). Generates a helpful structured tutorial.
        """
        logger.info(
            f"[VisualizationAgent] processing tutorial for session={session_id}"
        )

        prompt = TUTORIAL_GENERATION_PROMPT.format(
            context=report_text or "No specific report provided in context. Rely on the user inquiry.",
            query=query,
        )

        messages = [
            {"role": "system", "content": VISUALIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        from app.services.llm_client import chat
        
        # Use Nano Banana exclusively for tutorial generation!
        try:
            reply_text = await chat(messages, model="nano")
        except Exception as exc:
            logger.error("Visualization generation failed: %s", exc)
            reply_text = "I'm sorry, I couldn't generate the tutorial at this time."

        tutorial_data = None
        parsed_json = parse_json_from_text(reply_text)

        if parsed_json:
            try:
                tutorial_obj = VisualizationTutorial(**parsed_json)
                tutorial_data = tutorial_obj.model_dump()
            except ValidationError as e:
                logger.error(f"Failed to validate Visualization schema: {e}")

        # Format a human-readable markdown response from the JSON
        if tutorial_data:
            content = f"## 📚 Medical Tutorial: {tutorial_data.get('overview', 'Overview')}\n\n"
            for step in tutorial_data.get("steps", []):
                content += f"### Step {step.get('step_number')}: {step.get('title')}\n"
                content += f"{step.get('explanation')}\n\n"
                content += f"> 📸 *Visualization Cue: {step.get('image_prompt')}*\n\n"
        else:
            # Fallback if it didn't parse into clean JSON
            content = reply_text
            if not content.startswith("## ") and not "Step" in content:
                 content = f"## 📚 Medical Tutorial\n\n{content}"

        return AgentResponse(
            agent_name=self.name,
            content=content,
            metadata={
                "intent": "tutorial_generation",
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "tutorial_data": tutorial_data,
            },
        )
