"""
Run Diagnostic Imaging agent. Usage from backend/:
  PYTHONPATH=. python scripts/test_diagnostic_agent.py [path/to/image.png]
Without an image: agent returns the "upload image" prompt.
With an image: runs modality detection + analysis + report generation.
Ensure .env has a valid GEMINI_API_KEY.
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

from app.agents.diagnostic.agent import DiagnosticAgent


def mime_from_path(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


async def main():
    parser = argparse.ArgumentParser(description="Test Diagnostic Imaging agent")
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to medical image (e.g. X-ray, fundus, skin). Optional.",
    )
    parser.add_argument(
        "--query",
        "-q",
        default="Please analyse this image and provide a diagnostic report.",
        help="User message / clinical indication",
    )
    parser.add_argument(
        "--session",
        default="test-diagnostic-session-1",
        help="Session ID",
    )
    args = parser.parse_args()

    agent = DiagnosticAgent()
    session_id = args.session
    query = args.query
    image_base64 = None
    image_mime_type = "image/jpeg"

    if args.image:
        path = os.path.abspath(args.image)
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)
        with open(path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        image_mime_type = mime_from_path(path)
        print(f"Loaded image: {path} ({image_mime_type})")
    else:
        print("No image provided — agent will return the upload prompt.\n")

    print("=== Diagnostic Agent ===")
    print("Query:", query)
    print("-" * 60)
    resp = await agent.invoke(
        session_id=session_id,
        query=query,
        context=[],
        image_data=image_base64,
        image_mime_type=image_mime_type,
    )
    print("Agent:", resp.agent_name)
    print("-" * 60)
    print(resp.content)
    print("-" * 60)
    print("Metadata:", resp.metadata)
    if resp.metadata.get("structured_report"):
        print("\nStructured report (keys):", list(resp.metadata["structured_report"].keys()))


if __name__ == "__main__":
    asyncio.run(main())
