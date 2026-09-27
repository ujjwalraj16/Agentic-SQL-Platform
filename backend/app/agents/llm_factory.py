"""
agents/llm_factory.py – LLM factory: returns the configured LLM instance.

Supports:
- Ollama (local, via langchain-ollama)
- Gemini (cloud, via langchain-google-genai)

Provider is configured via LLM_PROVIDER env var.
No API keys are hard-coded here.
"""

from __future__ import annotations
import logging
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """Return a cached LLM instance based on LLM_PROVIDER."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        logger.info(
            "Using Ollama LLM: %s @ %s",
            settings.ollama_model,
            settings.ollama_base_url,
        )
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature,
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Set it in .env or switch to LLM_PROVIDER=ollama."
            )
        logger.info("Using Gemini LLM: %s", settings.gemini_model)
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            "Supported values: 'ollama', 'gemini'."
        )
