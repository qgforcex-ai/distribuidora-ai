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

REGRAS COMERCIAIS OBRIGATÓRIAS PARA SQL:

- Para métricas comerciais oficiais de vendas, sempre filtre
  vendas.origem = 'BASE_VENDA', mesmo que o usuário não cite a origem.
- Para faturamento, use SUM(itens_venda.subtotal),
  vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.
- Para "quanto vendemos" sem outra unidade explícita, trate como
  faturamento.
- Para volume comercial, use SUM(itens_venda.volume_hl).
  Não use SUM(itens_venda.quantidade) como volume.
- Para quantidade/unidades, use SUM(itens_venda.quantidade).
- Para distribuição, use COUNT(DISTINCT vendas.cliente_id, itens_venda.produto_id)
  com vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.
- Para cobertura, gere uma consulta que retorne compradores, universo_total
  e cobertura_percentual. Cobertura é compradores / universo_total * 100.
- Para comparar "melhor cobertura", ordene por cobertura_percentual,
  não por compradores absolutos.
- Revenda total considera todos os clientes com venda no período.
  Não filtre clientes.base_pdv_atual para revenda total, total geral,
  faturamento total, volume total, distribuição total ou cesta na revenda.
- RN é dimensão da Base PDV atual. Quando houver filtro por RN,
  use clientes.base_pdv_atual = TRUE e clientes.rn = o RN solicitado.
- Cesta é filtro de produtos. Para filtrar cesta, use:
  cestas -> cesta_produto_itens -> produtos -> itens_venda.
  Uma cesta na revenda não deve filtrar clientes.base_pdv_atual.
- Resolva nomes de cesta pelo cadastro cestas.nome. Se a pergunta usar
  variações como "NAB total" ou "total NAB", procure correspondência
  inequívoca pelo nome da cesta, sem inventar cestas inexistentes.
- Se usar apelidos nas tabelas, mantenha os filtros obrigatórios
  equivalentes nos apelidos correspondentes.
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
