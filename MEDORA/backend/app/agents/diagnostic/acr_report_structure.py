"""
ACR-aligned diagnostic imaging report structure.

This module is the single source of truth for report layout and section order.
It follows the ACR Practice Parameter for Communication of Diagnostic Imaging
Findings and standard radiology report conventions (RSNA, RadiologyInfo.org).

References:
- ACR Practice Parameter for Communication of Diagnostic Imaging Findings
  (final report must be prepared and archived by interpreting physician;
   suggested components: Demographics, Relevant Clinical Information, Body.)
- Standard report body: Indication → Comparison → Technique → Findings
  → Impression → Recommendations; critical findings communicated per ACR.
"""

from __future__ import annotations

from typing import List, Tuple

# -----------------------------------------------------------------------------
# ACR report components (ordered)
# -----------------------------------------------------------------------------
# Per ACR: (1) Demographics, (2) Relevant Clinical Information, (3) Body.
# Body is expanded per standard practice into the sections below.

# Section key, display title, description for prompts/docs
ACR_SECTIONS: List[Tuple[str, str, str]] = [
    # --- Demographics (ACR required) ---
    ("demographics", "DEMOGRAPHICS", "Facility/report ID, exam type, date/time, patient ID, optional DOB/gender"),
    # --- Relevant Clinical Information (ACR required) ---
    ("clinical_indication", "RELEVANT CLINICAL INFORMATION", "Reason for study; background pertinent to the examination"),
    ("comparison", "COMPARISON", "Prior studies used for comparison, or 'None'"),
    ("technique", "TECHNIQUE", "Examination scope and technique (views, sequences, contrast)"),
    # --- Body of report (ACR: detailed description of findings) ---
    ("findings", "FINDINGS", "Detailed description of imaging findings by anatomy"),
    ("impression", "IMPRESSION", "Synthesis of findings; diagnosis/differential; assessment category where applicable"),
    ("recommendations", "RECOMMENDATIONS", "Follow-up imaging or management"),
    ("critical_findings", "CRITICAL FINDINGS", "If any: list and state need for immediate communication per ACR"),
]

# Ordered keys only (for iteration / validation)
ACR_SECTION_KEYS: List[str] = [s[0] for s in ACR_SECTIONS]

# One-page report: section headers as they must appear in the generated text
# (so parsing or PDF can rely on consistent headings)
ACR_SECTION_HEADERS: List[str] = [s[1] for s in ACR_SECTIONS]

# Footer / metadata (not a numbered ACR "section" but required on report)
REPORT_METADATA_KEYS = ("report_id", "exam_date", "modality", "body_region", "urgency", "disclaimer")

# ACR Practice Parameter: critical findings require timely communication to
# referring physician and/or patient.
ACR_CRITICAL_FINDINGS_DISCLAIMER = (
    "Recommend immediate communication to referring physician and/or patient "
    "per ACR Practice Parameter for Communication of Diagnostic Imaging Findings."
)

# Standard disclaimer for AI-generated reports (not part of ACR text)
AI_REPORT_DISCLAIMER = (
    "AI-generated preliminary report. Not a substitute for interpretation by a "
    "board-certified radiologist or ophthalmologist. Verify and correlate clinically."
)
