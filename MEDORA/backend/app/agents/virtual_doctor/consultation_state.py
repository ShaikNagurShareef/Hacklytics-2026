"""
Per-session consultation state for Virtual Doctor follow-up flow.

In-memory store keyed by session_id; helpers to compute remaining symptom slots
and merge extracted info from user messages (rule-based extraction).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.agents.virtual_doctor.schemas import (
    ConsultationState,
    PatientProfile,
    SymptomEntry,
    SymptomCategory,
)

# Slots we collect for the current symptom (order can guide question priority)
SYMPTOM_SLOTS = ["description", "onset", "duration", "location", "severity_self_rated"]

# In-memory: session_id -> ConsultationState
_store: Dict[str, ConsultationState] = {}


def get_state(session_id: str) -> ConsultationState:
    """Get or create consultation state for the session."""
    if session_id not in _store:
        _store[session_id] = ConsultationState()
    return _store[session_id]


def set_state(session_id: str, state: ConsultationState) -> None:
    """Persist consultation state for the session."""
    _store[session_id] = state


def get_remaining_symptom_slots(state: ConsultationState) -> List[str]:
    """Return names of symptom slots not yet set (for current_symptom)."""
    remaining: List[str] = []
    symptom = state.current_symptom
    if symptom is None:
        return list(SYMPTOM_SLOTS)
    if not (symptom.description or "").strip():
        remaining.append("description")
    if not (symptom.onset or "").strip():
        remaining.append("onset")
    if not (symptom.duration or "").strip():
        remaining.append("duration")
    if not (symptom.location or "").strip():
        remaining.append("location")
    if symptom.severity_self_rated is None:
        remaining.append("severity_self_rated")
    return remaining


def _extract_severity(text: str) -> Optional[int]:
    """Try to find a 1-10 severity in the text."""
    # "7/10", "around 7", "severity 6", "pain level 8"
    for m in re.finditer(r"(?:severity|pain|level|scale|rate[d]?)\s*(?:of|is)?\s*(\d{1,2})", text, re.I):
        v = int(m.group(1))
        if 1 <= v <= 10:
            return v
    for m in re.finditer(r"(\d{1,2})\s*/\s*10", text):
        v = int(m.group(1))
        if 1 <= v <= 10:
            return v
    for m in re.finditer(r"\b(\d)\s*out\s*of\s*10", text, re.I):
        v = int(m.group(1))
        if 1 <= v <= 10:
            return v
    return None


def _extract_onset(text: str) -> Optional[str]:
    """Heuristic: phrases like 'since yesterday', 'started 2 days ago', 'for the last week'."""
    text_lower = text.lower()
    patterns = [
        r"(?:since|started?|began)\s+(?:yesterday|today|last\s+night)",
        r"(?:for\s+)?(?:the\s+)?last\s+\d+\s+(?:hours?|days?|weeks?)",
        r"\d+\s+(?:hours?|days?|weeks?)\s+ago",
        r"(?:about|around)\s+\d+\s+(?:hours?|days?|weeks?)",
        r"since\s+(?:this\s+morning|monday|last\s+\w+)",
    ]
    for pat in patterns:
        m = re.search(pat, text_lower, re.I)
        if m:
            return m.group(0).strip()
    return None


def _extract_duration(text: str) -> Optional[str]:
    """E.g. 'lasts a few hours', 'comes and goes', 'constant', 'intermittent'."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["constant", "all day", "all the time", "nonstop"]):
        return "constant"
    if any(w in text_lower for w in ["comes and goes", "intermittent", "on and off", "sometimes"]):
        return "intermittent"
    m = re.search(r"(?:lasts?|for)\s+(?:about\s+)?(\d+\s*(?:minutes?|hours?|days?))", text_lower)
    if m:
        return m.group(0).strip()
    return None


def _extract_location(text: str) -> Optional[str]:
    """Simple: look for body-part-like phrases (temples, forehead, chest, etc.)."""
    body_terms = [
        "head", "forehead", "temples", "back of head", "sinuses",
        "chest", "stomach", "abdomen", "throat", "neck", "back",
        "left side", "right side", "arm", "leg", "joint", "ear", "eye",
    ]
    text_lower = text.lower()
    for term in body_terms:
        if term in text_lower:
            return term
    return None


def extract_and_merge(
    query: str,
    context: List[Dict[str, Any]],
    state: ConsultationState,
) -> ConsultationState:
    """
    Extract symptom/patient info from the user's message and merge into state.
    Only fills fields that are currently empty. Returns a new state (caller should set_state).
    """
    import copy
    text = (query or "").strip()
    if not text:
        return state

    new_state = copy.deepcopy(state)
    symptom = new_state.current_symptom

    # First message: treat whole query as symptom description if we have no symptom yet
    if symptom is None:
        new_state.current_symptom = SymptomEntry(
            description=query.strip() or "general concern",
            category=SymptomCategory.GENERAL,
        )
        symptom = new_state.current_symptom

    # Merge extracted values only when current value is empty
    onset = _extract_onset(text)
    if onset and not (symptom.onset or "").strip():
        symptom.onset = onset
    duration = _extract_duration(text)
    if duration and not (symptom.duration or "").strip():
        symptom.duration = duration
    location = _extract_location(text)
    if location and not (symptom.location or "").strip():
        symptom.location = location
    severity = _extract_severity(text)
    if severity is not None and symptom.severity_self_rated is None:
        symptom.severity_self_rated = severity

    # Optional: after 2+ slots beyond description, mark ready for assessment
    remaining = get_remaining_symptom_slots(new_state)
    if len(remaining) <= 2 and "description" not in remaining:
        new_state.phase = "ready_for_assessment"

    return new_state


def format_consultation_state_block(state: ConsultationState, remaining_slots: List[str]) -> str:
    """Build the [Consultation state] block for the system prompt."""
    lines = ["[Consultation state]"]
    symptom = state.current_symptom
    if symptom:
        collected = []
        if (symptom.description or "").strip():
            collected.append(f'description="{symptom.description[:80]}..."' if len(symptom.description or "") > 80 else f'description="{symptom.description}"')
        if (symptom.onset or "").strip():
            collected.append(f'onset="{symptom.onset}"')
        if (symptom.duration or "").strip():
            collected.append(f'duration="{symptom.duration}"')
        if (symptom.location or "").strip():
            collected.append(f'location="{symptom.location}"')
        if symptom.severity_self_rated is not None:
            collected.append(f'severity_self_rated={symptom.severity_self_rated}')
        lines.append("Collected so far: " + (", ".join(collected) if collected else "none yet"))
    else:
        lines.append("Collected so far: none yet")
    if remaining_slots:
        human_slots = {
            "description": "what the symptom is",
            "onset": "when it started",
            "duration": "how long it lasts",
            "location": "where they feel it",
            "severity_self_rated": "severity 1-10",
        }
        need = [human_slots.get(s, s) for s in remaining_slots]
        lines.append("Still ask about: " + ", ".join(need) + ".")
    else:
        lines.append("You have enough information to recommend treatment.")
        lines.append(
            "Based on the collected answers (description, onset, duration, location, severity), "
            "recommend appropriate treatment and OTC medication. Use the symptom type, location, "
            "and severity to choose the right suggestion (e.g. headache in temples, severity 4–5 → "
            "rest, paracetamol or ibuprofen; stomach pain → different; cold/cough → different). "
            "Always say to follow the product label for dosage. Then say to see a doctor if "
            "symptoms persist or worsen."
        )
    return "\n".join(lines)
