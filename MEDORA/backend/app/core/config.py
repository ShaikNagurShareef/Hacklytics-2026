"""App configuration from environment. No secrets in code."""
import os
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


# Gemini
# Search (optional)
GEMINI_API_KEY: Optional[str] = get_env("GEMINI_API_KEY")
# Use model IDs that support generateContent (see https://ai.google.dev/gemini-api/docs/models)
# Override in .env if your region supports different models (e.g. gemini-1.5-pro).
GEMINI_MODEL_DEFAULT: str = get_env("GEMINI_MODEL_DEFAULT") or "gemini-2.0-flash"
GEMINI_MODEL_PRO: str = get_env("GEMINI_MODEL_PRO") or "gemini-2.0-flash"
GEMINI_MODEL_MED: str = get_env("GEMINI_MODEL_MED") or "medgemma"
# Nano Banana Pro = Gemini 3 Pro Image (Nano Banana Pro)
GEMINI_MODEL_NANO: str = get_env("GEMINI_MODEL_NANO") or "gemini-3-pro-image-preview"

# Search (optional)
TAVILY_API_KEY: Optional[str] = get_env("TAVILY_API_KEY")
