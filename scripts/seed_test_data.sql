USE distribuidora;

DELETE FROM itens_venda;
DELETE FROM vendas;
DELETE FROM produtos;
DELETE FROM clientes;

ALTER TABLE itens_venda AUTO_INCREMENT = 1;
ALTER TABLE vendas AUTO_INCREMENT = 1;
ALTER TABLE produtos AUTO_INCREMENT = 1;
ALTER TABLE clientes AUTO_INCREMENT = 1;

INSERT INTO clientes (id, nome, cidade, limite_credito) VALUES
(1, 'Mercado Central', 'Mogi das Cruzes', 12000.00),
(2, 'Supermercado Avenida', 'Caraguatatuba', 18000.00),
(3, 'Mercado São João', 'Itaquaquecetuba', 9000.00),
(4, 'Empório do Litoral', 'Caraguatatuba', 11000.00),
(5, 'Mercado União', 'São José dos Campos', 8500.00),
(6, 'Supermercado Imperial', 'São Paulo', 22000.00),
(7, 'Mercado Paulista', 'São Paulo', 16000.00),
(8, 'Empório Vale Sul', 'São José dos Campos', 14000.00),
(9, 'Mercado Tatuapé', 'São Paulo', 10000.00),
(10, 'Supermercado Leste', 'Itaquaquecetuba', 13000.00),
(11, 'Mercado Santos', 'Santos', 9500.00),
(12, 'Empório da Praia', 'Santos', 7000.00),
(13, 'Mercado Taubaté', 'Taubaté', 11500.00),
(14, 'Supermercado Bandeirantes', 'Mogi das Cruzes', 17500.00),
(15, 'Mercado Serra', 'Campos do Jordão', 8000.00),
(16, 'Empório Mantiqueira', 'Campos do Jordão', 10500.00),
(17, 'Mercado Nova Era', 'Taubaté', 6500.00),
(18, 'Supermercado Bom Preço', 'São José dos Campos', 15000.00),
(19, 'Mercado Sem Compra', 'Mogi das Cruzes', 5000.00),
(20, 'Cliente Novo', 'Santos', 9000.00);

INSERT INTO produtos (id, codigo, descricao, categoria, preco) VALUES
(1, 'BRAHMA350', 'Brahma Lata 350ml', 'Cerveja', 4.00),
(2, 'SPATEN350', 'Spaten Lata 350ml', 'Cerveja', 5.00),
(3, 'BUD350', 'Budweiser Lata 350ml', 'Cerveja', 5.00),
(4, 'STELLA330', 'Stella Artois 330ml', 'Cerveja', 6.00),
(5, 'BRAHMA600', 'Brahma 600ml', 'Cerveja', 8.00),
(6, 'GUARANA2L', 'Guaraná Antarctica 2L', 'NAB', 7.00),
(7, 'PEPSI2L', 'Pepsi 2L', 'NAB', 8.00),
(8, 'PEPSIZERO2L', 'Pepsi Black 2L', 'NAB', 8.00),
(9, 'GUARANAZERO2L', 'Guaraná Zero 2L', 'NAB', 7.00),
(10, 'H2OH500', 'H2OH 500ml', 'NAB', 4.00);

DROP TEMPORARY TABLE IF EXISTS seed_vendas;
DROP TEMPORARY TABLE IF EXISTS seed_itens_venda;

CREATE TEMPORARY TABLE seed_vendas (
    id INT PRIMARY KEY,
    cliente_id INT NOT NULL,
    data_venda DATETIME NOT NULL
);

CREATE TEMPORARY TABLE seed_itens_venda (
    venda_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL
);

INSERT INTO seed_vendas (id, cliente_id, data_venda) VALUES
(1, 1, '2026-06-05 09:20:00'),
(2, 2, '2026-06-06 10:15:00'),
(3, 3, '2026-06-08 14:30:00'),
(4, 5, '2026-06-10 11:05:00'),
(5, 7, '2026-06-13 16:40:00'),
(6, 11, '2026-06-16 09:50:00'),
(7, 13, '2026-06-20 13:25:00'),
(8, 18, '2026-06-25 15:10:00'),
(9, 4, '2026-06-28 10:35:00'),
(11, 1, '2026-07-03 09:10:00'),
(12, 1, '2026-07-18 15:45:00'),
(13, 2, '2026-07-04 11:20:00'),
(14, 2, '2026-07-22 14:00:00'),
(15, 3, '2026-07-07 10:30:00'),
(16, 4, '2026-07-09 16:15:00'),
(17, 5, '2026-07-11 09:05:00'),
(18, 6, '2026-07-12 13:00:00'),
(19, 7, '2026-07-14 10:25:00'),
(20, 8, '2026-07-15 15:35:00'),
(21, 10, '2026-07-17 11:10:00'),
(22, 12, '2026-07-19 09:40:00'),
(23, 13, '2026-07-21 13:50:00'),
(24, 14, '2026-07-23 16:20:00'),
(25, 16, '2026-07-25 10:00:00'),
(26, 17, '2026-07-27 12:10:00'),
(27, 18, '2026-07-29 14:45:00'),
(28, 1, '2026-08-04 09:30:00'),
(29, 1, '2026-08-19 15:00:00'),
(30, 2, '2026-08-05 10:45:00'),
(31, 3, '2026-08-07 11:20:00'),
(32, 3, '2026-08-24 16:10:00'),
(33, 6, '2026-08-08 13:15:00'),
(34, 7, '2026-08-10 09:55:00'),
(35, 8, '2026-08-12 14:05:00'),
(36, 9, '2026-08-13 10:30:00'),
(37, 12, '2026-08-15 11:40:00'),
(38, 13, '2026-08-17 15:25:00'),
(39, 14, '2026-08-18 09:45:00'),
(40, 15, '2026-08-20 13:35:00'),
(41, 17, '2026-08-22 10:15:00'),
(42, 18, '2026-08-26 14:50:00'),
(43, 20, '2026-08-28 16:30:00');

INSERT INTO seed_itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES
(1, 1, 75, 4.00), (1, 6, 100, 7.00),
(2, 5, 100, 8.00), (2, 6, 100, 7.00),
(3, 1, 100, 4.00), (3, 10, 100, 4.00),
(4, 2, 100, 5.00), (4, 6, 100, 7.00),
(5, 1, 50, 4.00), (5, 6, 100, 7.00),
(6, 6, 100, 7.00),
(7, 5, 75, 8.00), (7, 6, 100, 7.00),
(8, 4, 100, 6.00),
(9, 6, 50, 7.00), (9, 10, 100, 4.00),
(11, 1, 100, 4.00), (11, 7, 75, 8.00),
(12, 5, 100, 8.00), (12, 7, 100, 8.00), (12, 1, 100, 4.00),
(13, 1, 200, 4.00), (13, 5, 100, 8.00), (13, 7, 75, 8.00),
(14, 3, 120, 5.00), (14, 6, 100, 7.00), (14, 7, 62, 8.00), (14, 10, 1, 4.00),
(15, 5, 100, 8.00), (15, 7, 100, 8.00),
(16, 1, 200, 4.00), (16, 5, 100, 8.00), (16, 7, 75, 8.00),
(17, 2, 100, 5.00), (17, 6, 100, 7.00),
(18, 6, 100, 7.00),
(19, 5, 100, 8.00), (19, 6, 100, 7.00),
(20, 5, 100, 8.00), (20, 7, 100, 8.00), (20, 2, 100, 5.00),
(21, 1, 100, 4.00), (21, 10, 100, 4.00),
(22, 2, 120, 5.00),
(23, 2, 50, 5.00), (23, 6, 100, 7.00),
(24, 5, 100, 8.00), (24, 7, 100, 8.00),
(25, 2, 100, 5.00),
(26, 2, 60, 5.00),
(27, 1, 75, 4.00), (27, 6, 100, 7.00),
(28, 2, 200, 5.00), (28, 5, 100, 8.00), (28, 6, 100, 7.00),
(29, 3, 200, 5.00), (29, 8, 100, 8.00), (29, 9, 100, 7.00),
(30, 5, 100, 8.00), (30, 7, 100, 8.00), (30, 1, 100, 4.00),
(31, 1, 100, 4.00), (31, 10, 100, 4.00),
(32, 1, 100, 4.00), (32, 10, 100, 4.00),
(33, 1, 50, 4.00), (33, 6, 100, 7.00),
(34, 2, 80, 5.00), (34, 6, 100, 7.00),
(35, 5, 100, 8.00), (35, 7, 100, 8.00), (35, 2, 100, 5.00),
(36, 2, 100, 5.00), (36, 6, 100, 7.00),
(37, 4, 100, 6.00),
(38, 6, 200, 7.00),
(39, 6, 100, 7.00),
(40, 2, 50, 5.00), (40, 6, 100, 7.00),
(41, 1, 100, 4.00),
(42, 1, 75, 4.00), (42, 6, 100, 7.00),
(43, 3, 120, 5.00), (43, 6, 100, 7.00), (43, 7, 62, 8.00), (43, 10, 1, 4.00);

INSERT INTO vendas (id, cliente_id, data_venda, valor_total)
SELECT
    sv.id,
    sv.cliente_id,
    sv.data_venda,
    SUM(siv.quantidade * siv.preco_unitario) AS valor_total
FROM seed_vendas sv
JOIN seed_itens_venda siv ON siv.venda_id = sv.id
GROUP BY sv.id, sv.cliente_id, sv.data_venda
ORDER BY sv.id;

INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
SELECT
    venda_id,
    produto_id,
    quantidade,
    preco_unitario,
    quantidade * preco_unitario AS subtotal
FROM seed_itens_venda
ORDER BY venda_id, produto_id;

UPDATE vendas v
JOIN (
    SELECT venda_id, SUM(subtotal) AS total_itens
    FROM itens_venda
    GROUP BY venda_id
) totais ON totais.venda_id = v.id
SET v.valor_total = totais.total_itens;

DROP TEMPORARY TABLE IF EXISTS seed_itens_venda;
DROP TEMPORARY TABLE IF EXISTS seed_vendas;
