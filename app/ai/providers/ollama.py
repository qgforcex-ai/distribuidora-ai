import os
import requests

from app.ai.providers.base import LLMProvider


class OllamaProvider(LLMProvider):

    def __init__(self):
        self.url = os.getenv(
            "OLLAMA_URL",
            "http://host.docker.internal:11434"
        )

        self.model = os.getenv(
            "AI_MODEL",
            "qwen3:1.7b"
        )

    def chat(self, messages, tools=None):

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.url}/api/chat",
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        return response.json()["message"]