import json

from app.ai.providers.factory import get_llm_provider
from app.ai.sql_generator import gerar_sql
from app.ai.sql_guard import validar_sql
from app.ai.sql_executor import executar_sql
from app.ai.planner import analisar_intencao

from app.ai.conversation_memory import (
    buscar_contexto,
    salvar_contexto,
    limpar_contexto,
)


def perguntar_dados(
    pergunta: str,
    session_id: str
):

    # Busca uma conversa pendente no Redis
    contexto = buscar_contexto(session_id)

    pergunta_completa = pergunta

    # Se o agente estava aguardando uma resposta,
    # junta a pergunta anterior com o esclarecimento atual
    if contexto:
        if contexto.get("status") == "aguardando_esclarecimento":

            pergunta_original = contexto["pergunta_original"]

            pergunta_completa = f"""
Pergunta original:
{pergunta_original}

Esclarecimento fornecido pelo usuário:
{pergunta}
"""

            limpar_contexto(session_id)

    # Planner analisa a pergunta já com o contexto
    plano = analisar_intencao(pergunta_completa)

    # Ainda existe alguma ambiguidade importante?
    if plano["status"] == "precisa_esclarecimento":

        salvar_contexto(
            session_id,
            {
                "status": "aguardando_esclarecimento",
                "pergunta_original": pergunta_completa,
                "pergunta_esclarecimento": plano.get("pergunta")
            }
        )

        return {
            "status": "precisa_esclarecimento",
            "session_id": session_id,
            "pergunta_original": pergunta_completa,
            "motivo": plano.get("motivo"),
            "pergunta": plano.get("pergunta")
        }
   


    # 1. IA transforma português em SQL
    sql_gerado = gerar_sql(pergunta_completa)

    # 2. Código valida o SQL
    validacao = validar_sql(sql_gerado)

    sql_seguro = validacao["sql_seguro"]

    # 3. Executa com usuário read-only
    resultado = executar_sql(sql_seguro)

    # 4. IA interpreta os dados
    provider = get_llm_provider()

    messages = [
        {
            "role": "system",
            "content": (
                "Você é um analista comercial da Distribuidora AI. "
                "Responda utilizando exclusivamente os dados fornecidos. "
                "Não invente valores, clientes ou informações. "
                "Responda em português de forma clara e objetiva."
            )
        },
        {
            "role": "user",
            "content": f"""
Pergunta do usuário:

{pergunta_completa}

Resultado obtido no banco de dados:

{json.dumps(resultado, ensure_ascii=False, default=str)}

Responda à pergunta utilizando esses dados.
"""
        }
    ]

    resposta = provider.chat(messages)

    return {
        "session_id": session_id,
        "pergunta": pergunta,
        "pergunta_interpretada": pergunta_completa,
        "sql_gerado": sql_gerado,
        "sql_executado": sql_seguro,
        "quantidade_registros": resultado["quantidade"],
        "dados": resultado["dados"],
        "resposta": resposta.get("content", "")
    }