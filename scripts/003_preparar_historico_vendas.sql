-- Migration 003 - Preparar modelo definitivo para importacao historica de vendas
--
-- Regras:
-- clientes = cadastro mestre de todos os clientes conhecidos.
-- clientes.base_pdv_atual = TRUE apenas para PDVs pertencentes a Base PDV atual.
-- vendas sao historicas e distinguem operacao.
-- operacao = 1 -> VENDA
-- operacao = 2 -> BONIFICACAO

ALTER TABLE clientes
    ADD COLUMN base_pdv_atual BOOLEAN NOT NULL DEFAULT FALSE AFTER proxima_visita;

-- Backfill unico para o estado atual ja validado:
-- os 174 PDVs reais carregados na Base PDV atual possuem RN preenchido.
-- A partir desta migration, a regra operacional definitiva passa a ser
-- clientes.base_pdv_atual = TRUE, nao RN preenchido.
UPDATE clientes
SET base_pdv_atual = TRUE
WHERE codigo_pdv IS NOT NULL
  AND codigo_pdv <> ''
  AND rn IS NOT NULL
  AND rn <> '';

-- Clientes historicos podem ser conhecidos somente pela Base de Vendas.
-- Nesses casos nome/cidade podem ser desconhecidos ate uma base cadastral
-- futura complementar esses atributos.
ALTER TABLE clientes
    MODIFY nome VARCHAR(150) NULL,
    MODIFY cidade VARCHAR(100) NULL;

ALTER TABLE vendas
    ADD COLUMN operacao INT NOT NULL DEFAULT 1 AFTER valor_total;

-- A migration 001 criou a unique sem operacao. A nova granularidade separa
-- venda e bonificacao para o mesmo cliente/periodo/origem.
ALTER TABLE vendas
    DROP INDEX uk_vendas_cliente_periodo_origem;

ALTER TABLE vendas
    ADD UNIQUE KEY uk_vendas_cliente_periodo_operacao_origem (
        cliente_id,
        periodo,
        operacao,
        origem
    );

CREATE INDEX idx_vendas_periodo_operacao ON vendas (periodo, operacao);

-- Produtos historicos podem existir sem classificacao em cesta/categoria.
-- Eles participam de faturamento e volume total, mas nao entram em cestas
-- ate receberem classificacao comercial.
ALTER TABLE produtos
    MODIFY categoria VARCHAR(100) NULL,
    MODIFY preco DECIMAL(10,2) NOT NULL DEFAULT 0.00;
