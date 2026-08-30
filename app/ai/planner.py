import json

from app.ai.providers.factory import get_llm_provider
from app.ai.schema_catalog import SCHEMA_CATALOG
from app.ai.business_semantics import BUSINESS_SEMANTICS


def analisar_intencao(pergunta: str):

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

1. Se a pergunta estiver suficientemente clara:
   status = "pronto"

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

Exemplo:

Pergunta:
"Quais são os meus melhores clientes?"

Resposta:
{{
    "status": "precisa_esclarecimento",
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