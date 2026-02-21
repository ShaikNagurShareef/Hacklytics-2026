"""
Run Dietary agent turns. Usage from backend/:
  PYTHONPATH=. python scripts/test_dietary_agent.py
Ensure .env has a valid GEMINI_API_KEY.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.agents.dietary.agent import DietaryAgent


async def main():
    agent = DietaryAgent()
    session_id = "test-diet-session-1"

    # Turn 1: general / goals
    query1 = "I want to eat healthier and lose a bit of weight. I'm vegetarian."
    print("=== Dietary Agent – Turn 1 (goals + preference) ===")
    print("User:", query1)
    print("-" * 60)
    resp1 = await agent.invoke(session_id=session_id, query=query1, context=[])
    print("Agent:", resp1.content)
    print("Metadata:", resp1.metadata)
    print("-" * 60)

    # Turn 2: calorie calculation (BMR/TDEE) – tools should add numbers
    query2 = "What's my BMR and TDEE? I'm 70 kg, 170 cm, 30 years old, male."
    print("=== Dietary Agent – Turn 2 (BMR/TDEE) ===")
    print("User:", query2)
    print("-" * 60)
    resp2 = await agent.invoke(session_id=session_id, query=query2, context=[])
    print("Agent:", resp2.content)
    print("Metadata:", resp2.metadata)
    print("-" * 60)

    # Turn 3: meal plan intent
    query3 = "Can you suggest a simple meal plan for a day with around 1800 calories?"
    print("=== Dietary Agent – Turn 3 (meal plan) ===")
    print("User:", query3)
    print("-" * 60)
    resp3 = await agent.invoke(session_id=session_id, query=query3, context=[])
    print("Agent:", resp3.content)
    print("Metadata:", resp3.metadata)
    print("-" * 60)
    print("Dietary tests OK.")


if __name__ == "__main__":
    asyncio.run(main())
