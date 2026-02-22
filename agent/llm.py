"""
STREAM Agent — LLM Factory.

Initialises the ChatOpenAI instance pointing at the AIPipe / OpenRouter
compatible endpoint.  All config comes from environment variables so the
same code works locally and in production.

Env vars
--------
AIPIPE_TOKEN     : str   — Bearer token for AIPipe (required)
AIPIPE_BASE_URL  : str   — Base URL, default https://aipipe.org/openrouter/v1
AIPIPE_MODEL     : str   — Model identifier, default openai/gpt-4.1-nano
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env from data_ingestion/ (same as db.py)
_env_path = Path(__file__).resolve().parent.parent / "data_ingestion" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# Also try project-root .env
_root_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env, override=True)

AIPIPE_TOKEN = os.environ.get("AIPIPE_TOKEN", "")
AIPIPE_BASE_URL = os.environ.get("AIPIPE_BASE_URL", "https://aipipe.org/openrouter/v1")
AIPIPE_MODEL = os.environ.get("AIPIPE_MODEL", "openai/gpt-4.1-nano")


def get_llm(temperature: float = 0, **kwargs) -> ChatOpenAI:
    """Return a ChatOpenAI instance configured for AIPipe."""
    if not AIPIPE_TOKEN:
        raise RuntimeError(
            "AIPIPE_TOKEN is not set. Add it to data_ingestion/.env or export it."
        )
    return ChatOpenAI(
        base_url=AIPIPE_BASE_URL,
        api_key=AIPIPE_TOKEN,
        model=AIPIPE_MODEL,
        temperature=temperature,
        **kwargs,
    )
