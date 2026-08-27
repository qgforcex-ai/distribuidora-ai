from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.llm import perguntar_llm


router = APIRouter(
    prefix="/ia",
    tags=["IA"]
)


class PerguntaIA(BaseModel):
    pergunta: str


@router.post("/perguntar")
def perguntar(dados: PerguntaIA):
    try:
        resposta = perguntar_llm(dados.pergunta)

        return {
            "pergunta": dados.pergunta,
            "resposta": resposta
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar LLM: {str(erro)}"
        )