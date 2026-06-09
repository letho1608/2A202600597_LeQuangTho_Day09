"""Shared LLM factory for all agents.

Supports multiple providers: openrouter, nvidia, ollama, groq.
Provider and model are configured via environment variables.
"""

import os
import logging

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """Return a chat model based on the LLM_PROVIDER env var.

    Provider       | Env var              | Default model
    ---------------|----------------------|---------------------------
    openrouter     | OPENROUTER_API_KEY   | anthropic/claude-sonnet-4-5
    nvidia         | NVIDIA_API_KEY       | meta/llama-3.1-70b-instruct
    ollama         | (none)               | minimax-m3:cloud
    groq           | GROQ_API_KEY         | llama-3.3-70b-versatile

    The model can be overridden via LLM_MODEL for any provider.
    For backward compatibility, OPENROUTER_MODEL is used when provider=openrouter
    and LLM_MODEL is not set.
    """
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    model = os.getenv("LLM_MODEL", "").strip()

    logger.info("LLM provider: %s, model: %s", provider, model or "(default)")

    if provider == "nvidia":
        return _get_nvidia(model)
    elif provider == "ollama":
        return _get_ollama(model)
    elif provider == "groq":
        return _get_groq(model)
    else:
        return _get_openrouter(model)


def _get_openrouter(model: str) -> BaseChatModel:
    """OpenRouter via OpenAI-compatible API."""
    from langchain_openai import ChatOpenAI

    if not model:
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )


def _get_nvidia(model: str) -> BaseChatModel:
    """NVIDIA NIM / API Catalog."""
    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
    except ImportError:
        logger.error(
            "langchain-nvidia-ai-endpoints not installed. "
            "Run: pip install langchain-nvidia-ai-endpoints"
        )
        raise

    return ChatNVIDIA(
        model=model or "meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
    )


def _get_ollama(model: str) -> BaseChatModel:
    """Ollama local inference."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        logger.error(
            "langchain-ollama not installed. "
            "Run: pip install langchain-ollama"
        )
        raise

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return ChatOllama(
        model=model or "minimax-m3:cloud",
        base_url=ollama_base_url,
    )


def _get_groq(model: str) -> BaseChatModel:
    """Groq via OpenAI-compatible API."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or "llama-3.3-70b-versatile",
        openai_api_key=os.getenv("GROQ_API_KEY"),
        openai_api_base="https://api.groq.com/openai/v1",
    )
