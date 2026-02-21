"""
Run one wellbeing agent turn. Usage from backend/:
  PYTHONPATH=. python scripts/test_wellbeing_agent.py
Ensure .env has a valid GEMINI_API_KEY.
"""
import asyncio
import os
import sys

# Load .env from backend/ (parent of scripts/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.agents.wellbeing import WellbeingCounsellorAgent


async def main():
    agent = WellbeingCounsellorAgent()
    session_id = "test-session-1"

    # Turn 1: initial message (agent asks 1 question)
    query1 = "I've been feeling really overwhelmed lately and can't sleep well."
    print("=== Turn 1 ===")
    print("User:", query1)
    print("-" * 60)
    resp1 = await agent.invoke(session_id=session_id, query=query1, context=[])
    print("Agent:", resp1.content)
    print("-" * 60)

    # Turn 2: user answers (agent asks 3 follow-up questions)
    query2 = "Work mostly. Deadlines and my manager. I can't switch off."
    print("=== Turn 2 (follow-up) ===")
    print("User:", query2)
    print("-" * 60)
    resp2 = await agent.invoke(session_id=session_id, query=query2, context=[])
    print("Agent (3 follow-up questions):", resp2.content)
    print("-" * 60)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
