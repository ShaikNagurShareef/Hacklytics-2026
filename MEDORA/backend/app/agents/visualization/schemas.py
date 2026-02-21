from pydantic import BaseModel, Field
from typing import List, Optional

class DiagnosticDashboard(BaseModel):
    """Structured summary from a diagnostic report for dashboard visualization."""
    summary: str = Field(default="", description="One-line summary of the report")
    modality: str = Field(default="", description="e.g. CT, X-Ray, MRI")
    body_region: str = Field(default="", description="e.g. Head, Chest, Abdomen")
    severity: str = Field(default="", description="e.g. Routine, Urgent, Critical")
    key_findings: List[str] = Field(default_factory=list, description="3-6 bullet-point findings for the dashboard")
    recommendations: List[str] = Field(default_factory=list, description="Recommended next steps")

class TutorialStep(BaseModel):
    step_number: int
    title: str
    explanation: str = Field(description="Easy to understand explanation for the user")
    image_prompt: str = Field(description="A prompt that could be used to generate an image or diagram illustrating this step")

class VisualizationTutorial(BaseModel):
    overview: str
    dashboard: Optional[DiagnosticDashboard] = None
    steps: List[TutorialStep]
