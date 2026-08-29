import sqlglot
from sqlglot import exp


TABELAS_PERMITIDAS = {
    "clientes",
    "vendas",
    "itens_venda",
    "produtos",
}

LIMITE_MAXIMO = 500


class SQLGuardError(Exception):
    pass


def validar_sql(sql: str) -> dict:

    if not sql or not sql.strip():
        raise SQLGuardError(
            "A consulta SQL está vazia."
        )

    try:
        statements = sqlglot.parse(
            sql,
            read="mysql"
        )
    except Exception as erro:
        raise SQLGuardError(
            f"SQL inválido: {erro}"
        )

    # --------------------------------
    # Apenas uma instrução
    # --------------------------------

    if len(statements) != 1:
        raise SQLGuardError(
            "Apenas uma instrução SQL é permitida."
        )

    query = statements[0]

    # --------------------------------
    # Somente consultas SELECT
    # --------------------------------

    if not isinstance(query, exp.Query):
        raise SQLGuardError(
            "Somente consultas SELECT são permitidas."
        )

    # --------------------------------
    # Bloqueia operações de escrita
    # --------------------------------

    proibidos = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.TruncateTable,
    )

    for tipo in proibidos:

        if query.find(tipo):
            raise SQLGuardError(
                f"Operação não permitida: {tipo.__name__}"
            )

    # --------------------------------
    # Descobrir tabelas utilizadas
    # --------------------------------

    tabelas = {
        tabela.name.lower()
        for tabela in query.find_all(exp.Table)
    }

    tabelas_nao_permitidas = (
        tabelas - TABELAS_PERMITIDAS
    )

    if tabelas_nao_permitidas:

        raise SQLGuardError(
            "Tabela não autorizada: "
            + ", ".join(
                sorted(tabelas_nao_permitidas)
            )
        )

    # --------------------------------
    # Aplicar LIMIT
    # --------------------------------

    limit = query.args.get("limit")

    if limit is None:

        query = query.limit(
            LIMITE_MAXIMO
        )

    else:

        expression = limit.expression

        try:
            valor = int(expression.name)
        except (ValueError, TypeError, AttributeError):
            raise SQLGuardError(
                "LIMIT inválido."
            )

        if valor > LIMITE_MAXIMO:
            query.set(
                "limit",
                exp.Limit(
                    expression=exp.Literal.number(
                        LIMITE_MAXIMO
                    )
                )
            )

    sql_seguro = query.sql(
        dialect="mysql"
    )

    return {
        "valido": True,
        "sql_original": sql,
        "sql_seguro": sql_seguro,
        "tabelas": sorted(tabelas)
    }