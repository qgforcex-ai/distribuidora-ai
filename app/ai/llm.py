import requests


OLLAMA_URL = "http://host.docker.internal:11434"
OLLAMA_MODEL = "qwen3:1.7b"


def perguntar_llm(pergunta: str) -> str:

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é o assistente de inteligência comercial "
                    "do sistema Distribuidora AI. "
                    "Responda sempre em português brasileiro, "
                    "de forma objetiva."
                )
            },
            {
                "role": "user",
                "content": pergunta
            }
        ],

        "stream": False
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    dados = response.json()

    return dados["message"]["content"]