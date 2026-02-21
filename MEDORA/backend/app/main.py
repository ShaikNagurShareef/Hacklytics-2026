"""FastAPI app. Orchestrator and other routes can be added here."""
from dotenv import load_dotenv

load_dotenv()  # Load .env from backend/ when running uvicorn from backend/

import logging
from contextlib import asynccontextmanager

from typing import Optional

from fastapi import FastAPI, HTTPException
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
