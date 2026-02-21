"""App configuration from environment. No secrets in code."""
import os
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


# Gemini
# Search (optional)
GEMINI_API_KEY: Optional[str] = get_env("GEMINI_API_KEY")
# Use model IDs that support generateContent (see https://ai.google.dev/gemini-api/docs/models)
# gemini-2.0-flash is no longer available to new users; use 3.x preview models.
# Override in .env if needed.
GEMINI_MODEL_DEFAULT: str = get_env("GEMINI_MODEL_DEFAULT") or "gemini-2.5-flash"
GEMINI_MODEL_PRO: str = get_env("GEMINI_MODEL_PRO") or "gemini-2.5-pro"
GEMINI_MODEL_MED: str = get_env("GEMINI_MODEL_MED") or "medgemma"
# Nano Banana Pro = Gemini 3 Pro Image (Nano Banana Pro)
GEMINI_MODEL_NANO: str = get_env("GEMINI_MODEL_NANO") or "gemini-3-pro-image-preview"

# Search (optional)
TAVILY_API_KEY: Optional[str] = get_env("TAVILY_API_KEY")

# Auth
JWT_SECRET: str = get_env("JWT_SECRET") or "medora-dev-secret-change-in-production"
JWT_ALGORITHM: str = get_env("JWT_ALGORITHM") or "HS256"
JWT_EXPIRE_MINUTES: int = int(get_env("JWT_EXPIRE_MINUTES") or "10080")  # 7 days
