"""Gemini LLM client for agents. Uses Flash by default, Pro when model specified.
Supports multimodal (text + image) via vision_chat()."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Dict, List, Optional, Union

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL_DEFAULT, GEMINI_MODEL_PRO, GEMINI_MODEL_MED

logger = logging.getLogger(__name__)

# Lazy import so app starts even without API key
_gen_model = None
_gen_model_pro = None
_gen_model_med = None


def _get_client():
    global _gen_model, _gen_model_pro, _gen_model_med
    if GEMINI_API_KEY is None:
        raise RuntimeError("GEMINI_API_KEY is not set")
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        if _gen_model is None:
            _gen_model = genai.GenerativeModel(GEMINI_MODEL_DEFAULT)
        if _gen_model_pro is None:
            _gen_model_pro = genai.GenerativeModel(GEMINI_MODEL_PRO)
        if _gen_model_med is None:
            _gen_model_med = genai.GenerativeModel(GEMINI_MODEL_MED)
        return _gen_model, _gen_model_pro, _gen_model_med
    except ImportError as e:
        raise RuntimeError("google-generativeai not installed") from e


def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    """Convert messages to a single prompt string for generate_content."""
    lines = []
    for m in messages:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        if role == "system":
            lines.append(f"[System]\n{content}\n")
        elif role == "user":
            lines.append(f"User: {content}\n")
        elif role in ("assistant", "model"):
            lines.append(f"Assistant: {content}\n")
    return "\n".join(lines).strip()


def _generate_sync(gen_model: Any, prompt: str) -> str:
    """Synchronous generate_content call (run in thread)."""
    response = gen_model.generate_content(prompt)
    if not response or not response.text:
        return ""
    return response.text.strip()


class _LLMClientWrapper:
    """Wrapper exposing generate(messages) for agents that expect it."""

    async def generate(self, messages: List[Dict[str, Any]], **kwargs: Any) -> str:
        return await chat(messages, **kwargs)


def get_llm_client() -> _LLMClientWrapper:
    """Return a client object with async generate(messages) for VirtualDoctor/Dietary agents."""
    return _LLMClientWrapper()


async def chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    *,
    timeout_sec: float = 60.0,
) -> str:
    """
    Send messages to Gemini and return the model reply text.
    model: None = use default (Flash), "pro" or GEMINI_MODEL_PRO = use Pro, "med" or GEMINI_MODEL_MED = use Med.
    """
    flash, pro, med = _get_client()
    use_pro = model in ("pro", "gemini-1.5-pro", GEMINI_MODEL_PRO)
    use_med = model in ("med", "medgemma", GEMINI_MODEL_MED)
    
    if use_med:
        gen_model = med
    elif use_pro:
        gen_model = pro
    else:
        gen_model = flash
    prompt = _messages_to_prompt(messages)
    try:
        reply = await asyncio.wait_for(
            asyncio.to_thread(_generate_sync, gen_model, prompt),
            timeout=timeout_sec,
        )
        return reply or ""
    except asyncio.TimeoutError:
        logger.warning("LLM call timed out after %s s", timeout_sec)
        raise
    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        raise


def _generate_vision_sync(gen_model: Any, content_parts: list) -> str:
    """Synchronous multimodal generate_content call (run in thread)."""
    response = gen_model.generate_content(content_parts)
    if not response or not response.text:
        return ""
    return response.text.strip()


async def vision_chat(
    prompt: str,
    image_data: Union[bytes, str],
    mime_type: str = "image/jpeg",
    model: Optional[str] = None,
    *,
    timeout_sec: float = 90.0,
) -> str:
    """
    Send a text prompt + image to Gemini for multimodal analysis.

    Parameters
    ----------
    prompt : str
        The text instruction / question about the image.
    image_data : bytes | str
        Raw image bytes OR a base64-encoded string.
    mime_type : str
        MIME type of the image (default: image/jpeg).
    model : str, optional
        None = Flash (default), "pro" = Pro model.
    timeout_sec : float
        Max seconds to wait for the API response.

    Returns
    -------
    str
        The model's text response about the image.
    """
    flash, pro = _get_client()
    use_pro = model in ("pro", "gemini-1.5-pro", GEMINI_MODEL_PRO)
    gen_model = pro if use_pro else flash

    # Convert base64 string → bytes if needed
    if isinstance(image_data, str):
        image_data = base64.b64decode(image_data)

    # Build multimodal content: [text_prompt, image_part]
    import google.generativeai as genai
    image_part = {"mime_type": mime_type, "data": image_data}
    content_parts = [prompt, image_part]

    try:
        reply = await asyncio.wait_for(
            asyncio.to_thread(_generate_vision_sync, gen_model, content_parts),
            timeout=timeout_sec,
        )
        return reply or ""
    except asyncio.TimeoutError:
        logger.warning("Vision LLM call timed out after %s s", timeout_sec)
        raise
    except Exception as e:
        logger.exception("Vision LLM call failed: %s", e)
        raise


def parse_json_from_text(text: str) -> Optional[dict]:
    """Extract a single JSON object from model output (handles markdown code blocks)."""
    text = (text or "").strip()
    if not text:
        return None
    # Try raw parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find ```json ... ``` or ``` ... ```
    start = text.find("```")
    if start != -1:
        rest = text[start + 3:]
        if rest.lower().startswith("json"):
            rest = rest[4:].lstrip()
        end = rest.find("```")
        if end != -1:
            rest = rest[:end]
        try:
            return json.loads(rest.strip())
        except json.JSONDecodeError:
            pass
    # Try first { ... }
    i = text.find("{")
    j = text.rfind("}")
    if i != -1 and j != -1 and j > i:
        try:
            return json.loads(text[i : j + 1])
        except json.JSONDecodeError:
            pass
    return None
