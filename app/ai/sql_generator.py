import re

from app.ai.providers.factory import get_llm_provider
from app.ai.schema_catalog import SCHEMA_CATALOG
from app.ai.business_semantics import BUSINESS_SEMANTICS


def _extrair_sql(conteudo: str) -> str:
    conteudo = conteudo.strip()

    bloco_sql = re.search(
        r"```(?:sql|mysql)?\s*(.*?)```",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL
    )

    if bloco_sql:
        conteudo = bloco_sql.group(1).strip()

    inicio = re.search(
        r"\b(SELECT|WITH)\b",
        conteudo,
        flags=re.IGNORECASE
    )

    if inicio:
        conteudo = conteudo[inicio.start():].strip()

    if ";" in conteudo:
        conteudo = conteudo.split(";", 1)[0].strip() + ";"

    return conteudo.strip()


def gerar_sql(pergunta: str):

    provider = get_llm_provider()

    messages = [
        {
            "role": "system",
            "content": f"""
Você é um especialista em análise de dados e MySQL.

Transforme a pergunta do usuário em uma consulta SQL.

CATÁLOGO AUTORIZADO:

{SCHEMA_CATALOG}


REGRAS DE NEGÓCIO:

{BUSINESS_SEMANTICS}

REGRAS OBRIGATÓRIAS:

- Utilize somente tabelas existentes no catálogo.
- Utilize somente colunas existentes no catálogo.
- Gere somente consultas SELECT.
- Nunca utilize INSERT.
- Nunca utilize UPDATE.
- Nunca utilize DELETE.
- Nunca utilize DROP.
- Nunca utilize ALTER.
- Nunca utilize TRUNCATE.
- Nunca modifique dados.
- Utilize sintaxe MySQL.
- Utilize JOINs quando necessário.
- Não invente tabelas.
- Não invente colunas.
- Retorne somente o SQL.
- Não utilize markdown.
- Não utilize blocos ```sql.
- Não explique a consulta.
"""
        },
        {
            "role": "user",
            "content": pergunta
        }
    ]

    resposta = provider.chat(messages)

    return _extrair_sql(
        resposta.get("content", "")
    )
