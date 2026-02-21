from pydantic import BaseModel, Field
from typing import List

class TutorialStep(BaseModel):
    step_number: int
    title: str
    explanation: str = Field(description="Easy to understand explanation for the user")
    image_prompt: str = Field(description="A prompt that could be used to generate an image or diagram illustrating this step")

class VisualizationTutorial(BaseModel):
    overview: str
    steps: List[TutorialStep]
