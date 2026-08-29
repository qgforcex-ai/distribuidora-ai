import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.providers.factory import get_llm_provider
from app.ai.tools import TOOLS
from app.ai.sql_generator import gerar_sql

from app.database import get_db

from app.ai.sql_guard import (
    validar_sql,
    SQLGuardError
)


router = APIRouter(
    prefix="/ia",
    tags=["IA"]
)


class PerguntaIA(BaseModel):
    pergunta: str


class TesteSQL(BaseModel):
    sql: str


@router.post("/perguntar")
def perguntar(
    dados: PerguntaIA,
    db: Session = Depends(get_db)
):

    try:

        # ------------------------------------------------
        # 1. Carrega o provider configurado
        # ------------------------------------------------

        provider = get_llm_provider()

        # ------------------------------------------------
        # 2. Monta a conversa
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
        # 3. IA decide se precisa utilizar uma Tool
        # ------------------------------------------------

        resposta_modelo = provider.chat(
            messages,
            TOOLS
        )

        tool_calls = resposta_modelo.get(
            "tool_calls",
            []
        )

        # ------------------------------------------------
        # 4. Não precisa de Tool
        # ------------------------------------------------

        if not tool_calls:

            return {
                "pergunta": dados.pergunta,
                "resposta": resposta_modelo.get(
                    "content",
                    ""
                ),
                "usou_tool": False
            }

        # ------------------------------------------------
        # 5. IA solicitou uma Tool
        # ------------------------------------------------

        messages.append(resposta_modelo)

        for tool_call in tool_calls:

            nome = tool_call["function"]["name"]

            argumentos = tool_call[
                "function"
            ]["arguments"]

            # --------------------------------------------
            # Executa ranking_clientes
            # --------------------------------------------

            if nome == "ranking_clientes":

                resultado = ranking_clientes(
                    db=db,
                    data_inicio=argumentos["data_inicio"],
                    data_fim=argumentos["data_fim"]
                )

            else:

                resultado = {
                    "erro": (
                        f"Ferramenta desconhecida: {nome}"
                    )
                }

            # --------------------------------------------
            # Resultado da Tool volta para a IA
            # --------------------------------------------

            messages.append({
                "role": "tool",
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            })

        # ------------------------------------------------
        # 6. IA interpreta o resultado verdadeiro
        # ------------------------------------------------

        resposta_final = provider.chat(
            messages
        )

        return {
            "pergunta": dados.pergunta,
            "resposta": resposta_final.get(
                "content",
                ""
            ),
            "usou_tool": True,
            "tool": tool_calls[0][
                "function"
            ]["name"]
        }

    except Exception as erro:

        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )

@router.post("/gerar-sql")
def gerar_sql_teste(dados: PerguntaIA):

    try:

        sql = gerar_sql(dados.pergunta)

        return {
            "pergunta": dados.pergunta,
            "sql": sql,
            "executado": False
        }

    except Exception as erro:

        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )    



@router.post("/validar-sql")
def validar_sql_teste(dados: TesteSQL):

    try:

        resultado = validar_sql(
            dados.sql
        )

        return resultado

    except SQLGuardError as erro:

        return {
            "valido": False,
            "erro": str(erro)
        }            