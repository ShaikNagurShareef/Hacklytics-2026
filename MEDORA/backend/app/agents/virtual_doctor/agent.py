"""
Virtual Doctor Agent – MEDORA
==============================
Communicates with users in a natural, empathetic tone to:
  • Collect symptoms and medical history via multi-turn dialogue.
  • Provide preliminary consultation and health guidance.
  • Triage severity: if serious → fetch nearest hospital / medical
    centre and suggest first-aid measures.
  • **Analyse uploaded medical images** (skin conditions, injuries,
    rashes, etc.) using Gemini Vision.
  • Leverage web search (DuckDuckGo) for up-to-date medical info &
    nearby facility lookup.
  • Persist conversation context in ChromaDB for continuity.

**Disclaimer**: This agent does NOT replace professional medical advice.
It always recommends consulting a licensed physician for serious cases.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from app.agents.base import AgentResponse, BaseAgent
from app.agents.virtual_doctor.prompts import (
    VIRTUAL_DOCTOR_SYSTEM_PROMPT,
    TRIAGE_PROMPT,
    FIRST_AID_PROMPT,
    HOSPITAL_SEARCH_PROMPT,
    IMAGE_ANALYSIS_PROMPT,
)
from app.agents.virtual_doctor.tools import (
    assess_severity,
    get_first_aid_instructions,
    format_triage_report,
    SEVERITY_LEVELS,
)
from app.agents.virtual_doctor.schemas import (
    SymptomEntry,
    TriageResult,
    PatientProfile,
    ConsultationSummary,
)

logger = logging.getLogger(__name__)


class VirtualDoctorAgent(BaseAgent):
    """Natural-language virtual doctor for preliminary consultations."""

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return "VirtualDoctorAgent"

    @property
    def description(self) -> str:
        return (
            "A virtual doctor agent that communicates naturally to "
            "collect symptoms, provide preliminary consultation, "
            "triage severity, suggest first-aid for emergencies, and "
            "fetch nearest hospital / medical centre details when the "
            "case is serious."
        )

    # ------------------------------------------------------------------
    # Service helpers (lazy imports)
    # ------------------------------------------------------------------
    def _get_llm_client(self):
        from app.services.llm_client import get_llm_client
        return get_llm_client()

    def _get_search_client(self):
        from app.services.search import get_search_client
        return get_search_client()

    def _get_chroma_collection(self):
        from app.db.chroma import get_chroma_client
        client = get_chroma_client()
        return client.get_or_create_collection("virtual_doctor_memory")

    # ------------------------------------------------------------------
    # Context helpers (ChromaDB)
    # ------------------------------------------------------------------
    def _store_context(self, session_id: str, role: str, content: str) -> None:
        try:
            collection = self._get_chroma_collection()
            doc_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
            collection.add(
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }],
                ids=[doc_id],
            )
        except Exception as exc:
            logger.warning("ChromaDB store failed (non-fatal): %s", exc)

    def _retrieve_context(self, session_id: str, query: str, n: int = 5) -> List[str]:
        try:
            collection = self._get_chroma_collection()
            results = collection.query(
                query_texts=[query],
                n_results=n,
                where={"session_id": session_id},
            )
            return results.get("documents", [[]])[0]
        except Exception as exc:
            logger.warning("ChromaDB retrieval failed (non-fatal): %s", exc)
            return []

    # ------------------------------------------------------------------
    # Web search helpers
    # ------------------------------------------------------------------
    async def _search_medical_info(self, query: str) -> str:
        """Search for medical / symptom information from the web."""
        try:
            search = self._get_search_client()
            results = await search.search(f"medical information: {query}")
            if results:
                snippets = [r.get("snippet", r.get("body", "")) for r in results[:3]]
                return "\n".join(snippets)
        except Exception as exc:
            logger.warning("Medical search failed (non-fatal): %s", exc)
        return ""

    async def _search_nearby_hospitals(self, location: str) -> str:
        """Search for nearby hospitals / medical centres given a location."""
        try:
            search = self._get_search_client()
            results = await search.search(
                f"nearest hospital emergency medical centre near {location}"
            )
            if results:
                entries = []
                for r in results[:5]:
                    title = r.get("title", "")
                    snippet = r.get("snippet", r.get("body", ""))
                    link = r.get("link", r.get("href", ""))
                    entries.append(f"**{title}**\n{snippet}\n🔗 {link}")
                return "\n\n".join(entries)
        except Exception as exc:
            logger.warning("Hospital search failed (non-fatal): %s", exc)
        return ""

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------
    _EMERGENCY_KEYWORDS = [
        "chest pain", "heart attack", "stroke", "can't breathe",
        "cannot breathe", "difficulty breathing", "severe bleeding",
        "unconscious", "seizure", "choking", "anaphylaxis",
        "severe allergic", "poisoning", "overdose", "suicidal",
        "suicide", "not breathing", "collapsed",
    ]

    _HOSPITAL_KEYWORDS = [
        "hospital", "nearest hospital", "emergency room", "er near",
        "clinic near", "medical centre", "urgent care", "find doctor",
        "nearest doctor",
    ]

    _FIRST_AID_KEYWORDS = [
        "first aid", "what should i do", "emergency help",
        "how to stop bleeding", "cpr", "burns", "fracture",
        "broken bone", "bite", "sting",
    ]

    def _detect_intent(self, query: str) -> str:
        q = query.lower()
        if any(kw in q for kw in self._EMERGENCY_KEYWORDS):
            return "emergency"
        if any(kw in q for kw in self._HOSPITAL_KEYWORDS):
            return "hospital_search"
        if any(kw in q for kw in self._FIRST_AID_KEYWORDS):
            return "first_aid"
        if any(kw in q for kw in [
            "symptom", "symptoms", "feeling", "pain", "ache", "fever",
            "cough", "headache", "dizzy", "nausea", "vomit", "rash",
            "swelling", "fatigue", "tired", "sore",
        ]):
            return "symptom_assessment"
        return "general_consultation"

    # ------------------------------------------------------------------
    # Core invocation
    # ------------------------------------------------------------------
    async def invoke(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        image_data: Optional[Union[bytes, str]] = None,
        image_mime_type: str = "image/jpeg",
    ) -> AgentResponse:
        """
        Main entry-point called by the Orchestrator.

        Parameters
        ----------
        session_id : str
            Unique session / conversation identifier.
        query : str
            The user's latest message.
        context : List[Dict]
            Recent conversation history (list of {role, content} dicts).
        image_data : bytes | str | None
            Raw image bytes or base64-encoded string. When provided,
            the agent uses Gemini Vision to analyse the image.
        image_mime_type : str
            MIME type of the uploaded image (default: image/jpeg).
        """
        # ── Image analysis path ──────────────────────────────────────
        if image_data is not None:
            return await self._handle_image_analysis(
                session_id, query, context, image_data, image_mime_type,
            )

        intent = self._detect_intent(query)
        logger.info("[VirtualDoctorAgent] session=%s  intent=%s", session_id, intent)

        # Retrieve long-term memory
        memory_snippets = self._retrieve_context(session_id, query)

        # ── Emergency fast-path ──────────────────────────────────────
        if intent == "emergency":
            return await self._handle_emergency(session_id, query, context, memory_snippets)

        # ── Hospital search ──────────────────────────────────────────
        if intent == "hospital_search":
            return await self._handle_hospital_search(session_id, query, context, memory_snippets)

        # ── First-aid guidance ───────────────────────────────────────
        if intent == "first_aid":
            return await self._handle_first_aid(session_id, query, context, memory_snippets)

        # ── Symptom assessment ───────────────────────────────────────
        web_context = ""
        if intent == "symptom_assessment":
            web_context = await self._search_medical_info(query)

        # ── General consultation / symptom assessment ────────────────
        system_prompt = self._build_system_prompt(intent)
        messages = self._build_messages(
            system_prompt=system_prompt,
            context=context,
            memory_snippets=memory_snippets,
            web_context=web_context,
            user_query=query,
        )

        llm = self._get_llm_client()
        response_text = await llm.generate(messages)

        # Run deterministic severity assessment alongside LLM output
        if intent == "symptom_assessment":
            severity = assess_severity(query)
            if severity["level"] in ("high", "critical"):
                triage_report = format_triage_report(
                    TriageResult(
                        severity=severity["level"],
                        matched_keywords=severity["matched"],
                        recommendation=severity["recommendation"],
                    )
                )
                response_text = f"{response_text}\n\n---\n{triage_report}"

        # Persist
        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": intent,
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    # ------------------------------------------------------------------
    # Image analysis handler
    # ------------------------------------------------------------------
    async def _handle_image_analysis(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        image_data: Union[bytes, str],
        image_mime_type: str,
    ) -> AgentResponse:
        """
        Analyse an uploaded medical image using Gemini Vision.

        Combines the image analysis prompt with the user's text query
        (if any) and sends both to the multimodal Gemini model.
        """
        logger.info(
            "[VirtualDoctorAgent] session=%s  intent=image_analysis",
            session_id,
        )

        # Build the vision prompt
        user_context = query.strip() if query.strip() else "Please analyse this medical image."
        vision_prompt = (
            f"{IMAGE_ANALYSIS_PROMPT}\n\n"
            f"Patient's message: {user_context}"
        )

        # If there's prior conversation context, include a summary
        if context:
            recent = context[-6:]  # last 3 turns
            history_block = "\n".join(
                f"{t.get('role', 'user').title()}: {t.get('content', '')}"
                for t in recent
            )
            vision_prompt += (
                f"\n\nPrior conversation context:\n{history_block}"
            )

        # Call Gemini Vision
        try:
            from app.services.llm_client import vision_chat
            response_text = await vision_chat(
                prompt=vision_prompt,
                image_data=image_data,
                mime_type=image_mime_type,
            )
        except Exception as exc:
            logger.error("Vision analysis failed: %s", exc)
            response_text = (
                "I'm sorry, I wasn't able to analyse the image at this time. "
                "This could be due to image quality or a temporary issue.\n\n"
                "Could you please:\n"
                "1. **Describe what you see** in the image in text\n"
                "2. **Re-upload** the image (ensure it's well-lit and in focus)\n\n"
                "I'll do my best to help based on your description."
            )

        # Persist
        self._store_context(session_id, "user", f"[Image uploaded] {query}")
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": "image_analysis",
                "session_id": session_id,
                "image_provided": True,
                "image_mime_type": image_mime_type,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    # ------------------------------------------------------------------
    # Specialised handlers
    # ------------------------------------------------------------------
    async def _handle_emergency(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        memory_snippets: List[str],
    ) -> AgentResponse:
        """Handle potential emergencies with first-aid + hospital search."""
        # 1. Deterministic first-aid
        first_aid = get_first_aid_instructions(query)

        # 2. Ask LLM for calming, guided response
        messages = self._build_messages(
            system_prompt=TRIAGE_PROMPT,
            context=context,
            memory_snippets=memory_snippets,
            web_context="",
            user_query=query,
        )
        llm = self._get_llm_client()
        llm_response = await llm.generate(messages)

        # 3. Search for hospitals (best-effort)
        hospital_info = await self._search_nearby_hospitals("user location")

        # Compose final response
        parts = [
            "## 🚨 Emergency Detected\n",
            llm_response,
        ]
        if first_aid:
            parts.append(f"\n\n### 🩹 Immediate First-Aid\n{first_aid}")
        if hospital_info:
            parts.append(f"\n\n### 🏥 Nearby Medical Facilities\n{hospital_info}")
        parts.append(
            "\n\n> ⚠️ **This is not a substitute for professional medical help. "
            "Please call emergency services (911 / local equivalent) immediately.**"
        )

        response_text = "\n".join(parts)

        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": "emergency",
                "severity": "critical",
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    async def _handle_hospital_search(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        memory_snippets: List[str],
    ) -> AgentResponse:
        """Search for nearest hospitals / clinics."""
        # Extract location from query (LLM will help refine)
        hospital_info = await self._search_nearby_hospitals(query)

        messages = self._build_messages(
            system_prompt=HOSPITAL_SEARCH_PROMPT,
            context=context,
            memory_snippets=memory_snippets,
            web_context=hospital_info,
            user_query=query,
        )
        llm = self._get_llm_client()
        response_text = await llm.generate(messages)

        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": "hospital_search",
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    async def _handle_first_aid(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        memory_snippets: List[str],
    ) -> AgentResponse:
        """Provide first-aid instructions."""
        first_aid = get_first_aid_instructions(query)

        messages = self._build_messages(
            system_prompt=FIRST_AID_PROMPT,
            context=context,
            memory_snippets=memory_snippets,
            web_context=first_aid,
            user_query=query,
        )
        llm = self._get_llm_client()
        response_text = await llm.generate(messages)

        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata={
                "intent": "first_aid",
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def _build_system_prompt(self, intent: str) -> str:
        if intent == "emergency":
            return TRIAGE_PROMPT
        if intent == "first_aid":
            return FIRST_AID_PROMPT
        if intent == "hospital_search":
            return HOSPITAL_SEARCH_PROMPT
        return VIRTUAL_DOCTOR_SYSTEM_PROMPT

    def _build_messages(
        self,
        system_prompt: str,
        context: List[Dict],
        memory_snippets: List[str],
        web_context: str,
        user_query: str,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        if memory_snippets:
            mem_block = "\n---\n".join(memory_snippets)
            messages.append({
                "role": "system",
                "content": (
                    "[Long-term memory – prior interactions with this patient]\n"
                    f"{mem_block}"
                ),
            })

        if web_context:
            messages.append({
                "role": "system",
                "content": (
                    "[Web search results – reference information]\n"
                    f"{web_context}"
                ),
            })

        for turn in context[-10:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })

        messages.append({"role": "user", "content": user_query})
        return messages
