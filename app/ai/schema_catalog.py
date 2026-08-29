SCHEMA_CATALOG = """
BANCO: Distribuidora AI

OBJETIVO:
Banco de dados comercial contendo clientes, produtos,
vendas realizadas e itens pertencentes às vendas.


TABELA: clientes

Descrição:
Cadastro dos clientes da distribuidora.

Colunas:

- id
  Tipo: INT
  Chave primária.
  Identificador único do cliente.

- nome
  Tipo: VARCHAR(150)
  Nome do cliente.

- cidade
  Tipo: VARCHAR(100)
  Cidade onde o cliente está cadastrado.

- limite_credito
  Tipo: DECIMAL(10,2)
  Limite de crédito cadastrado para o cliente.


TABELA: vendas

Descrição:
Cabeçalho das vendas realizadas pela distribuidora.
Cada venda pertence a um cliente.

Colunas:

- id
  Tipo: INT
  Chave primária.
  Identificador único da venda.

- cliente_id
  Tipo: INT
  Chave estrangeira para clientes.id.
  Identifica o cliente responsável pela compra.

- data_venda
  Tipo: DATETIME
  Data e hora em que a venda foi realizada.

- valor_total
  Tipo: DECIMAL(10,2)
  Valor financeiro total da venda.
  Para análises de faturamento, utilize este campo.


TABELA: itens_venda

Descrição:
Itens/produtos pertencentes às vendas.

Colunas:

- id
  Tipo: INT
  Chave primária.

- venda_id
  Tipo: INT
  Chave estrangeira para vendas.id.

- produto_id
  Tipo: INT
  Chave estrangeira para produtos.id.

- quantidade
  Tipo: INT
  Quantidade vendida daquele produto.

- preco_unitario
  Tipo: DECIMAL(10,2)
  Preço unitário praticado naquela venda.

- subtotal
  Tipo: DECIMAL(10,2)
  Valor total daquele item da venda.


TABELA: produtos

Descrição:
Cadastro dos produtos comercializados pela distribuidora.

Colunas:

- id
  Tipo: INT
  Chave primária.

- codigo
  Tipo: VARCHAR(50)
  Código único do produto.

- descricao
  Tipo: VARCHAR(200)
  Nome ou descrição comercial do produto.

- categoria
  Tipo: VARCHAR(100)
  Categoria à qual o produto pertence.

- preco
  Tipo: DECIMAL(10,2)
  Preço cadastrado atualmente para o produto.


RELACIONAMENTOS:

clientes.id = vendas.cliente_id

vendas.id = itens_venda.venda_id

produtos.id = itens_venda.produto_id


REGRAS DE NEGÓCIO PARA ANÁLISES:

1. Para calcular faturamento geral, utilize vendas.valor_total.

2. Para calcular faturamento por cliente, relacione:
   clientes -> vendas
   e some vendas.valor_total.

3. Para análises de produtos, utilize:
   vendas -> itens_venda -> produtos.

4. Para calcular quantidade de produtos vendidos,
   utilize itens_venda.quantidade.

5. Para calcular valor vendido por produto ou categoria,
   utilize itens_venda.subtotal.

6. Não utilize produtos.preco para calcular faturamento histórico.
   produtos.preco representa o preço cadastrado do produto.
   O preço efetivamente praticado na venda está em
   itens_venda.preco_unitario.

7. Um cliente pode possuir várias vendas.

8. Uma venda pode possuir vários itens.

9. Um produto pode aparecer em várias vendas.
"""