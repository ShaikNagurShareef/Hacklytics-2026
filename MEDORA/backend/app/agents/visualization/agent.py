from __future__ import annotations

import base64
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
from app.services.llm_client import parse_json_from_text, generate_image

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

        # Format: dashboard section (from diagnostic report) + tutorial steps
        step_images: List[Dict[str, Any]] = []
        if tutorial_data:
            content = f"## 📚 Medical Tutorial: {tutorial_data.get('overview', 'Overview')}\n\n"
            dashboard = tutorial_data.get("dashboard") or {}
            if isinstance(dashboard, dict) and (dashboard.get("key_findings") or dashboard.get("summary")):
                content += "### 📊 Dashboard Summary\n\n"
                if dashboard.get("summary"):
                    content += f"**Summary:** {dashboard['summary']}\n\n"
                if dashboard.get("modality") or dashboard.get("body_region") or dashboard.get("severity"):
                    content += "| Modality | Body Region | Severity |\n|----------|-------------|----------|\n"
                    content += f"| {dashboard.get('modality', '—')} | {dashboard.get('body_region', '—')} | {dashboard.get('severity', '—')} |\n\n"
                if dashboard.get("key_findings"):
                    content += "**Key findings:**\n"
                    for f in dashboard["key_findings"]:
                        content += f"- {f}\n"
                    content += "\n"
                if dashboard.get("recommendations"):
                    content += "**Recommendations:**\n"
                    for r in dashboard["recommendations"]:
                        content += f"- {r}\n"
                    content += "\n"
                content += "---\n\n"
            content += "### 📖 Step-by-step tutorial\n\n"
            for step in tutorial_data.get("steps", []):
                content += f"### Step {step.get('step_number')}: {step.get('title')}\n"
                content += f"{step.get('explanation')}\n\n"
                image_prompt = step.get("image_prompt") or ""
                if image_prompt:
                    img_bytes = await generate_image(image_prompt, timeout_sec=45)
                    if img_bytes:
                        b64 = base64.b64encode(img_bytes).decode("ascii")
                        content += f"![Step {step.get('step_number')}](data:image/png;base64,{b64})\n\n"
                        step_images.append({"step_number": step.get("step_number"), "image_base64": b64})
                    else:
                        content += f"> 📸 *Visualization Cue: {image_prompt}*\n\n"
                else:
                    content += "\n"
        else:
            content = reply_text
            if not content.startswith("## ") and "Step" not in content:
                content = f"## 📚 Medical Tutorial\n\n{content}"

        metadata = {
            "intent": "tutorial_generation",
            "session_id": session_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "tutorial_data": tutorial_data,
        }
        if tutorial_data and tutorial_data.get("dashboard"):
            metadata["dashboard"] = tutorial_data["dashboard"]
        if tutorial_data and step_images:
            metadata["step_images"] = step_images

        return AgentResponse(
            agent_name=self.name,
            content=content,
            metadata=metadata,
        )
