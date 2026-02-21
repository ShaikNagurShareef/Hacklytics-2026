"""FastAPI app. Orchestrator and other routes can be added here."""
from dotenv import load_dotenv

load_dotenv()  # Load .env from backend/ when running uvicorn from backend/

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agents.wellbeing import WellbeingCounsellorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wellbeing_agent = WellbeingCounsellorAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MEDORA", description="Multi-agent healthcare", lifespan=lifespan)


class ChatRequest(BaseModel):
    session_id: str = "default"
    query: str
    context: list = []


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
