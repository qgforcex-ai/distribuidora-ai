import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.llm import perguntar_llm, TOOLS
from app.ai.tools import ranking_clientes
from app.database import get_db


router = APIRouter(
    prefix="/ia",
    tags=["IA"]
)


class PerguntaIA(BaseModel):
    pergunta: str


@router.post("/perguntar")
def perguntar(
    dados: PerguntaIA,
    db: Session = Depends(get_db)
):

    try:

        # ------------------------------------------------
        # 1. Pergunta do usuário
        # ------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": (
                    "Você é o assistente de inteligência comercial "
                    "da Distribuidora AI. "
                    "Quando a pergunta depender de dados de clientes "
                    "ou vendas, utilize as ferramentas disponíveis. "
                    "Nunca invente dados comerciais."
                )
            },
            {
                "role": "user",
                "content": dados.pergunta
            }
        ]

        # ------------------------------------------------
        # 2. Qwen decide se precisa de Tool
        # ------------------------------------------------

        resposta_modelo = perguntar_llm(
            messages,
            TOOLS
        )

        tool_calls = resposta_modelo.get("tool_calls", [])

        # ------------------------------------------------
        # 3. Não pediu ferramenta
        # ------------------------------------------------

        if not tool_calls:

            return {
                "pergunta": dados.pergunta,
                "resposta": resposta_modelo.get("content", ""),
                "usou_tool": False
            }

        # ------------------------------------------------
        # 4. Modelo pediu uma ferramenta
        # ------------------------------------------------

        messages.append(resposta_modelo)

        for tool_call in tool_calls:

            nome = tool_call["function"]["name"]
            argumentos = tool_call["function"]["arguments"]

            if nome == "ranking_clientes":

                resultado = ranking_clientes(
                    db=db,
                    data_inicio=argumentos["data_inicio"],
                    data_fim=argumentos["data_fim"]
                )

            else:

                resultado = {
                    "erro": f"Ferramenta desconhecida: {nome}"
                }

            # --------------------------------------------
            # 5. Resultado volta para o modelo
            # --------------------------------------------

            messages.append({
                "role": "tool",
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            })

        # ------------------------------------------------
        # 6. Qwen recebe os dados reais e responde
        # ------------------------------------------------

        resposta_final = perguntar_llm(messages)

        return {
            "pergunta": dados.pergunta,
            "resposta": resposta_final.get("content", ""),
            "usou_tool": True,
            "tool": tool_calls[0]["function"]["name"]
        }

    except Exception as erro:

        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )