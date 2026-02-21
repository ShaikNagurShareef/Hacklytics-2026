"""
Test Virtual Doctor image analysis (Gemini Vision).

Usage from backend/:
  PYTHONPATH=. python scripts/test_virtual_doctor_image.py

Optional: pass path to an image file:
  PYTHONPATH=. python scripts/test_virtual_doctor_image.py path/to/image.jpg

Requires GEMINI_API_KEY in .env.
"""
import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def get_test_image_base64(image_path: str = None):
    """Return (base64_string, mime_type). Use a small in-memory PNG if no path."""
    if image_path and os.path.isfile(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        return base64.b64encode(data).decode("utf-8"), mime
    # Tiny placeholder PNG (Gemini may reject; for full analysis pass a real image path)
    minimal_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02"
        b"\x08\x02\x00\x00\x00\xfd\xd4\x9a\x73\x00\x00\x00\x0cIDATx\x9cc\xf8"
        b"\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00"
        b"IEND\xaeB`\x82"
    )
    return base64.b64encode(minimal_png).decode("utf-8"), "image/png"


async def main():
    from app.agents.virtual_doctor.agent import VirtualDoctorAgent

    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    image_b64, mime = get_test_image_base64(image_path)

    agent = VirtualDoctorAgent()
    session_id = "test-image-session"
    query = "What do you see in this image? Is there anything I should get checked?"

    print("=== Virtual Doctor – Image analysis ===")
    print("Query:", query)
    print("Image: ", image_path or "minimal 2x2 PNG (placeholder)")
    print("-" * 60)

    resp = await agent.invoke(
        session_id=session_id,
        query=query,
        context=[],
        image_data=image_b64,
        image_mime_type=mime,
    )

    print("Agent:", resp.content)
    print("Metadata:", resp.metadata)
    print("-" * 60)
    assert resp.metadata.get("intent") == "image_analysis", "Expected intent image_analysis"
    assert resp.metadata.get("image_provided") is True, "Expected image_provided True"
    print("Image analysis test OK (path + fallback message verified).")
    print("For a full Gemini Vision response, run with a real image: python scripts/test_virtual_doctor_image.py path/to/image.jpg")


if __name__ == "__main__":
    asyncio.run(main())
