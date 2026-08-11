"""
Shared Gemini client. One client, used for both answer generation (Phase 7)
and chart-image understanding (Phase 3) — Gemini's free tier is multimodal,
so both live behind the same API key and the same thin wrapper.

Loads ``GOOGLE_API_KEY`` from a local ``.env`` file for development (never
committed — see .gitignore) or from the real environment in CI/production;
``load_dotenv()`` is a no-op if the variable is already set, so this works
identically in both cases.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai

__all__ = ["get_client"]

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        load_dotenv()
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey (no card required) and "
                "put it in a .env file as GOOGLE_API_KEY=... — see .env.example."
            )
        _client = genai.Client(api_key=api_key)
    return _client
