"""
Pydantic schemas for the Virtual Doctor Agent.
"""

from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------
class Severity(str, Enum):
    LOW = "low"            # self-care / monitor at home
    MODERATE = "moderate"  # see doctor within 24-48 hrs
    HIGH = "high"          # see doctor today / visit urgent care
    CRITICAL = "critical"  # call 911 / go to ER immediately


class SymptomCategory(str, Enum):
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    MUSCULOSKELETAL = "musculoskeletal"
    DERMATOLOGICAL = "dermatological"
    PSYCHOLOGICAL = "psychological"
    GENERAL = "general"
    OTHER = "other"


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------
class SymptomEntry(BaseModel):
    """A single symptom reported by the patient."""
    description: str
    onset: Optional[str] = None           # e.g. "2 days ago"
    duration: Optional[str] = None        # e.g. "intermittent for 3 hours"
    severity_self_rated: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Patient's self-rated severity 1-10"
    )
    location: Optional[str] = None        # body area
    category: SymptomCategory = SymptomCategory.GENERAL


class PatientProfile(BaseModel):
    """Collected patient information during consultation."""
    age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    known_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    symptoms: List[SymptomEntry] = Field(default_factory=list)
    location: Optional[str] = None  # for hospital search


class TriageResult(BaseModel):
    """Output of deterministic severity assessment."""
    severity: str
    matched_keywords: List[str] = Field(default_factory=list)
    recommendation: str
    requires_emergency: bool = False


class HospitalInfo(BaseModel):
    """A medical facility returned from search."""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None  # "hospital", "urgent_care", "clinic"
    distance: Optional[str] = None
    link: Optional[str] = None


class ConsultationSummary(BaseModel):
    """End-of-session summary of the virtual consultation."""
    session_id: str
    patient_profile: PatientProfile
    triage_result: Optional[TriageResult] = None
    preliminary_assessment: str
    recommendations: List[str] = Field(default_factory=list)
    follow_up_needed: bool = False
    nearby_facilities: List[HospitalInfo] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
