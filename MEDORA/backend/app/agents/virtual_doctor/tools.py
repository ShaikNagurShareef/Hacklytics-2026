"""
Deterministic tools / utility functions for the Virtual Doctor Agent.

These functions handle severity assessment, first-aid lookup, and
formatting without needing an LLM round-trip.
"""

from __future__ import annotations

from typing import Dict, List

from app.agents.virtual_doctor.schemas import Severity, TriageResult


# ------------------------------------------------------------------
# Severity keyword mappings
# ------------------------------------------------------------------
SEVERITY_LEVELS: Dict[str, Dict] = {
    "critical": {
        "keywords": [
            "chest pain", "heart attack", "stroke", "can't breathe",
            "cannot breathe", "not breathing", "severe bleeding",
            "unconscious", "seizure", "choking", "anaphylaxis",
            "poisoning", "overdose", "collapsed", "suicidal", "suicide",
        ],
        "recommendation": (
            "🚨 This sounds like a medical emergency. "
            "Please call 911 (or your local emergency number) IMMEDIATELY. "
            "Do not wait."
        ),
    },
    "high": {
        "keywords": [
            "difficulty breathing", "high fever", "severe pain",
            "blood in stool", "blood in urine", "sudden vision loss",
            "confusion", "numbness", "slurred speech", "severe headache",
            "worst headache", "severe allergic", "swollen tongue",
            "chest tightness", "fainting",
        ],
        "recommendation": (
            "⚠️ These symptoms may require urgent medical attention. "
            "Please visit an emergency room or urgent care centre today."
        ),
    },
    "moderate": {
        "keywords": [
            "persistent cough", "fever", "vomiting", "diarrhea",
            "ear pain", "sore throat", "rash", "swelling", "infection",
            "painful urination", "back pain", "joint pain",
            "shortness of breath", "dizziness",
        ],
        "recommendation": (
            "📋 These symptoms should be evaluated by a doctor within "
            "24-48 hours. Monitor your condition and seek earlier care "
            "if symptoms worsen."
        ),
    },
    "low": {
        "keywords": [
            "mild headache", "runny nose", "sneezing", "fatigue",
            "muscle soreness", "mild cough", "minor cut", "bruise",
            "dry skin", "insomnia",
        ],
        "recommendation": (
            "💚 These symptoms are generally mild. Rest, stay hydrated, "
            "and monitor. See a doctor if symptoms persist beyond a few "
            "days or worsen."
        ),
    },
}


# ------------------------------------------------------------------
# First-aid database (deterministic lookup)
# ------------------------------------------------------------------
FIRST_AID_DB: Dict[str, str] = {
    "choking": (
        "### Choking – First Aid\n"
        "1. **Ask** the person: 'Are you choking?'\n"
        "2. If they can't speak/cough, stand behind them.\n"
        "3. Place your fist just above the navel.\n"
        "4. Grasp your fist with the other hand.\n"
        "5. Perform **quick upward thrusts** (Heimlich manoeuvre).\n"
        "6. Repeat until the object is expelled or help arrives.\n"
        "⚠️ For infants: use back blows and chest thrusts instead."
    ),
    "bleeding": (
        "### Severe Bleeding – First Aid\n"
        "1. **Apply direct pressure** with a clean cloth or bandage.\n"
        "2. Press firmly and do NOT remove the cloth even if soaked "
        "through – add more layers on top.\n"
        "3. **Elevate** the injured area above the heart if possible.\n"
        "4. If bleeding doesn't stop, apply a tourniquet 2-3 inches "
        "above the wound (only as a last resort).\n"
        "5. Call 911 immediately.\n"
        "⚠️ Do NOT remove embedded objects."
    ),
    "burns": (
        "### Burns – First Aid\n"
        "1. **Cool the burn** under cool (not cold) running water for "
        "at least 10-20 minutes.\n"
        "2. Remove jewellery or tight clothing near the burn BEFORE "
        "swelling starts.\n"
        "3. Cover with a clean, non-fluffy dressing or cling film.\n"
        "4. Do NOT apply ice, butter, or toothpaste.\n"
        "5. Take over-the-counter pain relief if needed.\n"
        "⚠️ Seek medical help for burns larger than your hand, on the "
        "face/hands/feet, or if blistering is severe."
    ),
    "fracture": (
        "### Suspected Fracture – First Aid\n"
        "1. **Do NOT try to realign** the bone.\n"
        "2. **Immobilise** the injured area – use a splint or padding.\n"
        "3. Apply an **ice pack** wrapped in cloth to reduce swelling.\n"
        "4. If there's an open wound, cover with a clean dressing.\n"
        "5. Keep the person still and calm.\n"
        "6. Call for medical help.\n"
        "⚠️ Do NOT move the person if you suspect a spinal injury."
    ),
    "heart_attack": (
        "### Suspected Heart Attack – First Aid\n"
        "1. **Call 911 immediately.**\n"
        "2. Have the person sit or lie down in a comfortable position.\n"
        "3. If not allergic, give them an **aspirin** (325 mg) to chew.\n"
        "4. Loosen any tight clothing.\n"
        "5. If the person becomes unconscious and stops breathing, "
        "begin **CPR** (30 compressions, 2 breaths).\n"
        "6. Use an **AED** if available.\n"
        "⚠️ Do NOT leave the person alone."
    ),
    "seizure": (
        "### Seizure – First Aid\n"
        "1. **Clear the area** of hard or sharp objects.\n"
        "2. Place something soft under their head.\n"
        "3. **Do NOT** hold them down or put anything in their mouth.\n"
        "4. Turn them on their side (recovery position) once the "
        "seizure stops.\n"
        "5. Time the seizure – call 911 if it lasts > 5 minutes.\n"
        "6. Stay with them until they are fully conscious."
    ),
    "stroke": (
        "### Suspected Stroke – FAST Check\n"
        "**F** – Face: Ask to smile. Does one side droop?\n"
        "**A** – Arms: Can they raise both arms? Does one drift down?\n"
        "**S** – Speech: Is speech slurred or strange?\n"
        "**T** – Time: Call 911 IMMEDIATELY.\n\n"
        "1. Note the time symptoms started.\n"
        "2. Do NOT give food, drink, or medication.\n"
        "3. Keep the person comfortable and monitoring breathing.\n"
        "⚠️ Every minute counts – rapid treatment saves brain cells."
    ),
    "cpr": (
        "### CPR – Cardiopulmonary Resuscitation\n"
        "1. **Check** if the person is responsive – tap and shout.\n"
        "2. **Call 911** (or have someone call).\n"
        "3. Place the person on their back on a firm surface.\n"
        "4. Place heel of one hand on the centre of the chest, "
        "other hand on top, fingers interlocked.\n"
        "5. Push **hard and fast**: 2 inches deep, 100-120 per minute.\n"
        "6. After 30 compressions, give **2 rescue breaths** "
        "(tilt head, lift chin, seal mouth).\n"
        "7. Continue until help arrives or the person starts breathing.\n"
        "⚠️ Hands-only CPR (no breaths) is still effective if you're "
        "untrained or uncomfortable with rescue breaths."
    ),
}


# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------
def assess_severity(text: str) -> Dict:
    """
    Deterministic severity assessment based on keyword matching.

    Returns dict with keys: level, matched, recommendation.
    """
    text_lower = text.lower()
    for level in ("critical", "high", "moderate", "low"):
        info = SEVERITY_LEVELS[level]
        matched = [kw for kw in info["keywords"] if kw in text_lower]
        if matched:
            return {
                "level": level,
                "matched": matched,
                "recommendation": info["recommendation"],
            }
    return {
        "level": "unknown",
        "matched": [],
        "recommendation": (
            "I'd like to understand your symptoms better. "
            "Could you describe what you're experiencing in more detail?"
        ),
    }


def get_first_aid_instructions(text: str) -> str:
    """
    Look up first-aid instructions based on keywords in the text.
    Returns a Markdown block or empty string if no match.
    """
    text_lower = text.lower()
    results = []
    for key, instructions in FIRST_AID_DB.items():
        if key.replace("_", " ") in text_lower or key in text_lower:
            results.append(instructions)
    return "\n\n".join(results) if results else ""


def format_triage_report(triage: TriageResult) -> str:
    """Format a TriageResult into a human-readable Markdown block."""
    severity_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "moderate": "🟡",
        "low": "🟢",
    }
    emoji = severity_emoji.get(triage.severity, "⚪")

    lines = [
        f"### {emoji} Triage Assessment: **{triage.severity.upper()}**\n",
        triage.recommendation,
    ]
    if triage.matched_keywords:
        kw_list = ", ".join(f"`{k}`" for k in triage.matched_keywords)
        lines.append(f"\n**Flagged symptoms**: {kw_list}")
    return "\n".join(lines)
