"""
Speech Services for MEDORA
==========================
Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities
using the Google Gemini API for STT (multimodal audio understanding)
and Google Cloud Text-to-Speech / gTTS for TTS.

The STT pipeline sends raw audio to Gemini which natively understands
speech. The TTS pipeline converts the agent's text reply into audio
bytes that can be streamed back to the client.
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import tempfile
from typing import Optional

from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


# ── Speech-to-Text via Gemini (multimodal audio) ─────────────────────

STT_PROMPT = (
    "You are a medical speech transcription assistant. "
    "Listen to the audio carefully and transcribe the user's speech verbatim. "
    "Output ONLY the transcribed text. Do not add any commentary, "
    "timestamps, or formatting. Just the raw spoken words."
)


async def speech_to_text(
    audio_data: bytes,
    mime_type: str = "audio/webm",
    *,
    timeout_sec: float = 60.0,
) -> str:
    """
    Transcribe audio bytes to text using Gemini's native audio understanding.

    Parameters
    ----------
    audio_data : bytes
        Raw audio bytes (supports webm, wav, mp3, ogg, flac, etc.)
    mime_type : str
        MIME type of the audio (default: audio/webm for browser recordings).
    timeout_sec : float
        Max seconds to wait for the API response.

    Returns
    -------
    str
        Transcribed text from the audio.
    """
    if GEMINI_API_KEY is None:
        raise RuntimeError("GEMINI_API_KEY is not set")

    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel("gemini-2.0-flash")

    audio_part = {"mime_type": mime_type, "data": audio_data}
    content_parts = [STT_PROMPT, audio_part]

    def _transcribe():
        response = model.generate_content(content_parts)
        if not response or not response.text:
            return ""
        return response.text.strip()

    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(_transcribe),
            timeout=timeout_sec,
        )
        logger.info("STT transcription: %s", text[:100])
        return text
    except asyncio.TimeoutError:
        logger.warning("STT timed out after %s s", timeout_sec)
        raise
    except Exception as e:
        logger.exception("STT failed: %s", e)
        raise


# ── Text-to-Speech via gTTS (Google Translate TTS) ───────────────────

async def text_to_speech(
    text: str,
    lang: str = "en",
    slow: bool = False,
) -> bytes:
    """
    Convert text to speech audio bytes (MP3 format) using gTTS.

    Parameters
    ----------
    text : str
        The text to speak.
    lang : str
        Language code (default: 'en').
    slow : bool
        If True, speak slowly.

    Returns
    -------
    bytes
        MP3 audio bytes.
    """

    def _synthesize() -> bytes:
        try:
            from gtts import gTTS
        except ImportError:
            raise RuntimeError(
                "gTTS is not installed. Install it with: pip install gTTS"
            )

        tts = gTTS(text=text, lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()

    try:
        audio_bytes = await asyncio.to_thread(_synthesize)
        logger.info("TTS generated %d bytes of audio", len(audio_bytes))
        return audio_bytes
    except Exception as e:
        logger.exception("TTS failed: %s", e)
        raise


# ── Gemini-native TTS (uses Gemini's audio generation) ───────────────

async def text_to_speech_gemini(
    text: str,
    *,
    timeout_sec: float = 60.0,
) -> Optional[bytes]:
    """
    Convert text to speech using Gemini's native audio generation capabilities.
    Falls back to gTTS if Gemini audio generation is not available.

    Returns
    -------
    bytes or None
        Audio bytes (WAV format) or None on failure.
    """
    if GEMINI_API_KEY is None:
        logger.warning("GEMINI_API_KEY not set; falling back to gTTS")
        return await text_to_speech(text)

    try:
        import httpx

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent"
            f"?key={GEMINI_API_KEY.strip()}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"Read the following text aloud in a warm, calm, "
                                f"empathetic therapist voice. The text is:\n\n{text}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": "Kore"}
                    }
                },
            },
        }

        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            r = await client.post(url, json=payload)

        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            logger.warning("Gemini TTS returned no candidates; falling back to gTTS")
            return await text_to_speech(text)

        parts = candidates[0].get("content", {}).get("parts") or []
        for part in parts:
            if "inlineData" in part:
                b64 = part["inlineData"].get("data")
                if b64:
                    logger.info("Gemini TTS succeeded")
                    return base64.b64decode(b64)

        logger.warning("No audio data in Gemini TTS response; falling back to gTTS")
        return await text_to_speech(text)

    except Exception as e:
        logger.warning("Gemini TTS failed (%s); falling back to gTTS", e)
        return await text_to_speech(text)
