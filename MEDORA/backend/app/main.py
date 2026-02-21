"""FastAPI app. Orchestrator and other routes can be added here."""
from dotenv import load_dotenv

load_dotenv()  # Load .env from backend/ when running uvicorn from backend/

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.wellbeing import WellbeingCounsellorAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.virtual_doctor.agent import VirtualDoctorAgent
from app.agents.dietary.agent import DietaryAgent
from app.agents.diagnostic import DiagnosticAgent
from app.db.database import get_db, init_db
from app.dependencies import get_current_user_optional
from app.models.user import User
from app.routers import auth, users
from app.services.chat_history import append_turn
from app.services.voice_intent import classify_intent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wellbeing_agent = WellbeingCounsellorAgent()
orchestrator = OrchestratorAgent()
virtual_doctor_agent = VirtualDoctorAgent()
dietary_agent = DietaryAgent()
diagnostic_agent = DiagnosticAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MEDORA", description="Multi-agent healthcare", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


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
async def wellbeing_chat(
    req: ChatRequest,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Invoke the Personal Wellbeing Counsellor agent."""
    try:
        resp = await wellbeing_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
        )
        if user:
            try:
                append_turn(db, user.id, req.session_id, req.query, resp.content, resp.agent_name, agent_type="wellbeing")
            except Exception as e:
                logger.warning("Chat history save failed: %s", e)
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


async def _wellbeing_stream_generator(req: ChatRequest, user: User | None, db: Session):
    full_content = ""
    async for event in wellbeing_agent.invoke_stream(
        session_id=req.session_id,
        query=req.query,
        context=req.context,
    ):
        line = json.dumps(event) + "\n"
        yield line.encode("utf-8")
        if event.get("type") == "done":
            full_content = event.get("content", "")
    if user and full_content:
        try:
            append_turn(db, user.id, req.session_id, req.query, full_content, "Personal Wellbeing Counsellor", agent_type="wellbeing")
        except Exception as e:
            logger.warning("Chat history save failed: %s", e)


@app.post("/wellbeing/chat/stream")
async def wellbeing_chat_stream(
    req: ChatRequest,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Stream Wellbeing reply as NDJSON: {type: 'meta'|'text'|'done', ...}."""
    return StreamingResponse(
        _wellbeing_stream_generator(req, user, db),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _handle_agent_error(e: Exception) -> None:
    if "GEMINI_API_KEY" in str(e):
        raise HTTPException(status_code=503, detail="LLM not configured (set GEMINI_API_KEY)")
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def orchestrator_chat(
    req: ChatRequestWithImage,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Orchestrator: route query to the best agent (Virtual Doctor, Dietary, etc.)."""
    try:
        resp = await orchestrator.handle(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
            image_data=req.image_base64,
            image_mime_type=req.image_mime_type or "image/jpeg",
        )
        if user:
            try:
                append_turn(db, user.id, req.session_id, req.query, resp.content, resp.agent_name, agent_type="ask")
            except Exception as e:
                logger.warning("Chat history save failed: %s", e)
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
async def virtual_doctor_chat(
    req: ChatRequestWithImage,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Virtual Doctor: text chat or image analysis when image_base64 is provided."""
    try:
        resp = await virtual_doctor_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
            image_data=req.image_base64,
            image_mime_type=req.image_mime_type or "image/jpeg",
        )
        if user:
            try:
                append_turn(db, user.id, req.session_id, req.query, resp.content, resp.agent_name, agent_type="virtual-doctor")
            except Exception as e:
                logger.warning("Chat history save failed: %s", e)
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
async def dietary_chat(
    req: ChatRequest,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Invoke the Dietary agent (meal plans, nutrition reports, BMR/TDEE)."""
    try:
        resp = await dietary_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
        )
        if user:
            try:
                append_turn(db, user.id, req.session_id, req.query, resp.content, resp.agent_name, agent_type="dietary")
            except Exception as e:
                logger.warning("Chat history save failed: %s", e)
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


@app.post("/diagnostic/chat", response_model=ChatResponse)
async def diagnostic_chat(
    req: ChatRequestWithImage,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Diagnostic imaging agent: analyse medical images and generate reports."""
    try:
        resp = await diagnostic_agent.invoke(
            session_id=req.session_id,
            query=req.query,
            context=req.context,
            image_data=req.image_base64,
            image_mime_type=req.image_mime_type or "image/jpeg",
        )
        if user:
            try:
                append_turn(db, user.id, req.session_id, req.query, resp.content, resp.agent_name, agent_type="diagnostic")
            except Exception as e:
                logger.warning("Chat history save failed: %s", e)
        return ChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            metadata=resp.metadata,
        )
    except RuntimeError as e:
        _handle_agent_error(e)
    except Exception as e:
        logger.exception("diagnostic chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Agent error")


# ── Voice intent classification ──────────────────────────────────────

class VoiceIntentRequest(BaseModel):
    transcript: str
    session_id: str = "default"
    context: list = []


@app.post("/voice/intent")
async def voice_intent(
    req: VoiceIntentRequest,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Classify a voice transcript into an action the frontend can execute."""
    try:
        result = await classify_intent(req.transcript)
    except Exception as exc:
        logger.exception("Voice intent classification failed: %s", exc)
        # Fallback: treat as send_query
        result = {"action": "send_query", "query": req.transcript, "speech": None}

    # For send_query actions, also invoke the orchestrator so we return the answer
    if result.get("action") == "send_query" and result.get("query"):
        try:
            resp = await orchestrator.handle(
                session_id=req.session_id,
                query=result["query"],
                context=req.context,
            )
            result["agent_name"] = resp.agent_name
            result["response"] = resp.content
            result["metadata"] = resp.metadata
            # Determine which page the agent maps to
            agent_route_map = {
                "DietaryAgent": "/dietary",
                "VirtualDoctorAgent": "/virtual-doctor",
                "Personal Wellbeing Counsellor": "/wellbeing",
                "DiagnosticAgent": "/diagnostic",
            }
            routed_to = resp.metadata.get("routed_to", "")
            result["navigate_to"] = agent_route_map.get(routed_to, "/ask")
            # Save to chat history
            if user:
                try:
                    append_turn(db, user.id, req.session_id, result["query"], resp.content, resp.agent_name, agent_type="ask")
                except Exception as e:
                    logger.warning("Chat history save failed: %s", e)
        except Exception as exc:
            logger.warning("Orchestrator call in voice intent failed: %s", exc)
            result["response"] = "I'm having a moment. Could you try again?"
            result["agent_name"] = "MEDORA"

    return result

