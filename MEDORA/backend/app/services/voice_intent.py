"""
Voice Intent Classifier
========================
Takes a speech transcript and classifies it into a structured action
that the frontend can execute (navigate, send query, toggle theme, etc.).
Uses Gemini LLM for intent classification.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.services.llm_client import chat, parse_json_from_text

logger = logging.getLogger(__name__)

# All available actions and their descriptions for the LLM
INTENT_SYSTEM_PROMPT = """You are MEDORA's voice-action classifier. Given a user's spoken transcript, classify it into ONE structured JSON action.

Available actions:

1. **navigate** — User wants to go to a specific page.
   Routes: /ask (main chat), /virtual-doctor, /dietary, /wellbeing, /wellbeing/voice, /diagnostic, /profile, /about
   Return: {"action": "navigate", "target": "<route>", "speech": "<brief confirmation>"}

2. **send_query** — User is asking a health/medical/diet/wellbeing question that should be answered by an agent.
   Return: {"action": "send_query", "query": "<the user's question>", "speech": null}

3. **toggle_theme** — User wants to switch between dark and light mode.
   Return: {"action": "toggle_theme", "speech": "Switching theme for you"}

4. **greeting** — User is saying hello, hi, or a general greeting.
   Return: {"action": "greeting", "speech": "Hi there! I'm MEDORA, your healthcare assistant. How can I help you today?"}

5. **logout** — User wants to sign out / log out.
   Return: {"action": "logout", "speech": "Signing you out"}

6. **new_chat** — User wants to start a new conversation.
   Return: {"action": "new_chat", "speech": "Starting a fresh conversation"}

Rules:
- Navigation keywords: "go to", "open", "take me to", "show me", "navigate to", "switch to"
- If the user says an agent name (doctor, dietary, wellbeing, diagnostics), it's a navigate action.
- If the user asks a QUESTION about health, symptoms, diet, emotions, etc., it's a send_query action — extract their real question.
- ONLY return valid JSON. No explanation, no markdown. Just the JSON object.
- Keep "speech" responses short and friendly (under 15 words).
"""


async def classify_intent(transcript: str) -> Dict[str, Any]:
    """
    Classify a voice transcript into a structured action.
    
    Returns a dict like:
      {"action": "navigate", "target": "/dietary", "speech": "Opening dietary for you"}
      {"action": "send_query", "query": "I have a headache", "speech": null}
    """
    if not transcript or not transcript.strip():
        return {"action": "greeting", "speech": "I didn't catch that. Could you try again?"}

    transcript = transcript.strip()

    # Fast-path: check for obvious navigation keywords before hitting LLM
    fast_result = _fast_classify(transcript)
    if fast_result:
        logger.info("Voice intent fast-path: %s -> %s", transcript[:50], fast_result["action"])
        return fast_result

    # LLM classification
    try:
        response = await chat(
            [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript: \"{transcript}\""},
            ],
            timeout_sec=15.0,
        )
        parsed = parse_json_from_text(response)
        if parsed and "action" in parsed:
            logger.info("Voice intent LLM: %s -> %s", transcript[:50], parsed["action"])
            return parsed
    except Exception as exc:
        logger.warning("Voice intent LLM classification failed: %s", exc)

    # Fallback: treat as a send_query
    return {"action": "send_query", "query": transcript, "speech": None}


def _fast_classify(transcript: str) -> Optional[Dict[str, Any]]:
    """Keyword-based fast classification for obvious intents."""
    t = transcript.lower().strip()

    # Theme toggle
    if any(kw in t for kw in ["dark mode", "light mode", "switch theme", "toggle theme", "change theme"]):
        return {"action": "toggle_theme", "speech": "Switching theme for you"}

    # Greetings
    if t in ("hello", "hi", "hey", "hey there", "hi there", "hello there", "good morning", "good afternoon", "good evening"):
        return {"action": "greeting", "speech": "Hi there! I'm MEDORA. How can I help you today?"}

    # Logout
    if any(kw in t for kw in ["log out", "logout", "sign out", "sign me out"]):
        return {"action": "logout", "speech": "Signing you out"}

    # New chat
    if any(kw in t for kw in ["new chat", "new conversation", "start over", "fresh chat", "clear chat"]):
        return {"action": "new_chat", "speech": "Starting a fresh conversation"}

    # Navigation — check for explicit navigation keywords
    nav_phrases = ["go to", "open", "take me to", "show me", "navigate to", "switch to", "open up"]
    has_nav_keyword = any(kw in t for kw in nav_phrases)

    route_map = {
        "dietary": "/dietary",
        "diet": "/dietary",
        "nutrition": "/dietary",
        "meal": "/dietary",
        "doctor": "/virtual-doctor",
        "virtual doctor": "/virtual-doctor",
        "wellbeing": "/wellbeing",
        "mental health": "/wellbeing",
        "counselor": "/wellbeing",
        "counsellor": "/wellbeing",
        "diagnostic": "/diagnostic",
        "diagnostics": "/diagnostic",
        "imaging": "/diagnostic",
        "scan": "/diagnostic",
        "profile": "/profile",
        "my profile": "/profile",
        "account": "/profile",
        "settings": "/profile",
        "about": "/about",
        "about us": "/about",
        "ask": "/ask",
        "home": "/ask",
        "main": "/ask",
        "voice": "/wellbeing/voice",
        "voice mode": "/wellbeing/voice",
    }

    if has_nav_keyword:
        for keyword, route in route_map.items():
            if keyword in t:
                label = route.strip("/").replace("-", " ").title()
                return {"action": "navigate", "target": route, "speech": f"Opening {label} for you"}

    return None
