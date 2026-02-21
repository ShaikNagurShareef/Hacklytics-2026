# Hacklytics-2026

## Backend (MEDORA)

The backend is a **multi-agent healthcare API** built with **FastAPI**. It powers MEDORA with several specialist AI agents that handle virtual doctor consultations, dietary advice, wellbeing counselling, and diagnostic imaging analysis.

### How the app works (with agents)

MEDORA is an app where users chat about health, diet, or wellbeing. The backend makes that work by using **multiple AI agents**:

1. **Single entry point** — The app can send every message to **`/chat`**, which is handled by the **Orchestrator**.
2. **Orchestrator** — Decides which specialist agent should answer (e.g. “I have a headache” → Virtual Doctor; “plan my meals” → Dietary). It uses keywords first, then an LLM if the intent is unclear. It also keeps session context so follow-ups stay with the same agent.
3. **Specialist agents** — The Orchestrator calls one of the registered agents (e.g. **Virtual Doctor** for symptoms/triage/image analysis, **Dietary** for meal plans and nutrition). That agent uses the Gemini LLM and its own tools (search, BMR/TDEE, first-aid, etc.) to produce a reply.
4. **Direct agent endpoints** — The app can also call **`/virtual-doctor/chat`**, **`/dietary/chat`**, or **`/wellbeing/chat`** when the user has explicitly chosen “talk to doctor”, “diet help”, or “wellbeing support”, skipping the Orchestrator.

So the **app** is the frontend that users see; the **agents** are the backend logic that generate responses. The Orchestrator ties them together by routing each message to the right agent.

### Tech stack

- **Framework:** FastAPI with Uvicorn
- **LLM:** Google Gemini (e.g. `gemini-2.0-flash`, configurable via env)
- **Config:** `python-dotenv`; secrets and model IDs in `.env`
- **Optional:** DuckDuckGo search, ChromaDB-style memory (in-memory stub when ChromaDB is not installed)

### Project structure

```
MEDORA/backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, routes
│   ├── core/config.py       # Env-based config (GEMINI_*, TAVILY_*)
│   ├── agents/
│   │   ├── base.py          # BaseAgent, AgentResponse
│   │   ├── orchestrator.py  # Routes queries to the right agent
│   │   ├── virtual_doctor/  # Symptom collection, triage, image analysis
│   │   ├── dietary/         # Meal plans, BMR/TDEE, nutrition reports
│   │   ├── wellbeing/       # Stress/anxiety/depression detection & counselling
│   │   ├── diagnostic/      # Medical imaging analysis (X-ray, CT, MRI, etc.)
│   │   └── visualization/  # Visualization-related agent
│   ├── services/
│   │   ├── llm_client.py    # Gemini chat & vision
│   │   └── search.py        # Optional search
│   └── db/chroma.py         # In-memory / ChromaDB-style persistence
├── scripts/                 # Test and utility scripts
├── requirements.txt
└── .env                     # GEMINI_API_KEY, optional TAVILY_API_KEY
```

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | **Orchestrator** — routes to Virtual Doctor or Dietary based on query |
| `POST` | `/virtual-doctor/chat` | **Virtual Doctor** — text chat + optional `image_base64` for image analysis |
| `POST` | `/dietary/chat` | **Dietary** — meal plans, nutrition, BMR/TDEE |
| `POST` | `/wellbeing/chat` | **Wellbeing Counsellor** — mood/stress/anxiety/depression support |

Request body for chat endpoints: `{ "session_id": string, "query": string, "context": [] }`.  
Virtual Doctor also accepts `image_base64` and `image_mime_type` for image-based consultations.

### Agents

- **Orchestrator** — Keyword-first routing with LLM fallback; keeps per-session context and delegates to Virtual Doctor or Dietary.
- **Virtual Doctor** — Multi-turn symptom collection, triage, first-aid and hospital lookup, **image analysis** (e.g. skin, rashes) via Gemini Vision, optional web search; consultation state and context stored for continuity.
- **Dietary** — User preferences, restrictions, allergies; personalised meal plans and nutritional reports; BMR/TDEE and macro tools; optional web search.
- **Wellbeing Counsellor** — Detects stress/anxiety/depression from conversation and provides supportive counselling (used via `/wellbeing/chat`; not currently routed through the orchestrator).
- **Diagnostic** — Medical imaging analysis (modality detection, ACR-style reports, urgency); used via scripts or internal flows rather than a dedicated HTTP route in `main.py`.
- **Visualization** — Visualization-focused agent (see `app/agents/visualization/`).

### Run locally

From `MEDORA/backend/`:

```bash
# Create venv and install deps
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set Gemini API key in .env
echo "GEMINI_API_KEY=your_key" >> .env

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000`. Docs: `http://localhost:8000/docs`.