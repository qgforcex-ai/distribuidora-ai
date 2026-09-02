-- Migration 002 - Corrigir Base PDV operacional
--
-- Regra definitiva:
-- clientes = Base PDV atual, uma linha por PDV, sem periodo.
-- vendas/itens_venda = historico de vendas com periodo.
-- base_pdv_periodos permanece temporariamente como estrutura legada,
-- mas nao deve ser usada pelo agente nem pelos importadores operacionais.

ALTER TABLE clientes
    ADD COLUMN rn VARCHAR(20) NULL AFTER status_cliente,
    ADD COLUMN proxima_visita DATE NULL AFTER rn;

CREATE INDEX idx_clientes_rn ON clientes (rn);
CREATE INDEX idx_clientes_status_cliente ON clientes (status_cliente);
CREATE INDEX idx_clientes_cidade ON clientes (cidade);

-- Aproveita os dados completos carregados temporariamente em base_pdv_periodos
-- para popular a Base PDV atual em clientes.
UPDATE clientes c
JOIN (
    SELECT b1.*
    FROM base_pdv_periodos b1
    JOIN (
        SELECT cliente_id, MAX(periodo) AS periodo
        FROM base_pdv_periodos
        GROUP BY cliente_id
    ) latest
      ON latest.cliente_id = b1.cliente_id
     AND latest.periodo = b1.periodo
) b
  ON b.cliente_id = c.id
SET
    c.rn = b.rn,
    c.proxima_visita = b.proxima_visita,
    c.nome = COALESCE(NULLIF(b.nome_fantasia, ''), c.nome),
    c.cidade = COALESCE(NULLIF(b.cidade, ''), c.cidade),
    c.bairro = b.bairro,
    c.status_cliente = b.status_cliente;
