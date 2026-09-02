BUSINESS_SEMANTICS = """
# METRICAS E REGRAS DE NEGOCIO

## BASE PDV E UNIVERSO COMERCIAL

A tabela clientes representa o cadastro mestre de clientes conhecidos.
Clientes da Base PDV atual sao identificados por:

clientes.base_pdv_atual = TRUE

A Base PDV nao possui periodo.
Periodos pertencem as vendas.

Um cliente fora da Base PDV atual pode continuar existindo historicamente
nas vendas da revenda. Ele entra em faturamento/volume total da revenda,
mas nao entra em metricas que dependem da Base PDV atual, RN atual,
carteira atual ou cobertura da base atual.

RN, cidade, bairro, status e demais dimensoes comerciais devem
ser obtidos da tabela clientes:

- clientes.rn
- clientes.cidade
- clientes.bairro
- clientes.status_cliente

Futuramente poderao existir snapshots JSON da Base PDV para
fotografia historica/auditoria. Esses snapshots nao fazem parte
das consultas operacionais atuais.


## FATURAMENTO

Faturamento representa o valor financeiro vendido.
Somente operacao 1 entra em faturamento.

Regra conceitual:

SUM(itens_venda.subtotal)
WHERE vendas.operacao = 1

Exemplos de intencao:
- "quanto faturamos?"
- "maior faturamento"
- "faturamento por cliente"
- "faturamento por periodo"

Para analises por RN, cesta, produto, cidade, bairro ou status,
use clientes.base_pdv_atual = TRUE quando a pergunta depender da
Base PDV atual. Para faturamento total da revenda, nao aplique esse filtro.

Exemplo conceitual:

clientes
WHERE base_pdv_atual = TRUE
  AND rn = '104'
      ->
vendas
WHERE periodo = '2026-08-01'
  AND operacao = 1
      ->
itens_venda
      ->
produtos
      ->
cesta_produto_itens
      ->
cestas
      ->
SUM(itens_venda.subtotal)


## VOLUME HL

Volume comercial significa hectolitros (HL).
Nao use SUM(itens_venda.quantidade) como volume comercial.

Volume vendido em HL:

SUM(itens_venda.volume_hl)
WHERE vendas.operacao = 1

Volume bonificado em HL:

SUM(itens_venda.volume_hl)
WHERE vendas.operacao = 2

Volume movimentado em HL:

SUM(itens_venda.volume_hl)
WHERE vendas.operacao IN (1, 2)

Quantidade de SKU/unidades:

SUM(itens_venda.quantidade)

Nao confundir volume HL com quantidade de SKU/unidades
nem com quantidade de SKUs distintos.

Exemplos:
- "quantas unidades vendemos?"
- "qual o volume vendido?"
- "volume de cerveja"


## COBERTURA DE PRODUTO

Cobertura representa quantos PDVs distintos da Base PDV atual
compraram o produto no periodo analisado.

Regra conceitual:

COUNT(DISTINCT clientes.id)

sempre com clientes.base_pdv_atual = TRUE.

Um PDV conta apenas uma vez no periodo,
independentemente da quantidade comprada ou
do numero de compras.


## CESTA DE PRODUTOS

Uma cesta e um agrupamento comercial de produtos/SKUs.

Um produto pode pertencer a varias cestas.

Exemplo:

Brahma Lata 269 pode pertencer simultaneamente a:

- Cerveja Lata
- Cerveja Total

A relacao Produto x Cesta e muitos-para-muitos.


## COBERTURA DE CESTA

Um PDV cobre uma cesta quando compra pelo menos
um SKU pertencente a cesta no periodo analisado.

O PDV conta apenas uma vez na cobertura da cesta,
mesmo que compre varios produtos diferentes da cesta.

Regra conceitual:

COUNT(DISTINCT clientes.id)

considerando PDVs da Base PDV atual que compraram pelo menos
um produto pertencente a cesta.
Use clientes.base_pdv_atual = TRUE.

Cobertura deve manter separados tres conceitos:

- Cobertura absoluta: PDVs da Base PDV atual que compraram.
- Base: total de PDVs da Base PDV atual no universo solicitado.
- Cobertura percentual: cobertura absoluta / base atual * 100.


## DISTRIBUICAO

Distribuicao NAO representa volume fisico vendido.

Distribuicao mede a quantidade de SKUs distintos
da cesta comprados pelos PDVs no periodo.

Para distribuicao mensal, cada combinacao:

PDV + SKU + MES

pode contribuir no maximo 1 vez.

Compras repetidas do mesmo SKU pelo mesmo PDV
dentro do mesmo mes NAO aumentam a distribuicao.

Exemplo:

PDV 550 em agosto:

Primeira visita:
- Spaten Long Neck
- Skol Lata

Distribuicao acumulada = 2

Segunda visita:
- Spaten Long Neck
- Bud Lata

Spaten ja foi contabilizada para esse PDV no mes.

Distribuicao final = 3.

Regra conceitual:

Base PDV atual
-> clientes.base_pdv_atual = TRUE
-> filtra universo/RN/cidade/status quando solicitado
-> vendas pelo periodo
-> operacao conforme a metrica
-> produtos/cesta
-> COUNT DISTINCT produto por PDV
-> SUM


## DIFERENCA ENTRE METRICAS

Cobertura:
quantidade de PDVs distintos positivados.

Distribuicao:
soma dos SKUs distintos por PDV no periodo.

Volume:
volume comercial em HL.

Quantidade:
soma de itens_venda.quantidade.

Faturamento:
valor financeiro vendido.


## AMBIGUIDADE

Nunca escolha uma metrica arbitrariamente quando
a pergunta permitir mais de uma interpretacao relevante.

Exemplo:

"Como esta Cerveja Lata?"

Essa pergunta e ambigua.

Pode significar:
- cobertura
- distribuicao
- volume
- faturamento

O agente deve pedir esclarecimento antes de executar.

Exemplo de pergunta:

"Voce quer analisar cobertura, distribuicao,
volume ou faturamento de Cerveja Lata?"
"""
