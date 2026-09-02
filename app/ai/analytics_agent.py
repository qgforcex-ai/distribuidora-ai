import json
import os
import time

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


def _log_performance(timings):
    labels = [
        ("Provider", os.getenv("AI_PROVIDER", "ollama")),
        ("Planner", timings.get("planner")),
        ("SQL Generator", timings.get("sql_generator")),
        ("SQL Guard", timings.get("sql_guard")),
        ("SQL Executor", timings.get("sql_executor")),
        ("Resposta LLM", timings.get("resposta_llm")),
        ("TOTAL", timings.get("total")),
    ]

    for label, value in labels:
        if value is None:
            continue

        if isinstance(value, str):
            formatted = value
        else:
            formatted = f"{value:.3f}s"

        print(f"[PERF] {label:.<22} {formatted}")


def _tipo_resposta(plano):
    tipo = plano.get("tipo_resposta", "analise")

    if tipo not in ["lista", "analise"]:
        return "analise"

    return tipo


def perguntar_dados(
    pergunta: str,
    session_id: str
):
    inicio_total = time.perf_counter()
    timings = {}

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
    inicio = time.perf_counter()
    plano = analisar_intencao(pergunta_completa)
    timings["planner"] = time.perf_counter() - inicio
    tipo_resposta = _tipo_resposta(plano)

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

        timings["total"] = time.perf_counter() - inicio_total
        _log_performance(timings)

        return {
            "status": "precisa_esclarecimento",
            "session_id": session_id,
            "pergunta_original": pergunta_completa,
            "motivo": plano.get("motivo"),
            "pergunta": plano.get("pergunta")
        }
   


    # 1. IA transforma português em SQL
    inicio = time.perf_counter()
    sql_gerado = gerar_sql(pergunta_completa)
    timings["sql_generator"] = time.perf_counter() - inicio

    # 2. Código valida o SQL
    inicio = time.perf_counter()
    validacao = validar_sql(sql_gerado)
    timings["sql_guard"] = time.perf_counter() - inicio

    sql_seguro = validacao["sql_seguro"]

    # 3. Executa com usuário read-only
    inicio = time.perf_counter()
    resultado = executar_sql(sql_seguro)
    timings["sql_executor"] = time.perf_counter() - inicio

    if tipo_resposta == "lista":
        resumo = f"Foram encontrados {resultado['quantidade']} registros."
        timings["resposta_llm"] = "SKIPPED"
        timings["total"] = time.perf_counter() - inicio_total
        _log_performance(timings)

        return {
            "status": "ok",
            "tipo_resposta": "lista",
            "session_id": session_id,
            "pergunta": pergunta,
            "pergunta_interpretada": pergunta_completa,
            "sql_gerado": sql_gerado,
            "sql_executado": sql_seguro,
            "quantidade_registros": resultado["quantidade"],
            "total_registros": resultado["quantidade"],
            "resumo": resumo,
            "resposta": resumo,
            "dados": resultado["dados"]
        }

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

    inicio = time.perf_counter()
    resposta = provider.chat(messages)
    timings["resposta_llm"] = time.perf_counter() - inicio
    timings["total"] = time.perf_counter() - inicio_total
    _log_performance(timings)

    return {
        "status": "ok",
        "tipo_resposta": "analise",
        "session_id": session_id,
        "pergunta": pergunta,
        "pergunta_interpretada": pergunta_completa,
        "sql_gerado": sql_gerado,
        "sql_executado": sql_seguro,
        "quantidade_registros": resultado["quantidade"],
        "dados": resultado["dados"],
        "resposta": resposta.get("content", "")
    }
