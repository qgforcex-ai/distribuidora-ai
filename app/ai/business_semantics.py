BUSINESS_SEMANTICS = """
# MÉTRICAS E REGRAS DE NEGÓCIO

## FATURAMENTO

Faturamento representa o valor financeiro vendido.

Regra conceitual:

SUM(vendas.valor_total)

Exemplos de intenção:
- "quanto faturamos?"
- "maior faturamento"
- "faturamento por cliente"
- "faturamento por período"


## VOLUME

Volume representa a quantidade física vendida.

Regra conceitual:

SUM(itens_venda.quantidade)

Não confundir volume com quantidade de SKUs distintos.

Exemplos:
- "quantas unidades vendemos?"
- "qual o volume vendido?"
- "volume de cerveja"


## COBERTURA DE PRODUTO

Cobertura representa quantos clientes distintos
compraram o produto no período analisado.

Regra conceitual:

COUNT(DISTINCT vendas.cliente_id)

Um cliente conta apenas uma vez no período,
independentemente da quantidade comprada ou
do número de compras.


## CESTA DE PRODUTOS

Uma cesta é um agrupamento comercial de produtos/SKUs.

Um produto pode pertencer a várias cestas.

Exemplo:

Brahma Lata 269 pode pertencer simultaneamente a:

- Cerveja Lata
- Cerveja Total

A relação Produto x Cesta é muitos-para-muitos.


## COBERTURA DE CESTA

Um cliente cobre uma cesta quando compra pelo menos
um SKU pertencente à cesta no período analisado.

O cliente conta apenas uma vez na cobertura da cesta,
mesmo que compre vários produtos diferentes da cesta.

Regra conceitual:

COUNT(DISTINCT cliente_id)

considerando clientes que compraram pelo menos
um produto pertencente à cesta.


## DISTRIBUIÇÃO

Distribuição NÃO representa volume físico vendido.

Distribuição mede a quantidade de SKUs distintos
da cesta comprados pelos clientes no período.

Para distribuição mensal, cada combinação:

CLIENTE + SKU + MÊS

pode contribuir no máximo 1 vez.

Compras repetidas do mesmo SKU pelo mesmo cliente
dentro do mesmo mês NÃO aumentam a distribuição.

Exemplo:

Cliente A em agosto:

Primeira visita:
- Spaten Long Neck
- Skol Lata

Distribuição acumulada = 2

Segunda visita:
- Spaten Long Neck
- Bud Lata

Spaten já foi contabilizada para esse cliente no mês.

Distribuição final = 3.


## DIFERENÇA ENTRE MÉTRICAS

Cobertura:
quantidade de clientes distintos positivados.

Distribuição:
soma dos SKUs distintos por cliente no período.

Volume:
quantidade física vendida.

Faturamento:
valor financeiro vendido.


## AMBIGUIDADE

Nunca escolha uma métrica arbitrariamente quando
a pergunta permitir mais de uma interpretação relevante.

Exemplo:

"Como está Cerveja Lata?"

Essa pergunta é ambígua.

Pode significar:
- cobertura
- distribuição
- volume
- faturamento

O agente deve pedir esclarecimento antes de executar.

Exemplo de pergunta:

"Você quer analisar cobertura, distribuição,
volume ou faturamento de Cerveja Lata?"
"""