"""
Deterministic tools / utility functions for the Dietary Agent.

These are *pure* helper functions that the agent calls to compute
nutrition metrics without needing an LLM round-trip.
"""

from __future__ import annotations

from typing import Optional

from app.agents.dietary.schemas import ActivityLevel, MacroSplit, NutritionalReport


# ------------------------------------------------------------------
# Activity-level multipliers (Harris-Benedict revised)
# ------------------------------------------------------------------
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: float,
    gender: str = "male",
) -> float:
    """
    Mifflin-St Jeor equation for Basal Metabolic Rate.

    Male  : 10 × weight(kg) + 6.25 × height(cm) − 5 × age − 161 + 166
            simplified → 10w + 6.25h − 5a + 5
    Female: 10w + 6.25h − 5a − 161
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender.lower() in ("male", "m"):
        return base + 5
    return base - 161


def calculate_tdee(
    bmr: float,
    activity_level: str = "moderate",
) -> float:
    """Total Daily Energy Expenditure = BMR × activity multiplier."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)
    return bmr * multiplier


def build_macro_split(
    tdee: float,
    protein_pct: float = 0.30,
    carbs_pct: float = 0.40,
    fats_pct: float = 0.30,
    fibre_g: float = 25.0,
) -> MacroSplit:
    """
    Compute gram targets from TDEE and percentage split.

    Energy densities: protein 4 kcal/g, carbs 4 kcal/g, fats 9 kcal/g.
    """
    return MacroSplit(
        protein_g=round((tdee * protein_pct) / 4, 1),
        carbs_g=round((tdee * carbs_pct) / 4, 1),
        fats_g=round((tdee * fats_pct) / 9, 1),
        fibre_g=fibre_g,
    )


def format_nutritional_report(report: NutritionalReport) -> str:
    """Return a human-friendly Markdown summary of the nutritional report."""
    m = report.macros
    return (
        "### 📊 Your Nutritional Profile\n\n"
        f"| Metric               | Value          |\n"
        f"|----------------------|----------------|\n"
        f"| **BMR**              | {report.bmr:,.0f} kcal/day |\n"
        f"| **TDEE**             | {report.tdee:,.0f} kcal/day |\n"
        f"| **Protein target**   | {m.protein_g:.0f} g        |\n"
        f"| **Carbs target**     | {m.carbs_g:.0f} g          |\n"
        f"| **Fats target**      | {m.fats_g:.0f} g           |\n"
        f"| **Fibre target**     | {m.fibre_g:.0f} g          |\n"
    )
