"""
Pydantic schemas for the Dietary Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------
class DietaryPreference(str, Enum):
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non_vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    MEDITERRANEAN = "mediterranean"
    OTHER = "other"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"          # little or no exercise
    LIGHT = "light"                  # 1-3 days / week
    MODERATE = "moderate"            # 3-5 days / week
    ACTIVE = "active"                # 6-7 days / week
    VERY_ACTIVE = "very_active"      # intense daily or 2x/day


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------
class UserProfile(BaseModel):
    """Collected user profile used across dietary conversations."""
    age: Optional[int] = None
    gender: Optional[Gender] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    dietary_preference: Optional[DietaryPreference] = None
    allergies: List[str] = Field(default_factory=list)
    health_conditions: List[str] = Field(default_factory=list)
    calorie_target: Optional[int] = None
    goal: Optional[str] = None  # e.g. "weight loss", "muscle gain", "maintenance"


class MacroSplit(BaseModel):
    """Macro-nutrient gram targets for a day."""
    protein_g: float
    carbs_g: float
    fats_g: float
    fibre_g: float = 25.0  # default recommendation


class NutritionalReport(BaseModel):
    """Output of a BMR / TDEE calculation with macro split."""
    bmr: float
    tdee: float
    macros: MacroSplit


class MealEntry(BaseModel):
    """A single meal in a meal plan."""
    name: str
    description: str = ""
    calories: float
    protein_g: float
    carbs_g: float
    fats_g: float


class MealPlanRequest(BaseModel):
    """Structured request for a meal plan generation."""
    user_profile: UserProfile
    meals_per_day: int = 4
    cuisine_preference: Optional[str] = None
    duration_days: int = 1
    additional_notes: Optional[str] = None


class MealPlanDay(BaseModel):
    """A single day's meal plan."""
    day: int
    meals: List[MealEntry]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fats_g: float
