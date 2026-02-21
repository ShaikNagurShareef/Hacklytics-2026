"""
Real-time interactive chat for testing MEDORA agents.

Run from MEDORA/backend (or from project root: cd MEDORA/backend first).

  # Use orchestrator in-process (no server needed)
  PYTHONPATH=. python scripts/chat_realtime.py

  # Use running server (start server first: uvicorn app.main:app --host 127.0.0.1 --port 8000)
  PYTHONPATH=. python scripts/chat_realtime.py --url http://127.0.0.1:8000
  (If server has no /chat, script falls back to /virtual-doctor/chat.)

  # Virtual Doctor only (no orchestrator)
  PYTHONPATH=. python scripts/chat_realtime.py --agent virtual-doctor

Commands:
  /quit or /q   Exit
  /clear        Clear conversation context (new thread)
"""
import argparse
import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def parse_args():
    p = argparse.ArgumentParser(description="Real-time chat with MEDORA agents")
    p.add_argument("--url", default=None, help="Base URL of running API (e.g. http://127.0.0.1:8000). If not set, uses orchestrator in-process.")
    p.add_argument("--agent", choices=["orchestrator", "virtual-doctor", "wellbeing", "dietary"], default="orchestrator", help="Agent when using in-process (ignored if --url is set)")
    p.add_argument("--session", default="realtime-session", help="Session ID")
    return p.parse_args()


def _mime_from_path(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


async def chat_via_server(url: str, session_id: str, query: str, context: list, image_base64: str = None, image_mime_type: str = "image/jpeg", prefer_chat: bool = True) -> tuple[str, str, dict]:
    import httpx
    base = url.rstrip("/")
    payload = {"session_id": session_id, "query": query, "context": context}
    if image_base64 is not None:
        payload["image_base64"] = image_base64
        payload["image_mime_type"] = image_mime_type
        endpoint = f"{base}/virtual-doctor/chat"
    else:
        endpoint = f"{base}/chat" if prefer_chat else f"{base}/virtual-doctor/chat"
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(endpoint, json=payload)
        if r.status_code == 404 and endpoint.endswith("/chat") and not image_base64:
            endpoint = f"{base}/virtual-doctor/chat"
            r = await client.post(endpoint, json=payload)
    r.raise_for_status()
    data = r.json()
    return data.get("agent_name", ""), data.get("content", ""), data.get("metadata", {})


# One-off agent instances for in-process mode (keeps session state)
_agents = {}


def _get_agent(agent_name: str):
    global _agents
    if agent_name not in _agents:
        if agent_name == "orchestrator":
            from app.agents.orchestrator import OrchestratorAgent
            _agents[agent_name] = OrchestratorAgent()
        elif agent_name == "virtual-doctor":
            from app.agents.virtual_doctor.agent import VirtualDoctorAgent
            _agents[agent_name] = VirtualDoctorAgent()
        elif agent_name == "wellbeing":
            from app.agents.wellbeing import WellbeingCounsellorAgent
            _agents[agent_name] = WellbeingCounsellorAgent()
        elif agent_name == "dietary":
            from app.agents.dietary.agent import DietaryAgent
            _agents[agent_name] = DietaryAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    return _agents[agent_name]


async def chat_in_process(agent_name: str, session_id: str, query: str, context: list, image_base64: str = None, image_mime_type: str = "image/jpeg") -> tuple[str, str, dict]:
    agent = _get_agent(agent_name)
    if agent_name == "orchestrator":
        resp = await agent.handle(session_id, query, context)
        return resp.agent_name, resp.content, resp.metadata
    if agent_name == "virtual-doctor":
        resp = await agent.invoke(
            session_id, query, context,
            image_data=image_base64,
            image_mime_type=image_mime_type,
        )
        return resp.agent_name, resp.content, resp.metadata
    resp = await agent.invoke(session_id, query, context)
    return resp.agent_name, resp.content, resp.metadata


def read_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "/quit"


def main():
    args = parse_args()
    use_server = args.url is not None
    session_id = args.session
    context = []

    if use_server:
        print(f"Real-time chat → Server at {args.url}")
        print("  Commands: /quit, /q, /clear")
        print("  Image:   /image path/to/image.jpg  (then type your question)\n")
    else:
        print(f"Real-time chat → In-process ({args.agent})")
        print("  Session:", session_id)
        print("  Commands: /quit, /q, /clear")
        if args.agent == "virtual-doctor":
            print("  Image:   /image path/to/image.jpg  (then type your question)\n")
        else:
            print()

    print("-" * 60)

    while True:
        user_input = read_input("You: ")
        if not user_input:
            continue
        if user_input in ("/quit", "/q"):
            print("Bye.")
            break
        if user_input == "/clear":
            context = []
            print("[Context cleared.]\n")
            continue

        # Optional: /image path → load image and use as next message
        image_base64 = None
        image_mime_type = "image/jpeg"
        if user_input.lower().startswith("/image "):
            path = user_input[7:].strip()
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                image_mime_type = _mime_from_path(path)
                user_input = read_input("Message about the image: ").strip() or "What do you see in this image?"
            else:
                print(f"File not found: {path}\n")
                continue

        print("...")
        try:
            if use_server:
                agent_name, content, metadata = asyncio.run(chat_via_server(
                    args.url, session_id, user_input, context, image_base64, image_mime_type
                ))
            else:
                agent_name, content, metadata = asyncio.run(chat_in_process(
                    args.agent, session_id, user_input, context, image_base64, image_mime_type
                ))
        except Exception as e:
            print(f"Error: {e}\n")
            continue

        # Update context for next turn
        context.append({"role": "user", "content": user_input})
        context.append({"role": "assistant", "content": content})
        if len(context) > 20:
            context = context[-20:]

        print(f"\n[{agent_name}]")
        print(content)
        if metadata.get("routed_to"):
            print(f"  (routed to: {metadata['routed_to']})")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
