-- Migration 004 - Adicionar volume comercial em hectolitros
--
-- Regras:
-- produtos.fator_hl armazena o fator atual/cadastral do SKU quando conhecido.
-- itens_venda.fator_hl preserva o fator informado na Base Venda para o item.
-- itens_venda.volume_hl preserva o volume HL informado na Base Venda.
-- Faturamento continua sendo SUM(itens_venda.subtotal) apenas operacao = 1.
-- Volume comercial passa a ser SUM(itens_venda.volume_hl), nao SUM(quantidade).

ALTER TABLE produtos
    ADD COLUMN fator_hl DECIMAL(15,6) NULL AFTER preco;

ALTER TABLE itens_venda
    ADD COLUMN fator_hl DECIMAL(15,6) NULL AFTER quantidade,
    ADD COLUMN volume_hl DECIMAL(15,6) NOT NULL DEFAULT 0.000000 AFTER fator_hl;

CREATE INDEX idx_itens_venda_volume_hl ON itens_venda (volume_hl);
