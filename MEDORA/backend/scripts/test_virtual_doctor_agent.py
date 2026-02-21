"""
Run Virtual Doctor agent turns. Usage from backend/:
  PYTHONPATH=. python scripts/test_virtual_doctor_agent.py
Ensure .env has a valid GEMINI_API_KEY.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.agents.virtual_doctor.agent import VirtualDoctorAgent


async def main():
    agent = VirtualDoctorAgent()
    session_id = "test-vd-session-1"

    # Turn 1: mild symptom (general consultation)
    query1 = "I've had a mild headache and feel a bit tired for the last two days."
    print("=== Virtual Doctor – Turn 1 (mild symptom) ===")
    print("User:", query1)
    print("-" * 60)
    resp1 = await agent.invoke(session_id=session_id, query=query1, context=[])
    print("Agent:", resp1.content)
    print("Metadata:", resp1.metadata)
    print("-" * 60)

    # Turn 2: first-aid intent
    query2 = "What's the first aid for a small burn?"
    print("=== Virtual Doctor – Turn 2 (first aid) ===")
    print("User:", query2)
    print("-" * 60)
    resp2 = await agent.invoke(session_id=session_id, query=query2, context=[])
    print("Agent:", resp2.content)
    print("Metadata:", resp2.metadata)
    print("-" * 60)

    # Turn 3: symptom that may trigger triage (moderate)
    query3 = "I have a persistent cough and fever since yesterday."
    print("=== Virtual Doctor – Turn 3 (symptom assessment) ===")
    print("User:", query3)
    print("-" * 60)
    resp3 = await agent.invoke(session_id=session_id, query=query3, context=[])
    print("Agent:", resp3.content)
    print("Metadata:", resp3.metadata)
    print("-" * 60)
    print("Virtual Doctor tests OK.")


if __name__ == "__main__":
    asyncio.run(main())
