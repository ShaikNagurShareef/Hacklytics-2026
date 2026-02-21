"""FastAPI app. Orchestrator and other routes can be added here."""
from dotenv import load_dotenv

load_dotenv()  # Load .env from backend/ when running uvicorn from backend/

import logging
from contextlib import asynccontextmanager

from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from app.agents.wellbeing import WellbeingCounsellorAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.virtual_doctor.agent import VirtualDoctorAgent
from app.agents.dietary.agent import DietaryAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wellbeing_agent = WellbeingCounsellorAgent()
orchestrator = OrchestratorAgent()
virtual_doctor_agent = VirtualDoctorAgent()
dietary_agent = DietaryAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MEDORA", description="Multi-agent healthcare", lifespan=lifespan)


class ChatRequest(BaseModel):
    session_id: str = "default"
    query: str
    context: list = []


class ChatRequestWithImage(ChatRequest):
    """Chat request with optional image for Virtual Doctor image analysis."""
    image_base64: Optional[str] = None
    image_mime_type: str = "image/jpeg"


class ChatResponse(BaseModel):
    agent_name: str
    content: str
    metadata: dict = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/wellbeing/chat", response_model=ChatResponse)
async def wellbeing_chat(req: ChatRequest):
    """Invoke the Personal Wellbeing Counsellor agent."""
    try:
        resp = await wellbeing_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
        )
        return ChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            metadata=resp.metadata,
        )
    except RuntimeError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="LLM not configured (set GEMINI_API_KEY)")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("wellbeing chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Agent error")


@app.post("/wellbeing/voice")
async def wellbeing_voice(
    audio: UploadFile = File(..., description="Audio file from user (webm, wav, mp3, etc.)"),
    session_id: str = Form("default"),
):
    """
    Speech-to-speech wellbeing counselling endpoint.

    Pipeline:
      1. Receive audio upload from the user.
      2. Transcribe audio → text using Gemini STT.
      3. Run the Wellbeing Counsellor agent on the transcribed text.
      4. Convert the agent's text reply → audio using TTS.
      5. Return the audio response to the client.

    The response is an audio/mpeg file (MP3) that the client can play directly.
    A custom header `X-Transcribed-Text` contains the user's transcribed words.
    A custom header `X-Agent-Text` contains the agent's text reply.
    """
    from app.services.speech import speech_to_text, text_to_speech, text_to_speech_gemini

    # ── Step 1: Read the uploaded audio ──────────────────────────────
    audio_bytes = await audio.read()
    mime = audio.content_type or "audio/webm"
    logger.info("[voice] Received %d bytes of audio (%s)", len(audio_bytes), mime)

    # ── Step 2: Transcribe audio → text ──────────────────────────────
    try:
        transcribed_text = await speech_to_text(audio_bytes, mime_type=mime)
    except Exception as e:
        logger.exception("STT failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {e}")

    if not transcribed_text.strip():
        raise HTTPException(status_code=400, detail="Could not understand the audio. Please try again.")

    logger.info("[voice] Transcribed: %s", transcribed_text[:120])

    # ── Step 3: Run the wellbeing agent ──────────────────────────────
    try:
        agent_response = await wellbeing_agent.invoke(
            session_id=session_id,
            query=transcribed_text,
            context=[],
        )
        agent_text = agent_response.content
    except Exception as e:
        logger.exception("Wellbeing agent failed: %s", e)
        raise HTTPException(status_code=500, detail="Wellbeing agent error")

    logger.info("[voice] Agent reply: %s", agent_text[:120])

    # ── Step 4: Convert agent reply → audio ──────────────────────────
    try:
        # Try Gemini native TTS first, falls back to gTTS automatically
        audio_response = await text_to_speech_gemini(agent_text)
        if audio_response is None:
            audio_response = await text_to_speech(agent_text)
        content_type = "audio/mpeg"
    except Exception as e:
        logger.exception("TTS failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {e}")

    # ── Step 5: Return audio with metadata headers ───────────────────
    return Response(
        content=audio_response,
        media_type=content_type,
        headers={
            "X-Transcribed-Text": transcribed_text[:500],
            "X-Agent-Text": agent_text[:500],
            "X-Agent-Name": agent_response.agent_name,
            "X-Session-Id": session_id,
        },
    )


def _handle_agent_error(e: Exception) -> None:
    if "GEMINI_API_KEY" in str(e):
        raise HTTPException(status_code=503, detail="LLM not configured (set GEMINI_API_KEY)")
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def orchestrator_chat(req: ChatRequest):
    """Orchestrator: route query to the best agent (Virtual Doctor, Dietary, etc.)."""
    try:
        resp = await orchestrator.handle(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
        )
        return ChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            metadata=resp.metadata,
        )
    except RuntimeError as e:
        _handle_agent_error(e)
    except Exception as e:
        logger.exception("orchestrator chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Agent error")


@app.post("/virtual-doctor/chat", response_model=ChatResponse)
async def virtual_doctor_chat(req: ChatRequestWithImage):
    """Virtual Doctor: text chat or image analysis when image_base64 is provided."""
    try:
        resp = await virtual_doctor_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
            image_data=req.image_base64,
            image_mime_type=req.image_mime_type or "image/jpeg",
        )
        return ChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            metadata=resp.metadata,
        )
    except RuntimeError as e:
        _handle_agent_error(e)
    except Exception as e:
        logger.exception("virtual doctor chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Agent error")


@app.post("/dietary/chat", response_model=ChatResponse)
async def dietary_chat(req: ChatRequest):
    """Invoke the Dietary agent (meal plans, nutrition reports, BMR/TDEE)."""
    try:
        resp = await dietary_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
        )
        return ChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            metadata=resp.metadata,
        )
    except RuntimeError as e:
        _handle_agent_error(e)
    except Exception as e:
        logger.exception("dietary chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Agent error")
