"""
Deterministic tools / utility functions for the Diagnostic Agent.

Pure helper functions for modality detection, critical-findings
flagging, report formatting, and structured data extraction.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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


# =====================================================================
# Modality detection (keyword-based, fast path)
# =====================================================================

_MODALITY_KEYWORDS: Dict[str, List[str]] = {
    "x-ray": [
        "xray", "x-ray", "x ray", "radiograph", "plain film",
        "pa view", "ap view", "lateral view", "chest film",
    ],
    "ct": [
        "ct scan", "ct ", "computed tomography", "cat scan",
        "ct angiography", "cta", "hrct", "non-contrast ct",
    ],
    "mri": [
        "mri", "magnetic resonance", "t1 weighted", "t2 weighted",
        "flair", "dwi", "diffusion weighted", "gadolinium",
    ],
    "ultrasound": [
        "ultrasound", "sonograph", "echo", "doppler",
        "sonogram", "ultrasonography",
    ],
    "oct": [
        "oct", "optical coherence", "retinal scan",
        "rnfl", "macular scan", "ganglion cell",
    ],
    "fundoscopy": [
        "fundus", "fundoscopy", "retinal photo", "optic disc photo",
        "retinal image", "ophthalmoscop",
    ],
    "mammography": [
        "mammogra", "breast imaging", "bi-rads", "birads",
    ],
    "pet": [
        "pet scan", "pet/ct", "pet-ct", "positron emission",
        "fdg", "suv",
    ],
    "dexa": [
        "dexa", "dxa", "bone density", "bone mineral",
    ],
}

_REGION_KEYWORDS: Dict[str, List[str]] = {
    "chest": ["chest", "lung", "pulmonary", "thorax", "thoracic", "cardiac"],
    "brain": ["brain", "cranial", "intracranial", "cerebr"],
    "head": ["head", "skull", "facial", "sinus", "orbit"],
    "neck": ["neck", "cervical", "thyroid", "larynx"],
    "abdomen": ["abdomen", "abdominal", "liver", "kidney", "spleen", "pancrea"],
    "pelvis": ["pelvis", "pelvic", "bladder", "uterus", "ovary", "prostate"],
    "spine_cervical": ["c-spine", "cervical spine"],
    "spine_thoracic": ["t-spine", "thoracic spine"],
    "spine_lumbar": ["l-spine", "lumbar spine", "lower back", "lumbosacral"],
    "knee": ["knee", "patella", "tibial plateau", "meniscus"],
    "shoulder": ["shoulder", "rotator cuff", "glenohumeral", "acromi"],
    "hand_wrist": ["hand", "wrist", "carpal", "metacarpal", "finger"],
    "hip": ["hip", "femoral head", "acetabul"],
    "ankle_foot": ["ankle", "foot", "calcaneus", "metatarsal", "talus"],
    "eye": ["eye", "retina", "macula", "optic nerve", "vitreous", "fovea"],
    "breast": ["breast", "mammary", "axillary"],
}


def detect_modality_from_text(text: str) -> ImagingModality:
    """Detect imaging modality from user-provided text (query, filename, etc.)."""
    t = text.lower()
    best_modality = ImagingModality.UNKNOWN
    best_score = 0
    for modality, keywords in _MODALITY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in t)
        if score > best_score:
            best_score = score
            best_modality = ImagingModality(modality)
    return best_modality


def detect_body_region_from_text(text: str) -> BodyRegion:
    """Detect body region from user-provided text."""
    t = text.lower()
    best_region = BodyRegion.UNKNOWN
    best_score = 0
    for region, keywords in _REGION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in t)
        if score > best_score:
            best_score = score
            best_region = BodyRegion(region)
    return best_region


def parse_modality_from_llm(llm_response: str) -> Tuple[ImagingModality, BodyRegion]:
    """
    Parse the LLM's JSON response from the modality detection prompt.
    Returns (modality, body_region).
    """
    try:
        # Try direct JSON parse
        data = json.loads(llm_response.strip())
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        match = re.search(r'\{[^}]+\}', llm_response)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return ImagingModality.UNKNOWN, BodyRegion.UNKNOWN
        else:
            return ImagingModality.UNKNOWN, BodyRegion.UNKNOWN

    modality_str = data.get("modality", "unknown").lower().replace(" ", "_")
    region_str = data.get("body_region", "unknown").lower().replace(" ", "_")

    try:
        modality = ImagingModality(modality_str)
    except ValueError:
        modality = ImagingModality.UNKNOWN

    try:
        region = BodyRegion(region_str)
    except ValueError:
        region = BodyRegion.UNKNOWN

    return modality, region


# =====================================================================
# Critical findings detection
# =====================================================================

CRITICAL_FINDINGS_PATTERNS: Dict[str, List[str]] = {
    "Pneumothorax": [
        "pneumothorax", "collapsed lung", "tension pneumo",
    ],
    "Aortic dissection": [
        "aortic dissection", "intimal flap", "double lumen",
    ],
    "Pulmonary embolism": [
        "pulmonary embolism", "pe ", "filling defect.*pulmonary",
    ],
    "Intracranial hemorrhage": [
        "intracranial hemorrhage", "intracranial haemorrhage",
        "subdural hematoma", "epidural hematoma",
        "subarachnoid hemorrhage", "subarachnoid haemorrhage",
        "intraparenchymal", "midline shift",
    ],
    "Stroke / Infarction": [
        "acute infarct", "acute ischemic", "acute ischaemic",
        "restricted diffusion",
    ],
    "Fracture with displacement": [
        "displaced fracture", "comminuted fracture",
        "open fracture", "pathological fracture",
    ],
    "Retinal detachment": [
        "retinal detachment", "retinal tear",
        "rhegmatogenous detachment",
    ],
    "Papilloedema": [
        "papilloedema", "papilledema", "raised intracranial pressure",
    ],
    "Mass / Tumor (suspicious)": [
        "suspicious mass", "malignant", "metastas",
        "spiculated mass", "bi-rads 5", "bi-rads 4",
    ],
    "Free air (perforation)": [
        "free air", "pneumoperitoneum", "bowel perforation",
    ],
}


def detect_critical_findings(report_text: str) -> List[str]:
    """
    Scan the AI-generated report text for critical/urgent findings.
    Returns a list of matched critical finding categories.
    """
    text_lower = report_text.lower()
    found = []
    for category, patterns in CRITICAL_FINDINGS_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found.append(category)
                break  # one match per category is enough
    return found


def classify_urgency(critical_findings: List[str], report_text: str) -> UrgencyLevel:
    """Determine urgency level based on critical findings."""
    if not critical_findings:
        text_lower = report_text.lower()
        # Check for moderate-urgency terms
        moderate_terms = [
            "fracture", "effusion", "pneumonia", "consolidation",
            "nodule", "mass", "stenosis", "herniation",
        ]
        if any(term in text_lower for term in moderate_terms):
            return UrgencyLevel.SEMI_URGENT
        return UrgencyLevel.ROUTINE

    # If any immediately life-threatening finding
    life_threatening = {
        "Pneumothorax", "Aortic dissection", "Pulmonary embolism",
        "Intracranial hemorrhage", "Stroke / Infarction",
        "Free air (perforation)", "Retinal detachment",
    }
    if any(cf in life_threatening for cf in critical_findings):
        return UrgencyLevel.CRITICAL

    return UrgencyLevel.URGENT


# =====================================================================
# Report generation helpers
# =====================================================================

def generate_report_id() -> str:
    """Generate a unique report ID in hospital format."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"MDR-{timestamp}-{short_uuid}"


def build_patient_context_from_text(text: str) -> PatientContext:
    """
    Extract patient context from free-text query.
    Looks for age, gender, clinical indication.
    """
    age = None
    gender = None
    t = text.lower()

    # Age extraction
    age_match = re.search(r'(\d{1,3})\s*(?:year|yr|y/?o|years?\s*old)', t)
    if age_match:
        age = int(age_match.group(1))
        if age > 120:
            age = None

    # Gender extraction
    if any(g in t for g in ["male", " man ", " boy ", "gentleman"]):
        gender = "Male"
    elif any(g in t for g in ["female", " woman ", " girl ", " lady "]):
        gender = "Female"

    return PatientContext(
        age=age,
        gender=gender,
        clinical_indication=text.strip() if text.strip() else None,
    )


def format_report_header(
    report_id: str,
    study_info: StudyInfo,
    patient_context: Optional[PatientContext] = None,
) -> str:
    """Format the report header section."""
    modality_display = study_info.modality.value.upper().replace("_", " ")
    region_display = study_info.body_region.value.replace("_", " ").title()

    header = (
        f"**Report ID:** {report_id}\n"
        f"**Date:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Modality:** {modality_display}\n"
        f"**Body Region:** {region_display}\n"
    )

    if study_info.num_images > 1:
        header += f"**Images Analysed:** {study_info.num_images}\n"

    if patient_context:
        header += (
            "\n### PATIENT INFORMATION\n"
            "| Field | Value |\n"
            "|-------|-------|\n"
            f"| Age | {patient_context.age or 'Not provided'} |\n"
            f"| Gender | {patient_context.gender or 'Not provided'} |\n"
        )
        if patient_context.relevant_history:
            header += f"| Relevant History | {patient_context.relevant_history} |\n"

    return header


def format_critical_alert(critical_findings: List[str]) -> str:
    """Format the critical findings alert section."""
    if not critical_findings:
        return "### ⚠️ CRITICAL FINDINGS\nNo critical findings identified.\n"

    lines = ["### 🚨 CRITICAL FINDINGS — IMMEDIATE ATTENTION REQUIRED\n"]
    for i, finding in enumerate(critical_findings, 1):
        lines.append(f"**{i}. {finding}** — Requires immediate clinical correlation and action.\n")
    lines.append(
        "\n> 🔴 **These findings may require urgent notification of the "
        "referring physician and/or patient per ACR Practice Parameter "
        "for Communication of Diagnostic Imaging Findings.**\n"
    )
    return "\n".join(lines)
