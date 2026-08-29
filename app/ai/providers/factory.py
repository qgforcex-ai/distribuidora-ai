import os

from app.ai.providers.ollama import OllamaProvider


def get_llm_provider():

    provider = os.getenv(
        "AI_PROVIDER",
        "ollama"
    ).lower()

    if provider == "ollama":
        return OllamaProvider()

    raise ValueError(
        f"Provider de IA não suportado: {provider}"
    )