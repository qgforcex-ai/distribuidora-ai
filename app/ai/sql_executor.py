import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text


AI_DB_HOST = os.getenv("AI_DB_HOST", "mysql")
AI_DB_PORT = os.getenv("AI_DB_PORT", "3306")
AI_DB_NAME = os.getenv("AI_DB_NAME", "distribuidora")
AI_DB_USER = os.getenv("AI_DB_USER", "agente_readonly")
AI_DB_PASSWORD = os.getenv("AI_DB_PASSWORD")


if not AI_DB_PASSWORD:
    raise RuntimeError(
        "AI_DB_PASSWORD não configurada."
    )


#DATABASE_URL = (
#    f"mysql+pymysql://{AI_DB_USER}:{AI_DB_PASSWORD}"
#    f"@{AI_DB_HOST}:{AI_DB_PORT}/{AI_DB_NAME}"
#   )


AI_DB_PASSWORD_ENCODED = quote_plus(AI_DB_PASSWORD)

DATABASE_URL = (
    f"mysql+pymysql://{AI_DB_USER}:{AI_DB_PASSWORD_ENCODED}"
    f"@{AI_DB_HOST}:{AI_DB_PORT}/{AI_DB_NAME}"
)


engine_readonly = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def executar_sql(sql: str):

    with engine_readonly.connect() as conexao:

        resultado = conexao.execute(
            text(sql)
        )

        colunas = list(resultado.keys())

        linhas = [
            dict(linha._mapping)
            for linha in resultado
        ]

    return {
        "colunas": colunas,
        "dados": linhas,
        "quantidade": len(linhas)
    }