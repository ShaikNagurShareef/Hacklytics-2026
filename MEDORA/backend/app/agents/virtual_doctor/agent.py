"""
Virtual Doctor Agent – MEDORA
==============================
Communicates with users in a natural, empathetic tone to:
  • Collect symptoms and medical history via multi-turn dialogue.
  • Provide preliminary consultation and health guidance.
  • Triage severity: if serious → fetch nearest hospital / medical
    centre and suggest first-aid measures.
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
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent
from app.agents.virtual_doctor.prompts import (
    VIRTUAL_DOCTOR_SYSTEM_PROMPT,
    TRIAGE_PROMPT,
    FIRST_AID_PROMPT,
    HOSPITAL_SEARCH_PROMPT,
    build_consultation_messages,
)
from app.agents.virtual_doctor.consultation_state import (
    get_state,
    set_state,
    extract_and_merge,
    get_remaining_symptom_slots,
    format_consultation_state_block,
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
        """
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

        # ── Symptom assessment / general consultation (follow-up flow) ─
        web_context = ""
        assessed_severity = None  # used for symptom_assessment: treatment guidance + triage + metadata
        if intent == "symptom_assessment":
            web_context = await self._search_medical_info(query)
            assessed_severity = assess_severity(query)

        if intent in ("symptom_assessment", "general_consultation"):
            state = get_state(session_id)
            new_state = extract_and_merge(query, context, state)
            set_state(session_id, new_state)
            remaining = get_remaining_symptom_slots(new_state)
            consultation_block = format_consultation_state_block(new_state, remaining)
            is_follow_up = any(m.get("role") == "user" for m in context)
            severity_level = (assessed_severity or {}).get("level", "unknown") if assessed_severity else "unknown"
            ready_for_treatment = len(remaining) == 0  # use collected answers to recommend medication

            messages = build_consultation_messages(
                conversation_history=context[-10:],
                current_query=query,
                memory_snippets=memory_snippets,
                web_context=web_context,
                is_follow_up=is_follow_up,
                consultation_state_block=consultation_block,
                severity_level=severity_level,
                ready_for_treatment=ready_for_treatment,
            )
        else:
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

        # Append triage recommendation when severity is high/critical
        if intent == "symptom_assessment" and assessed_severity and assessed_severity.get("level") in ("high", "critical"):
            triage_report = format_triage_report(
                TriageResult(
                    severity=assessed_severity["level"],
                    matched_keywords=assessed_severity.get("matched", []),
                    recommendation=assessed_severity.get("recommendation", ""),
                )
            )
            response_text = f"{response_text}\n\n---\n{triage_report}"

        # Persist
        self._store_context(session_id, "user", query)
        self._store_context(session_id, "assistant", response_text)

        metadata = {
            "intent": intent,
            "session_id": session_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        if intent in ("symptom_assessment", "general_consultation"):
            state = get_state(session_id)
            remaining = get_remaining_symptom_slots(state)
            if intent == "symptom_assessment" and assessed_severity:
                metadata["assessed_severity"] = assessed_severity.get("level", "unknown")
            if remaining:
                question_templates = {
                    "description": "What symptoms are you experiencing?",
                    "onset": "When did it start?",
                    "duration": "How long does it last?",
                    "location": "Where do you feel it?",
                    "severity_self_rated": "On a scale of 1-10, how severe is it?",
                }
                metadata["remaining_questions"] = [question_templates.get(s, s) for s in remaining[:3]]
            if state.current_symptom:
                symptom = state.current_symptom
                metadata["collected_so_far"] = {
                    "description": (symptom.description or "").strip() or None,
                    "onset": (symptom.onset or "").strip() or None,
                    "duration": (symptom.duration or "").strip() or None,
                    "location": (symptom.location or "").strip() or None,
                    "severity_self_rated": symptom.severity_self_rated,
                }

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            metadata=metadata,
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
