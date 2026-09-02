USE distribuidora;

-- Preflight: este SELECT deve retornar zero linhas antes da UNIQUE em itens.
SELECT venda_id, produto_id, COUNT(*) AS qtd
FROM itens_venda
GROUP BY venda_id, produto_id
HAVING COUNT(*) > 1;

-- Clientes passa a representar a dimensao mestre do PDV.
ALTER TABLE clientes
    ADD COLUMN codigo_pdv VARCHAR(50) NULL AFTER id,
    ADD COLUMN bairro VARCHAR(150) NULL AFTER cidade,
    ADD COLUMN status_cliente VARCHAR(50) NULL AFTER bairro;

UPDATE clientes
SET codigo_pdv = CAST(id AS CHAR)
WHERE codigo_pdv IS NULL OR codigo_pdv = '';

-- Preflight: este SELECT deve retornar zero linhas antes da UNIQUE de codigo_pdv.
SELECT codigo_pdv, COUNT(*) AS qtd
FROM clientes
GROUP BY codigo_pdv
HAVING COUNT(*) > 1;

ALTER TABLE clientes
    MODIFY codigo_pdv VARCHAR(50) NOT NULL,
    ADD UNIQUE KEY uk_clientes_codigo_pdv (codigo_pdv);

-- Controle de importacoes.
CREATE TABLE importacoes (
    id INT NOT NULL AUTO_INCREMENT,
    tipo VARCHAR(50) NOT NULL,
    periodo DATE NULL,
    arquivo_nome VARCHAR(255) NULL,
    arquivo_hash VARCHAR(64) NULL,
    status VARCHAR(30) NULL,
    linhas_lidas INT NOT NULL DEFAULT 0,
    linhas_importadas INT NOT NULL DEFAULT 0,
    erros INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_importacoes_tipo_periodo (tipo, periodo),
    KEY idx_importacoes_arquivo_hash (arquivo_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Snapshot do universo comercial por periodo.
CREATE TABLE base_pdv_periodos (
    id INT NOT NULL AUTO_INCREMENT,
    periodo DATE NOT NULL,
    cliente_id INT NOT NULL,
    rn VARCHAR(20) NOT NULL,
    nome_fantasia VARCHAR(150) NULL,
    cidade VARCHAR(100) NULL,
    bairro VARCHAR(150) NULL,
    status_cliente VARCHAR(50) NULL,
    proxima_visita DATE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_base_pdv_periodo_cliente (periodo, cliente_id),
    KEY idx_base_pdv_periodo_rn (periodo, rn),
    KEY idx_base_pdv_cliente_id (cliente_id),
    KEY idx_base_pdv_periodo (periodo),
    CONSTRAINT fk_base_pdv_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vendas passa a suportar fato analitico mensal.
ALTER TABLE vendas
    ADD COLUMN periodo DATE NULL AFTER cliente_id,
    MODIFY data_venda DATETIME NULL,
    ADD COLUMN origem VARCHAR(50) NULL AFTER valor_total,
    ADD COLUMN importacao_id INT NULL AFTER origem;

UPDATE vendas
SET periodo = STR_TO_DATE(DATE_FORMAT(data_venda, '%Y-%m-01'), '%Y-%m-%d')
WHERE periodo IS NULL AND data_venda IS NOT NULL;

UPDATE vendas
SET periodo = CURRENT_DATE()
WHERE periodo IS NULL;

-- Origem unica por venda didatica evita colisao com a nova granularidade
-- cliente + periodo + origem, preservando os registros existentes.
UPDATE vendas
SET origem = CONCAT('DIDATICO_', id)
WHERE origem IS NULL OR origem = '';

ALTER TABLE vendas
    MODIFY periodo DATE NOT NULL,
    ADD UNIQUE KEY uk_vendas_cliente_periodo_origem (cliente_id, periodo, origem),
    ADD KEY idx_vendas_cliente_periodo (cliente_id, periodo),
    ADD KEY idx_vendas_periodo (periodo),
    ADD KEY idx_vendas_importacao_id (importacao_id),
    ADD CONSTRAINT fk_vendas_importacao
        FOREIGN KEY (importacao_id) REFERENCES importacoes(id);

-- Itens passam a representar produto consolidado dentro da venda mensal.
ALTER TABLE itens_venda
    MODIFY quantidade DECIMAL(15,4) NOT NULL,
    MODIFY preco_unitario DECIMAL(15,6) NOT NULL,
    MODIFY subtotal DECIMAL(15,2) NOT NULL,
    ADD UNIQUE KEY uk_itens_venda_produto (venda_id, produto_id);
