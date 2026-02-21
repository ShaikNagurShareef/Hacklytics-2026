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


# ── Speech-to-Text ────────────────────────────────────────────────────
#
# Primary: Google Speech Recognition (via SpeechRecognition library)
#   - Accurate, no hallucination, free tier
#   - Requires converting webm → wav first
#
# Fallback: Gemini multimodal (may hallucinate on short clips)

async def speech_to_text(
    audio_data: bytes,
    mime_type: str = "audio/webm",
    *,
    timeout_sec: float = 60.0,
) -> str:
    """
    Transcribe audio bytes to text.
    Uses the browser's Web Speech API result if provided,
    otherwise converts audio and uses Google Speech Recognition.
    """
    if not audio_data or len(audio_data) < 100:
        return ""

    # Try Google Speech Recognition (more accurate, no hallucination)
    try:
        return await _transcribe_google_sr(audio_data, mime_type)
    except Exception as e:
        logger.warning("Google SR failed (%s), trying Gemini STT...", e)

    # Fallback: Gemini multimodal
    try:
        return await _transcribe_gemini(audio_data, mime_type, timeout_sec)
    except Exception as e:
        logger.exception("All STT methods failed: %s", e)
        raise


async def _transcribe_google_sr(audio_data: bytes, mime_type: str) -> str:
    """Transcribe using Google Speech Recognition (SpeechRecognition library)."""

    def _do_recognize():
        import speech_recognition as sr
        from pydub import AudioSegment

        # Convert webm/mp3 → wav using pydub
        audio_input = io.BytesIO(audio_data)
        if "webm" in mime_type:
            seg = AudioSegment.from_file(audio_input, format="webm")
        elif "mp3" in mime_type or "mpeg" in mime_type:
            seg = AudioSegment.from_mp3(audio_input)
        elif "ogg" in mime_type:
            seg = AudioSegment.from_ogg(audio_input)
        else:
            seg = AudioSegment.from_file(audio_input)

        # Export to WAV
        wav_buf = io.BytesIO()
        seg.export(wav_buf, format="wav")
        wav_buf.seek(0)

        # Recognize
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_buf) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)
        return text.strip()

    result = await asyncio.to_thread(_do_recognize)
    logger.info("Google SR transcription: %s", result[:100])
    return result


async def _transcribe_gemini(
    audio_data: bytes, mime_type: str, timeout_sec: float
) -> str:
    """Fallback: Transcribe using Gemini multimodal API."""
    if GEMINI_API_KEY is None:
        raise RuntimeError("GEMINI_API_KEY is not set")

    import httpx

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY.strip()}"
    )

    audio_b64 = base64.b64encode(audio_data).decode("utf-8")

    prompt = (
        "TASK: Transcribe the spoken words in this audio clip EXACTLY as spoken. "
        "Output ONLY the verbatim transcription. Do NOT paraphrase, summarize, "
        "add words, or generate content. If silent, output: [silence]"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": audio_b64}},
                ],
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            r = await client.post(url, json=payload)

        r.raise_for_status()
        data = r.json()

        candidates = data.get("candidates") or []
        if not candidates:
            return ""

        parts = candidates[0].get("content", {}).get("parts") or []
        text = ""
        for part in parts:
            if "text" in part:
                text += part["text"]

        text = text.strip()
        logger.info("Gemini STT transcription: %s", text[:100])
        return text

    except Exception as e:
        logger.exception("Gemini STT failed: %s", e)
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


# ── Gemini-native TTS (dedicated TTS model) ──────────────────────────

async def text_to_speech_gemini(
    text: str,
    *,
    timeout_sec: float = 90.0,
) -> Optional[bytes]:
    """
    Convert text to speech using Gemini's dedicated TTS model.
    Uses gemini-2.5-flash-preview-tts for the most natural speech output.
    Falls back to gTTS if Gemini TTS is not available.
    """
    if GEMINI_API_KEY is None:
        logger.warning("GEMINI_API_KEY not set; falling back to gTTS")
        return await text_to_speech(text)

    try:
        import httpx

        # Use the dedicated TTS model for best quality
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.5-flash-preview-tts:generateContent"
            f"?key={GEMINI_API_KEY.strip()}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"Speak the following text in a warm, calm, "
                                f"caring therapist voice:\n\n{text}"
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
                    raw_pcm = base64.b64decode(b64)
                    # Gemini TTS returns raw PCM (L16, 24kHz, mono)
                    # Wrap in WAV header so browsers can play it
                    wav_audio = _pcm_to_wav(raw_pcm, sample_rate=24000, channels=1, bit_depth=16)
                    logger.info("Gemini TTS (dedicated model) succeeded, %d bytes WAV", len(wav_audio))
                    return wav_audio

        logger.warning("No audio in Gemini TTS response; falling back to gTTS")
        return await text_to_speech(text)

    except Exception as e:
        logger.warning("Gemini TTS failed (%s); falling back to gTTS", e)
        return await text_to_speech(text)


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bit_depth: int = 16) -> bytes:
    """Wrap raw PCM audio data in a WAV file header."""
    import struct
    byte_rate = sample_rate * channels * (bit_depth // 8)
    block_align = channels * (bit_depth // 8)
    data_size = len(pcm_data)
    file_size = 36 + data_size

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',       # ChunkID
        file_size,     # ChunkSize
        b'WAVE',       # Format
        b'fmt ',       # Subchunk1ID
        16,            # Subchunk1Size (PCM)
        1,             # AudioFormat (PCM = 1)
        channels,      # NumChannels
        sample_rate,   # SampleRate
        byte_rate,     # ByteRate
        block_align,   # BlockAlign
        bit_depth,     # BitsPerSample
        b'data',       # Subchunk2ID
        data_size,     # Subchunk2Size
    )
    return header + pcm_data

