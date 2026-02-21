"""
Diagnostic Imaging Agent – MEDORA
===================================
Expert-level medical imaging analysis agent that:
  • Accepts medical image uploads (X-ray, CT, MRI, Ultrasound, OCT,
    Fundoscopy, Mammography, and more).
  • Auto-detects the imaging modality and body region.
  • Applies modality-specific analysis prompts (radiologist-level
    systematic reading patterns).
  • Generates ACR-standard diagnostic imaging reports.
  • Flags critical findings with urgency classification.
  • Outputs both a human-readable report AND structured JSON.
  • Supports multi-image studies and optional patient context.

**Disclaimer**: This agent provides AI-assisted preliminary observations
ONLY. Reports MUST be reviewed and verified by a board-certified
radiologist or ophthalmologist.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from app.agents.base import AgentResponse, BaseAgent
from app.agents.diagnostic.prompts import (
    DIAGNOSTIC_SYSTEM_PROMPT,
    GENERIC_ANALYSIS_PROMPT,
    MODALITY_DETECTION_PROMPT,
    MODALITY_PROMPTS,
    REPORT_GENERATION_PROMPT,
)
from app.agents.diagnostic.schemas import (
    BodyRegion,
    DiagnosticReport,
    Finding,
    FindingSeverity,
    ImagingModality,
    PatientContext,
    StudyInfo,
    UrgencyLevel,
)
from app.agents.diagnostic.tools import (
    build_patient_context_from_text,
    classify_urgency,
    detect_body_region_from_text,
    detect_critical_findings,
    detect_modality_from_text,
    format_critical_alert,
    format_report_header,
    generate_report_id,
    parse_modality_from_llm,
)

logger = logging.getLogger(__name__)


class DiagnosticAgent(BaseAgent):
    """
    Medical imaging diagnostic agent with modality-specific analysis
    and ACR-standard report generation.
    """

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return "DiagnosticAgent"

    @property
    def description(self) -> str:
        return (
            "A diagnostic imaging agent that analyses medical images "
            "(X-ray, CT, MRI, Ultrasound, OCT, Fundoscopy, Mammography) "
            "and generates standard hospital-grade radiology / ophthalmology "
            "reports with critical findings alerts, following ACR guidelines."
        )

    # ------------------------------------------------------------------
    # Service helpers (lazy-loaded)
    # ------------------------------------------------------------------
    def _get_llm_client(self):
        from app.services.llm_client import get_llm_client
        return get_llm_client()

    def _get_vision_client(self):
        from app.services import llm_client
        return llm_client

    def _get_chroma_collection(self):
        from app.db.chroma import get_chroma_client
        client = get_chroma_client()
        return client.get_or_create_collection("diagnostic_agent_memory")

    # ------------------------------------------------------------------
    # Memory (ChromaDB)
    # ------------------------------------------------------------------
    def _store_context(self, session_id: str, role: str, content: str) -> None:
        try:
            collection = self._get_chroma_collection()
            doc_id = f"{session_id}-{uuid.uuid4().hex[:8]}"
            collection.add(
                documents=[content],
                metadatas=[{"session_id": session_id, "role": role}],
                ids=[doc_id],
            )
        except Exception as exc:
            logger.warning("ChromaDB store failed (non-fatal): %s", exc)

    def _retrieve_context(
        self, session_id: str, query: str, n: int = 3,
    ) -> List[str]:
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
    # Modality detection
    # ------------------------------------------------------------------
    async def _detect_modality(
        self,
        query: str,
        image_data: Union[bytes, str],
        image_mime_type: str,
    ) -> tuple[ImagingModality, BodyRegion]:
        """
        Two-layer modality detection:
        1. Keyword-based from user query (fast).
        2. LLM Vision-based from the image itself (fallback).
        """
        # Layer 1: keywords
        modality = detect_modality_from_text(query)
        body_region = detect_body_region_from_text(query)

        if modality != ImagingModality.UNKNOWN and body_region != BodyRegion.UNKNOWN:
            logger.info("Modality detected via keywords: %s / %s", modality, body_region)
            return modality, body_region

        # Layer 2: ask Gemini Vision to identify the modality
        try:
            vision = self._get_vision_client()
            llm_response = await vision.vision_chat(
                prompt=MODALITY_DETECTION_PROMPT,
                image_data=image_data,
                mime_type=image_mime_type,
            )
            llm_modality, llm_region = parse_modality_from_llm(llm_response)

            if modality == ImagingModality.UNKNOWN:
                modality = llm_modality
            if body_region == BodyRegion.UNKNOWN:
                body_region = llm_region

            logger.info(
                "Modality detected via LLM Vision: %s / %s", modality, body_region,
            )
        except Exception as exc:
            logger.warning("LLM modality detection failed: %s", exc)

        return modality, body_region

    # ------------------------------------------------------------------
    # Core image analysis
    # ------------------------------------------------------------------
    async def _analyse_image(
        self,
        image_data: Union[bytes, str],
        image_mime_type: str,
        modality: ImagingModality,
        body_region: BodyRegion,
        patient_context: Optional[PatientContext],
        user_query: str,
    ) -> str:
        """
        Send the image to Gemini Vision with a modality-specific analysis
        prompt and generate a detailed analysis.
        """
        # Select the modality-specific prompt
        modality_prompt = MODALITY_PROMPTS.get(
            modality.value, GENERIC_ANALYSIS_PROMPT
        )

        # Build the full prompt
        prompt_parts = [
            DIAGNOSTIC_SYSTEM_PROMPT,
            f"\n**Imaging Modality:** {modality.value.upper()}",
            f"**Body Region:** {body_region.value.replace('_', ' ').title()}",
        ]

        if patient_context:
            ctx_lines = []
            if patient_context.age:
                ctx_lines.append(f"Age: {patient_context.age}")
            if patient_context.gender:
                ctx_lines.append(f"Gender: {patient_context.gender}")
            if patient_context.clinical_indication:
                ctx_lines.append(
                    f"Clinical indication: {patient_context.clinical_indication}"
                )
            if patient_context.relevant_history:
                ctx_lines.append(
                    f"Relevant history: {patient_context.relevant_history}"
                )
            if patient_context.prior_studies:
                ctx_lines.append(
                    f"Prior studies: {patient_context.prior_studies}"
                )
            if ctx_lines:
                prompt_parts.append(
                    "\n**Patient Context:**\n" + "\n".join(ctx_lines)
                )

        prompt_parts.append(f"\n{modality_prompt}")

        if user_query.strip():
            prompt_parts.append(
                f"\n**Patient's message:** {user_query}"
            )

        full_prompt = "\n".join(prompt_parts)

        # Call Gemini Vision
        vision = self._get_vision_client()
        analysis = await vision.vision_chat(
            prompt=full_prompt,
            image_data=image_data,
            mime_type=image_mime_type,
        )
        return analysis

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------
    async def _generate_report(
        self,
        analysis_text: str,
        modality: ImagingModality,
        body_region: BodyRegion,
        patient_context: Optional[PatientContext],
        user_query: str,
    ) -> str:
        """
        Take the raw analysis and reformat it into a standard
        hospital-grade diagnostic report using the LLM.
        """
        report_id = generate_report_id()

        prompt = (
            f"{REPORT_GENERATION_PROMPT}\n\n"
            f"**Report ID:** {report_id}\n"
            f"**Modality:** {modality.value.upper()}\n"
            f"**Body Region:** {body_region.value.replace('_', ' ').title()}\n"
        )

        if patient_context:
            if patient_context.age:
                prompt += f"**Patient Age:** {patient_context.age}\n"
            if patient_context.gender:
                prompt += f"**Patient Gender:** {patient_context.gender}\n"
            if patient_context.clinical_indication:
                prompt += (
                    f"**Clinical Indication:** "
                    f"{patient_context.clinical_indication}\n"
                )

        prompt += (
            f"\n--- RAW AI ANALYSIS ---\n{analysis_text}\n--- END ---\n\n"
            "Now format the above analysis into the standard report template."
        )

        from app.services.llm_client import chat
        report_text = await chat(
            [
                {"role": "system", "content": DIAGNOSTIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return report_text

    # ------------------------------------------------------------------
    # Build structured report object
    # ------------------------------------------------------------------
    def _build_structured_report(
        self,
        report_text: str,
        modality: ImagingModality,
        body_region: BodyRegion,
        patient_context: Optional[PatientContext],
        num_images: int,
    ) -> DiagnosticReport:
        """Build the Pydantic DiagnosticReport from the generated text."""
        report_id = generate_report_id()
        critical = detect_critical_findings(report_text)
        urgency = classify_urgency(critical, report_text)

        study_info = StudyInfo(
            modality=modality,
            body_region=body_region,
            num_images=num_images,
            study_date=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        )

        return DiagnosticReport(
            report_id=report_id,
            study_info=study_info,
            patient_context=patient_context,
            findings_text=report_text,
            urgency=urgency,
            critical_findings=critical,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Core invocation
    # ------------------------------------------------------------------
    async def invoke(
        self,
        session_id: str,
        query: str,
        context: List[Dict],
        image_data: Optional[Union[bytes, str, List[Union[bytes, str]]]] = None,
        image_mime_type: str = "image/jpeg",
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Main entry-point called by the Orchestrator.

        Parameters
        ----------
        session_id : str
            Unique session / conversation identifier.
        query : str
            The user's message (may include clinical indication, patient
            details, or questions about the image).
        context : List[Dict]
            Recent conversation history.
        image_data : bytes | str | list | None
            Single image (bytes/base64) or list of images for multi-image
            studies. If None, the agent will ask the user to upload.
        image_mime_type : str
            MIME type of the uploaded image(s).
        patient_context : dict | None
            Optional patient demographics and clinical context.
        """
        # ── No image provided — prompt user to upload ────────────────
        if image_data is None:
            return self._prompt_for_image(session_id, query)

        # ── Parse patient context ────────────────────────────────────
        ctx = None
        if patient_context:
            ctx = PatientContext(**patient_context)
        elif query.strip():
            ctx = build_patient_context_from_text(query)

        # ── Normalise image_data to a list ───────────────────────────
        if isinstance(image_data, list):
            images = image_data
        else:
            images = [image_data]

        num_images = len(images)
        logger.info(
            "[DiagnosticAgent] session=%s  images=%d  query=%s",
            session_id, num_images, query[:80],
        )

        # ── Step 1: Detect modality (using first image) ──────────────
        modality, body_region = await self._detect_modality(
            query, images[0], image_mime_type,
        )
        logger.info(
            "Detected: modality=%s  region=%s", modality.value, body_region.value,
        )

        # ── Step 2: Analyse each image ───────────────────────────────
        all_analyses = []
        for i, img in enumerate(images):
            label = f"Image {i + 1}/{num_images}" if num_images > 1 else ""
            try:
                analysis = await self._analyse_image(
                    image_data=img,
                    image_mime_type=image_mime_type,
                    modality=modality,
                    body_region=body_region,
                    patient_context=ctx,
                    user_query=query,
                )
                if label:
                    analysis = f"### {label}\n{analysis}"
                all_analyses.append(analysis)
            except Exception as exc:
                logger.error("Image analysis failed for image %d: %s", i + 1, exc)
                all_analyses.append(
                    f"### {label}\n⚠️ Analysis failed for this image: {exc}"
                )

        combined_analysis = "\n\n---\n\n".join(all_analyses)

        # ── Step 3: Generate structured report ───────────────────────
        try:
            report_text = await self._generate_report(
                analysis_text=combined_analysis,
                modality=modality,
                body_region=body_region,
                patient_context=ctx,
                user_query=query,
            )
        except Exception as exc:
            logger.error("Report generation failed: %s", exc)
            report_text = (
                "## DIAGNOSTIC IMAGING REPORT\n\n"
                "⚠️ Report formatting failed. Raw analysis below:\n\n"
                f"{combined_analysis}\n\n"
                "> 📋 *This report was generated by MEDORA Diagnostic AI. "
                "Please consult a qualified medical professional.*"
            )

        # ── Step 4: Critical findings detection ──────────────────────
        critical_findings = detect_critical_findings(report_text)
        urgency = classify_urgency(critical_findings, report_text)

        if critical_findings:
            alert = format_critical_alert(critical_findings)
            report_text += f"\n\n{alert}"

        # ── Step 5: Build structured data ────────────────────────────
        structured = self._build_structured_report(
            report_text=report_text,
            modality=modality,
            body_region=body_region,
            patient_context=ctx,
            num_images=num_images,
        )

        # ── Persist to memory ────────────────────────────────────────
        self._store_context(
            session_id, "user",
            f"[Diagnostic image uploaded: {modality.value} / {body_region.value}] {query}",
        )
        self._store_context(session_id, "assistant", report_text)

        return AgentResponse(
            agent_name=self.name,
            content=report_text,
            metadata={
                "intent": "diagnostic_analysis",
                "modality": modality.value,
                "body_region": body_region.value,
                "num_images": num_images,
                "urgency": urgency.value,
                "critical_findings": critical_findings,
                "structured_report": structured.model_dump(),
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    # ------------------------------------------------------------------
    # No-image fallback
    # ------------------------------------------------------------------
    def _prompt_for_image(self, session_id: str, query: str) -> AgentResponse:
        """Return a helpful prompt asking the user to upload an image."""
        content = (
            "## 🏥 MEDORA Diagnostic Imaging\n\n"
            "I'm ready to analyse your medical image. To generate a "
            "diagnostic report, I'll need:\n\n"
            "### Required\n"
            "📎 **Upload your medical image** — I support:\n"
            "- 🦴 **X-ray** (chest, extremity, spine, etc.)\n"
            "- 🧠 **CT scan** (brain, chest, abdomen, etc.)\n"
            "- 🧲 **MRI** (brain, spine, joint, etc.)\n"
            "- 📡 **Ultrasound** (abdominal, cardiac, vascular, etc.)\n"
            "- 👁️ **OCT** (retinal/macular scans)\n"
            "- 👁️ **Fundus photography** (retinal images)\n"
            "- 🎀 **Mammography** (breast imaging)\n\n"
            "### Optional (improves report quality)\n"
            "Include any of the following with your upload:\n"
            "- **Patient age and gender**\n"
            "- **Clinical indication** (why the scan was ordered)\n"
            "- **Relevant medical history**\n"
            "- **Prior imaging** for comparison\n\n"
            "### Example\n"
            "*\"Here's my chest X-ray. 45-year-old male with persistent "
            "cough for 3 weeks. History of smoking.\"*\n\n"
            "> 📋 *I'll generate a standard hospital-grade diagnostic "
            "report following ACR guidelines.*"
        )

        return AgentResponse(
            agent_name=self.name,
            content=content,
            metadata={
                "intent": "awaiting_image",
                "session_id": session_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
        )
