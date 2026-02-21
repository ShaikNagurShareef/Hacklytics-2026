"""Wellbeing indicator schema: stress, anxiety, depression. Extensible for more parameters."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StressLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AnxietyLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class DepressionLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


class WellbeingIndicators(BaseModel):
    """Detected indicators from conversation. Aligned to PHQ-9 / GAD-7 / PSS concepts."""

    stress: StressLevel = Field(default=StressLevel.LOW, description="Perceived stress level")
    anxiety: AnxietyLevel = Field(default=AnxietyLevel.NONE, description="Anxiety indicators")
    depression: DepressionLevel = Field(default=DepressionLevel.NONE, description="Depression indicators")
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Overall confidence 0-1")

    def to_metadata(self) -> dict:
        return {
            "stress": self.stress.value,
            "anxiety": self.anxiety.value,
            "depression": self.depression.value,
            **({"confidence": self.confidence} if self.confidence is not None else {}),
        }

    @classmethod
    def from_parsed(cls, data: dict) -> "WellbeingIndicators":
        """Build from LLM-parsed dict (string values). Uses defaults on invalid values."""
        def safe_stress(v: str) -> StressLevel:
            try:
                return StressLevel(v.lower().strip().replace(" ", "_"))
            except (ValueError, AttributeError):
                return StressLevel.LOW

        def safe_anxiety(v: str) -> AnxietyLevel:
            try:
                return AnxietyLevel(v.lower().strip().replace(" ", "_"))
            except (ValueError, AttributeError):
                return AnxietyLevel.NONE

        def safe_depression(v: str) -> DepressionLevel:
            v = (v or "").lower().strip().replace(" ", "_").replace("-", "_")
            if v == "moderatelysevere":
                v = "moderately_severe"
            try:
                return DepressionLevel(v)
            except (ValueError, AttributeError):
                return DepressionLevel.NONE

        stress = safe_stress(str(data.get("stress", "low")))
        anxiety = safe_anxiety(str(data.get("anxiety", "none")))
        depression = safe_depression(str(data.get("depression", "none")))
        conf = data.get("confidence")
        confidence = float(conf) if conf is not None else None
        return cls(stress=stress, anxiety=anxiety, depression=depression, confidence=confidence)
