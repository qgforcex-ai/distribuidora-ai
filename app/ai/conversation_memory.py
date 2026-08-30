import json
import os

import redis


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

SESSION_TTL = 3600


def _chave(session_id: str) -> str:
    return f"ai:conversation:{session_id}"


def salvar_contexto(session_id: str, contexto: dict):
    redis_client.setex(
        _chave(session_id),
        SESSION_TTL,
        json.dumps(contexto, ensure_ascii=False)
    )


def buscar_contexto(session_id: str):
    conteudo = redis_client.get(
        _chave(session_id)
    )

    if not conteudo:
        return None

    return json.loads(conteudo)


def limpar_contexto(session_id: str):
    redis_client.delete(
        _chave(session_id)
    )