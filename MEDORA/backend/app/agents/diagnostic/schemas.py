"""
Pydantic schemas for the Diagnostic Agent.

Report field order and section names align with the ACR Practice Parameter
for Communication of Diagnostic Imaging Findings. See acr_report_structure.py
for the canonical section list and references.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────

class ImagingModality(str, Enum):
    """Supported medical imaging modalities."""
    XRAY = "x-ray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    OCT = "oct"                   # Optical Coherence Tomography
    FUNDOSCOPY = "fundoscopy"     # Retinal fundus photography
    MAMMOGRAPHY = "mammography"
    FLUOROSCOPY = "fluoroscopy"
    PET = "pet"
    DEXA = "dexa"                 # Bone density scan
    UNKNOWN = "unknown"


class BodyRegion(str, Enum):
    """Anatomical region of the study."""
    HEAD = "head"
    BRAIN = "brain"
    NECK = "neck"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    SPINE_CERVICAL = "cervical_spine"
    SPINE_THORACIC = "thoracic_spine"
    SPINE_LUMBAR = "lumbar_spine"
    UPPER_EXTREMITY = "upper_extremity"
    LOWER_EXTREMITY = "lower_extremity"
    KNEE = "knee"
    SHOULDER = "shoulder"
    HAND_WRIST = "hand_wrist"
    HIP = "hip"
    ANKLE_FOOT = "ankle_foot"
    EYE = "eye"
    BREAST = "breast"
    CARDIAC = "cardiac"
    WHOLE_BODY = "whole_body"
    UNKNOWN = "unknown"


class UrgencyLevel(str, Enum):
    """Urgency classification for findings."""
    ROUTINE = "routine"
    SEMI_URGENT = "semi-urgent"
    URGENT = "urgent"
    CRITICAL = "critical"


class FindingSeverity(str, Enum):
    """Individual finding severity."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


# ── Patient context ──────────────────────────────────────────────────

class PatientContext(BaseModel):
    """Optional patient demographics and clinical context."""
    age: Optional[int] = None
    gender: Optional[str] = None
    clinical_indication: Optional[str] = Field(
        None,
        description="Reason for the study (e.g., 'rule out fracture', 'chronic cough')",
    )
    relevant_history: Optional[str] = Field(
        None,
        description="Relevant medical history (e.g., 'prior CABG', 'type 2 diabetes')",
    )
    prior_studies: Optional[str] = Field(
        None,
        description="Prior imaging for comparison (e.g., 'chest X-ray 2024-01-15')",
    )


# ── Study metadata ───────────────────────────────────────────────────

class StudyInfo(BaseModel):
    """Metadata about the imaging study."""
    modality: ImagingModality = ImagingModality.UNKNOWN
    body_region: BodyRegion = BodyRegion.UNKNOWN
    num_images: int = 1
    technique: Optional[str] = Field(
        None,
        description="e.g., 'PA and Lateral views', 'with IV contrast', 'T1/T2/FLAIR sequences'",
    )
    study_date: Optional[str] = None
    referring_physician: Optional[str] = None


# ── Individual finding ───────────────────────────────────────────────

class Finding(BaseModel):
    """A single observation from the imaging study."""
    location: str = Field(..., description="Anatomical location of the finding")
    observation: str = Field(..., description="What was observed")
    severity: FindingSeverity = FindingSeverity.NORMAL
    measurement: Optional[str] = Field(None, description="Size/measurement if applicable")
    is_critical: bool = False


# ── Structured report (ACR section order: acr_report_structure.ACR_SECTION_KEYS) ─

class DiagnosticReport(BaseModel):
    """
    Structured diagnostic imaging report aligned with ACR Practice Parameter
    for Communication of Diagnostic Imaging Findings (Demographics, Relevant
    Clinical Information, Body of Report). Field order follows ACR_section_keys.
    """

    # Demographics (ACR)
    report_id: str = Field(..., description="Unique report identifier")
    study_info: StudyInfo = Field(..., description="Examination type, modality, body region, date")
    patient_context: Optional[PatientContext] = None

    # Relevant Clinical Information (ACR)
    clinical_indication: str = Field(
        "Not provided",
        description="ACR: Relevant clinical information / reason for study",
    )
    comparison: str = Field(
        "No prior studies available for comparison.",
        description="ACR body: prior studies used for comparison",
    )
    technique: str = Field(
        "Standard protocol",
        description="ACR body: examination scope and technique",
    )

    # Body of report (ACR: detailed description of findings)
    findings: List[Finding] = Field(
        default_factory=list,
        description="Structured findings by anatomy (optional; narrative in findings_text)",
    )
    findings_text: str = Field(
        "",
        description="Full narrative report text in ACR section order",
    )

    # Impression and recommendations (ACR body)
    impression: str = Field(
        "",
        description="Synthesis of findings; diagnosis/differential; assessment category",
    )
    recommendations: str = Field(
        "",
        description="Follow-up imaging or management",
    )

    # Critical findings (ACR: timely communication to referring physician/patient)
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    critical_findings: List[str] = Field(
        default_factory=list,
        description="Findings requiring immediate communication per ACR Practice Parameter",
    )

    # Metadata
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
    )
    disclaimer: str = Field(
        default=(
            "This report was generated by an AI diagnostic assistant and is "
            "NOT a substitute for interpretation by a board-certified "
            "radiologist or ophthalmologist. All findings must be clinically "
            "correlated and verified by a qualified medical professional."
        ),
    )
