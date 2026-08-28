import requests


OLLAMA_URL = "http://host.docker.internal:11434"
OLLAMA_MODEL = "qwen3:1.7b"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ranking_clientes",
            "description": (
                "Consulta o ranking de clientes por valor total comprado "
                "em um determinado período."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial no formato YYYY-MM-DD"
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD"
                    }
                },
                "required": [
                    "data_inicio",
                    "data_fim"
                ]
            }
        }
    }
]


def perguntar_llm(messages, tools=None):

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }

    if tools:
        payload["tools"] = tools

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    return response.json()["message"]