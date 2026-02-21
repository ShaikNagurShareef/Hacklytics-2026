"""
Run Virtual Doctor agent with a MOCK LLM (no API calls). Use when you want to
test the follow-up flow and metadata without hitting Gemini.

  PYTHONPATH=. python scripts/test_virtual_doctor_mock.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock LLM before importing agent
class MockLLM:
    async def generate(self, messages, **kwargs):
        # Inspect last user message to return a plausible reply (simulate follow-up flow)
        user_content = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_content = (m.get("content") or "").lower()
                break
        if "headache" in user_content or "tired" in user_content:
            return "I hear you. When did it start? How long does it last?"
        if "days ago" in user_content or "comes and goes" in user_content or "started about" in user_content:
            return "That helps. Where do you feel the headache—temples, forehead, or elsewhere?"
        if "temples" in user_content or "forehead" in user_content or "back of" in user_content or "location" in user_content:
            return "Thanks. On a scale of 1 to 10, how severe is the pain?"
        if "4" in user_content or "5" in user_content or "out of 10" in user_content or "severity" in user_content:
            return (
                "Based on your headache in the temples, intermittent for two days, severity around 5: "
                "try rest and paracetamol or ibuprofen—follow the product label. See a doctor if it persists or worsens."
            )
        if "burn" in user_content:
            return "Cool the burn under running water for 10-20 minutes. Seek medical attention if needed."
        if "cough" in user_content or "fever" in user_content:
            return "That sounds concerning. How high is the fever? Is the cough dry or with mucus?"
        return "I understand. Can you tell me more?"


def mock_get_llm_client():
    return MockLLM()


# Patch the agent's LLM
import app.agents.virtual_doctor.agent as agent_module
agent_module.VirtualDoctorAgent._get_llm_client = lambda self: mock_get_llm_client()

from app.agents.virtual_doctor.agent import VirtualDoctorAgent


async def main():
    agent = VirtualDoctorAgent()
    session_id = "test-mock-session"

    # Turn 1: symptom (consultation flow)
    query1 = "I've had a mild headache and feel a bit tired for the last two days."
    print("=== Turn 1 (mild symptom) ===")
    print("User:", query1)
    resp1 = await agent.invoke(session_id=session_id, query=query1, context=[])
    print("Agent:", resp1.content)
    print("Metadata keys:", list(resp1.metadata.keys()))
    assert "remaining_questions" in resp1.metadata
    assert "collected_so_far" in resp1.metadata
    assert resp1.metadata["collected_so_far"].get("description")
    print("-" * 60)

    # Turn 2: user answers onset + duration
    context2 = [
        {"role": "user", "content": query1},
        {"role": "assistant", "content": resp1.content},
    ]
    query2 = "It started about 2 days ago. It comes and goes."
    print("=== Turn 2 (onset + duration) ===")
    print("User:", query2)
    resp2 = await agent.invoke(session_id=session_id, query=query2, context=context2)
    print("Agent:", resp2.content)
    print("collected_so_far:", resp2.metadata.get("collected_so_far"))
    cf = resp2.metadata.get("collected_so_far") or {}
    assert cf.get("onset") or cf.get("duration"), "Expected onset or duration extracted"
    print("-" * 60)

    # Turn 3: user answers location
    context3 = context2 + [{"role": "user", "content": query2}, {"role": "assistant", "content": resp2.content}]
    query3 = "Mostly in my temples. Sometimes the back of my head."
    print("=== Turn 3 (location) ===")
    print("User:", query3)
    resp3 = await agent.invoke(session_id=session_id, query=query3, context=context3)
    print("Agent:", resp3.content)
    print("collected_so_far:", resp3.metadata.get("collected_so_far"))
    print("-" * 60)

    # Turn 4: user answers severity
    context4 = context3 + [{"role": "user", "content": query3}, {"role": "assistant", "content": resp3.content}]
    query4 = "Maybe a 4 or 5 out of 10."
    print("=== Turn 4 (severity 1-10) ===")
    print("User:", query4)
    resp4 = await agent.invoke(session_id=session_id, query=query4, context=context4)
    print("Agent:", resp4.content)
    print("collected_so_far:", resp4.metadata.get("collected_so_far"))
    cf4 = resp4.metadata.get("collected_so_far") or {}
    assert cf4.get("severity_self_rated") is not None, "Expected severity extracted"
    print("-" * 60)

    # Turn 5: first aid (different intent, after consultation is filled)
    query5 = "What's the first aid for a small burn?"
    print("=== Turn 5 (first aid) ===")
    print("User:", query5)
    resp5 = await agent.invoke(session_id=session_id, query=query5, context=[])
    print("Agent:", resp5.content)
    assert resp5.metadata.get("intent") == "first_aid"
    print("-" * 60)

    print("All mock tests passed (consultation flow + first aid).")


if __name__ == "__main__":
    asyncio.run(main())
