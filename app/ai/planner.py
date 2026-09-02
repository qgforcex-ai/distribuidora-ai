import json
import re

from app.ai.providers.factory import get_llm_provider
from app.ai.schema_catalog import SCHEMA_CATALOG
from app.ai.business_semantics import BUSINESS_SEMANTICS


PADROES_METRICAS_TEMPORAIS = [
    r"\bcobertura\b",
    r"\bdistribuição\b",
    r"\bdistribuicao\b",
    r"\bvolume\b",
    r"\bfaturamento\b",
    r"\bquanto\s+vendemos\b",
    r"\bdesempenho\b",
    r"\bperformance\b",
    r"\bcompar(ar|e|ação|acao)\b",
    r"\bqueda\b",
    r"\bcrescimento\b",
    r"\bevolução\b",
    r"\bevolucao\b",
    r"\b(número|numero|quant[oa]s?|quantidade|qtd|total)\s+de\s+(vendas|pedidos)\b",
    r"\bquant[oa]s?\s+(vendas|pedidos)\b",
]

PADROES_PERIODO = [
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b20\d{2}\b",
    r"\b(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b",
    r"\b(hoje|ontem|semana|mês|mes|ano|trimestre|bimestre|quinzena)\b",
    r"\b(últimos|ultimos|últimas|ultimas|periodo|período)\b",
    r"\b(mês passado|mes passado|mês atual|mes atual|este mês|este mes|esse mês|esse mes)\b",
]


def _solicitar_periodo_se_necessario(pergunta: str):
    texto = pergunta.lower()

    possui_metrica_temporal = any(
        re.search(padrao, texto)
        for padrao in PADROES_METRICAS_TEMPORAIS
    )

    if not possui_metrica_temporal:
        return None

    possui_periodo = any(
        re.search(padrao, texto)
        for padrao in PADROES_PERIODO
    )

    if possui_periodo:
        return None

    return {
        "status": "precisa_esclarecimento",
        "tipo_resposta": "analise",
        "motivo": "Não foi definido o período da métrica solicitada.",
        "pergunta": "Qual período você deseja analisar?"
    }


def analisar_intencao(pergunta: str):

    periodo_pendente = _solicitar_periodo_se_necessario(pergunta)
    if periodo_pendente:
        return periodo_pendente

    provider = get_llm_provider()

    messages = [
        {
            "role": "system",
            "content": f"""
Você é o planejador de um agente de análise comercial.

Sua função NÃO é responder à pergunta e NÃO é gerar SQL.

Analise se existem informações suficientes para executar
uma análise correta no banco de dados.

CATÁLOGO DISPONÍVEL:

{SCHEMA_CATALOG}

REGRAS DE NEGÓCIO:

{BUSINESS_SEMANTICS}

REGRAS:

IMPORTANTE SOBRE IDs E DADOS TÉCNICOS:

Nunca peça ao usuário IDs internos do banco de dados quando
eles puderem ser descobertos através das informações fornecidas.

O usuário não precisa conhecer:
- cliente_id
- produto_id
- cesta_id
- venda_id
- ou qualquer outra chave interna.

Se o usuário informar um nome, descrição, código comercial ou
outro identificador de negócio suficiente para localizar o registro,
considere a pergunta suficientemente especificada.

Exemplo:

"Quais produtos pertencem à cesta CERVEJA TOTAL?"

NÃO perguntar:
"Qual é o ID da cesta?"

A cesta deve ser localizada utilizando cestas.nome e os
relacionamentos disponíveis no catálogo.

Só solicite esclarecimento quando existir uma ambiguidade de negócio
que possa alterar significativamente a resposta e que não possa ser
resolvida consultando os dados disponíveis.

1. Se a pergunta estiver suficientemente clara:
   status = "pronto"

   Informe tambem:
   tipo_resposta = "lista" ou "analise"

2. Se existir uma ambiguidade que possa alterar
   significativamente o resultado:
   status = "precisa_esclarecimento"

3. Não peça esclarecimento para detalhes irrelevantes.

4. Nunca invente datas, períodos, clientes, produtos
   ou critérios importantes.

5. Quando pedir esclarecimento, faça uma pergunta curta
   e objetiva.

6. Se possível, apresente opções ao usuário.

Exemplo:

Pergunta:
"Qual cliente teve a maior queda?"

Resposta:
{{
    "status": "precisa_esclarecimento",
    "motivo": "Não foi definido o período de comparação.",
    "pergunta": "Você quer comparar mês a mês ou ano contra ano?"
}}

Exemplo:

Pergunta:
"Quais são os 5 clientes que mais compraram?"

Resposta:
{{
    "status": "pronto",
    "tipo_resposta": "analise",
    "motivo": null,
    "pergunta": null
}}

CLASSIFICAÇÃO DO TIPO DE RESPOSTA:

Use tipo_resposta = "lista" quando a intenção principal do usuário
for consultar, listar ou mostrar registros do banco, sem pedir
interpretação, comparação, ranking subjetivo, causa, tendência,
diagnóstico ou recomendação.

Exemplos de lista:
- "Quais produtos pertencem à cesta CERVEJA TOTAL?"
- "Liste os clientes de Caraguatatuba."
- "Quais cestas estão cadastradas?"
- "Mostre os produtos da cesta NAB."

Use tipo_resposta = "analise" quando a intenção exigir interpretação
dos dados, comparação, ranking, síntese analítica, explicação,
tendência, desempenho, queda, crescimento, distribuição, melhores,
piores ou qualquer conclusão de negócio.

Exemplos de analise:
- "Analise meus melhores clientes por faturamento."
- "Como está a distribuição da cesta CERVEJA TOTAL?"
- "Qual cliente teve a maior queda de faturamento?"
- "Compare o desempenho deste mês com o mês passado."

Exemplo:

Pergunta:
"Quais produtos pertencem à cesta CERVEJA TOTAL?"

Resposta:
{{
    "status": "pronto",
    "tipo_resposta": "lista",
    "motivo": null,
    "pergunta": null
}}

Exemplo:

Pergunta:
"Como está a distribuição da cesta CERVEJA TOTAL?"

Resposta:
{{
    "status": "pronto",
    "tipo_resposta": "analise",
    "motivo": null,
    "pergunta": null
}}


7. Não escolha sozinho métricas de negócio quando a pergunta
usar conceitos subjetivos ou relativos como:

- melhor
- pior
- maior desempenho
- menor desempenho
- crescimento
- queda
- evolução
- performance
- destaque
- relevância

Se houver mais de uma métrica válida para interpretar o conceito,
peça ao usuário que defina o critério.

Não peça esclarecimento quando o conceito relativo já vier junto
de uma métrica explícita. Nesses casos, use a métrica informada:

- "melhor cobertura" = maior cobertura percentual.
- "maior faturamento" = maior faturamento.
- "maior volume" = maior volume comercial em HL.
- "quanto vendemos" = faturamento, quando nao houver outra unidade
  explicitamente pedida.

No contexto comercial, "volume" significa volume em HL e nao exige
esclarecimento entre volume e quantidade.

Exemplo:

Pergunta:
"Quais são os meus melhores clientes?"

Resposta:
{{
    "status": "precisa_esclarecimento",
    "tipo_resposta": "analise",
    "motivo": "O critério para definir melhores clientes não foi informado.",
    "pergunta": "Melhores por faturamento, quantidade comprada ou frequência de compras?"
}}

8. Antes de marcar uma pergunta como "pronto", verifique:
"Existe mais de uma interpretação razoável que produziria
resultados significativamente diferentes?"

Se sim, use "precisa_esclarecimento".

Retorne SOMENTE JSON válido.
"""
        },
        {
            "role": "user",
            "content": pergunta
        }
    ]

    resposta = provider.chat(messages)

    conteudo = resposta.get("content", "").strip()

    # Alguns modelos podem devolver ```json
    conteudo = conteudo.replace("```json", "")
    conteudo = conteudo.replace("```", "")
    conteudo = conteudo.strip()

    return json.loads(conteudo)
