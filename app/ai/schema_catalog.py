SCHEMA_CATALOG = """
BANCO: Distribuidora AI

OBJETIVO:
Banco de dados comercial contendo a Base PDV atual,
produtos, cestas, vendas historicas e itens pertencentes as vendas.


TABELA: clientes

Descricao:
Cadastro mestre de todos os clientes conhecidos da distribuidora:
clientes da Base PDV atual, clientes historicos e clientes encontrados
nas vendas. Cada cliente possui codigo_pdv unico quando vier das bases
comerciais.

Colunas:

- id
  Tipo: INT
  Chave primaria.
  Identificador interno do cliente.

- codigo_pdv
  Tipo: VARCHAR(50)
  Codigo comercial unico do PDV.
  Deve ser usado para cruzar arquivos externos de Base PDV e vendas.

- nome
  Tipo: VARCHAR(150)
  Nome fantasia ou nome comercial principal do PDV.

- cidade
  Tipo: VARCHAR(100)
  Cidade atual do PDV.

- bairro
  Tipo: VARCHAR(150)
  Bairro atual do PDV.

- status_cliente
  Tipo: VARCHAR(50)
  Status cadastral/comercial atual do PDV.

- rn
  Tipo: VARCHAR(20)
  RN/carteira comercial atual do PDV.

- proxima_visita
  Tipo: DATE
  Proxima visita prevista para o PDV, quando existir.

- base_pdv_atual
  Tipo: BOOLEAN
  Indica se o cliente pertence atualmente a Base PDV operacional.

- limite_credito
  Tipo: DECIMAL(10,2)
  Limite de credito cadastrado para o cliente.


TABELA: vendas

Descricao:
Fato analitico de vendas.
Vendas sao historicas e possuem periodo. A Base PDV nao possui periodo.
Para metricas comerciais oficiais, a fonte importada oficial e:
vendas.origem = 'BASE_VENDA'.

Colunas:

- id
  Tipo: INT
  Chave primaria.
  Identificador da venda/fato.

- cliente_id
  Tipo: INT
  Chave estrangeira para clientes.id.

- periodo
  Tipo: DATE
  Periodo de referencia da venda, gravado como o primeiro dia do mes.
  Exemplo: agosto de 2026 = 2026-08-01.

- data_venda
  Tipo: DATETIME
  Data da venda quando existir. Pode ser nula para fatos mensais
  importados sem data real de pedido.

- valor_total
  Tipo: DECIMAL(10,2)
  Valor financeiro total da venda/fato.

- operacao
  Tipo: INT
  Operacao da venda mensal.
  1 = VENDA.
  2 = BONIFICACAO.

- origem
  Tipo: VARCHAR(50)
  Origem da carga ou do registro.

- importacao_id
  Tipo: INT
  Chave estrangeira opcional para importacoes.id.


TABELA: itens_venda

Descricao:
Itens/produtos pertencentes a venda/fato.
Para cargas mensais, a granularidade prevista e venda mensal + produto.

Colunas:

- id
  Tipo: INT
  Chave primaria.

- venda_id
  Tipo: INT
  Chave estrangeira para vendas.id.

- produto_id
  Tipo: INT
  Chave estrangeira para produtos.id.

- quantidade
  Tipo: DECIMAL(15,4)
  Quantidade de SKU/unidades vendidas ou bonificadas.

- fator_hl
  Tipo: DECIMAL(15,6)
  Fator de conversao para hectolitros informado na Base Venda.

- volume_hl
  Tipo: DECIMAL(15,6)
  Volume comercial em hectolitros informado na Base Venda.

- preco_unitario
  Tipo: DECIMAL(15,6)
  Preco unitario calculado/praticado para o item.

- subtotal
  Tipo: DECIMAL(15,2)
  Valor total daquele produto na venda/fato.


TABELA: produtos

Descricao:
Cadastro dos produtos comercializados pela distribuidora.

Colunas:

- id
  Tipo: INT
  Chave primaria.

- codigo
  Tipo: VARCHAR(50)
  Codigo unico do produto.

- descricao
  Tipo: VARCHAR(200)
  Nome ou descricao comercial do produto.

- categoria
  Tipo: VARCHAR(100)
  Categoria cadastral do produto.

- preco
  Tipo: DECIMAL(10,2)
  Preco cadastrado atualmente para o produto.

- fator_hl
  Tipo: DECIMAL(15,6)
  Fator HL cadastral atual do SKU, quando conhecido.


TABELA: cestas

Descricao:
Cadastro das cestas ou agrupamentos comerciais de produtos.
Uma cesta representa um conjunto de produtos/SKUs utilizado
nas analises comerciais da distribuidora.

Colunas:

- id
  Tipo: INT
  Chave primaria.

- nome
  Tipo: VARCHAR(150)
  Nome comercial da cesta.

- tipo
  Tipo: VARCHAR(50)
  Tipo ou classificacao da cesta.


TABELA: cesta_produto_itens

Descricao:
Tabela associativa entre produtos e cestas.
Representa a relacao muitos-para-muitos entre produtos e cestas.
A combinacao cesta_id + produto_id e unica.

Colunas:

- id
  Tipo: INT
  Chave primaria.

- cesta_id
  Tipo: INT
  Chave estrangeira para cestas.id.

- produto_id
  Tipo: INT
  Chave estrangeira para produtos.id.


TABELA: importacoes

Descricao:
Controle de cargas/importacoes administrativas.

Colunas:

- id
  Tipo: INT
  Chave primaria.

- tipo
  Tipo: VARCHAR(50)
  Tipo da importacao. Exemplos: BASE_PDV, BASE_VENDA.

- periodo
  Tipo: DATE
  Periodo associado a importacao quando a base importada for historica.
  Para BASE_PDV operacional atual, periodo deve ser NULL.

- arquivo_nome
  Tipo: VARCHAR(255)
  Nome do arquivo importado.

- arquivo_hash
  Tipo: VARCHAR(64)
  Hash do arquivo importado para auditoria.

- status
  Tipo: VARCHAR(30)
  Status da importacao.

- linhas_lidas
  Tipo: INT

- linhas_importadas
  Tipo: INT

- erros
  Tipo: INT

- created_at
  Tipo: DATETIME


RELACIONAMENTOS:

clientes.id = vendas.cliente_id

importacoes.id = vendas.importacao_id

vendas.id = itens_venda.venda_id

produtos.id = itens_venda.produto_id

cestas.id = cesta_produto_itens.cesta_id

produtos.id = cesta_produto_itens.produto_id


REGRAS DE NEGOCIO PARA ANALISES:

1. Consulta total da revenda deve considerar todos os clientes em vendas.
   Nao filtre clientes.base_pdv_atual quando a pergunta for total geral
   da empresa/revenda, faturamento total, volume total, distribuicao total
   ou cesta na revenda.

2. Para filtrar RN, cidade, bairro, status ou carteira comercial,
   utilize clientes.base_pdv_atual = TRUE e os campos atuais em clientes.
   RN representa a Base PDV atual, nao a revenda total.

3. Periodo pertence a vendas. A tabela clientes nao possui periodo.

4. Para cruzar Base PDV e vendas, utilize:
   clientes -> vendas.

5. Para analises de produtos ou cestas, utilize:
   vendas -> itens_venda -> produtos -> cesta_produto_itens -> cestas.

6. Para calcular faturamento por produto/cesta, utilize itens_venda.subtotal
   e filtre vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.

7. Para calcular volume vendido em HL, utilize itens_venda.volume_hl
   e filtre vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.

8. Para calcular volume bonificado em HL, utilize itens_venda.volume_hl
   e filtre vendas.operacao = 2 e vendas.origem = 'BASE_VENDA'.

9. Para calcular volume movimentado em HL, utilize itens_venda.volume_hl
   e filtre vendas.operacao IN (1, 2) e vendas.origem = 'BASE_VENDA'.

10. Para calcular quantidade de SKU/unidades, utilize itens_venda.quantidade.
    Para quantidade de venda oficial, use vendas.origem = 'BASE_VENDA'.

11. Para volume de cesta/grupo, filtre os produtos pela cesta e some
    itens_venda.volume_hl.

12. Nao use SUM(itens_venda.quantidade) como volume comercial.
    Volume comercial significa HL.

13. Para cobertura, retorne compradores, base total e percentual.
    Numerador: PDVs da Base PDV atual que compraram pelo menos um produto
    do filtro no periodo, com clientes.base_pdv_atual = TRUE,
    vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.
    Denominador: total de PDVs da Base PDV atual no universo solicitado.

14. Para base de cobertura, conte todos os PDVs da Base PDV atual
   que pertencem ao universo solicitado.

15. Para cobertura percentual:
    cobertura absoluta / base atual * 100.
    Para comparar melhor cobertura, compare esse percentual.

16. Para distribuicao, conte combinacoes distintas cliente + produto
    compradas no periodo e no universo solicitado:
    vendas.operacao = 1 e vendas.origem = 'BASE_VENDA'.
    Em MySQL, use COUNT(DISTINCT vendas.cliente_id, itens_venda.produto_id).
    Cesta e filtro de produto, nao filtro de cliente.

17. Nao utilize produtos.categoria como substituto para cestas.
    As associacoes oficiais estao em cesta_produto_itens.

18. Produtos podem existir sem pertencer a cesta. Eles participam de
    faturamento total e volume total, mas nao entram em filtros de cesta.

19. Nao crie metricas fixas na Base PDV, como faturamento_cerveja,
    cobertura_cerveja ou distribuicao_cerveja. Essas metricas sao
    calculadas por consulta.

20. A tabela base_pdv_periodos e uma estrutura legada temporaria.
    Ela nao deve ser usada em consultas operacionais do agente.

21. Futuramente poderao existir snapshots JSON da Base PDV para
    fotografia historica/auditoria. Esses snapshots nao fazem parte
    do modelo operacional atual.

22. "Quanto vendemos" sem unidade/metrica explicita deve ser interpretado
    como faturamento, usando SUM(itens_venda.subtotal), operacao = 1
    e origem = 'BASE_VENDA'.

23. Se o usuario usar "volume" no contexto comercial, use volume HL:
    SUM(itens_venda.volume_hl). Nao substitua por SUM(quantidade).

24. Area 400 historicamente concentra aproximadamente 85% do faturamento
    medio e reune super clientes. Esse percentual e apenas contexto:
    para qualquer periodo especifico, calcule nos dados do periodo.
"""
