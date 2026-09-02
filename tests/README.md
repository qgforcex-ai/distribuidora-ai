# Gabarito comercial e regressao

Esta pasta preserva o gabarito comercial oficial de agosto/2026 e os
testes de regressao das regras do agente.

## Testes deterministically rapidos

Os testes em `tests/test_commercial_semantics.py` nao chamam Gemini,
Ollama, MySQL ou Redis. Eles validam as regras semanticas aprovadas:

- metricas oficiais usam `vendas.origem = 'BASE_VENDA'`;
- revenda total nao e limitada por `clientes.base_pdv_atual`;
- RN usa `clientes.base_pdv_atual = TRUE`;
- volume comercial usa `itens_venda.volume_hl`;
- distribuicao usa combinacao distinta cliente + produto;
- cobertura retorna compradores, universo e percentual;
- cesta e filtro de produto;
- "quanto vendemos" e interpretado como faturamento.

Execute:

```bash
py -m unittest discover -s tests
```

## Eval completo do agente

O arquivo `tests/evals/commercial_aug_2026.json` contem as 18 perguntas
oficiais da bateria aprovada, com valores esperados e expectativas
semanticas.

O eval completo passa pelo endpoint real `/ia/analisar` e pode depender
de Gemini, MySQL, Redis e API local rodando. Ele nao deve ser executado
como parte dos testes rapidos.

Com a API local ativa:

```bash
py scripts/run_commercial_eval.py --base-url http://localhost:8000
```

Para salvar o resultado:

```bash
py scripts/run_commercial_eval.py --base-url http://localhost:8000 --json-output tests/evals/last_run.json
```

Nao coloque API keys nos arquivos de teste. Use apenas variaveis de
ambiente para configurar provider e credenciais.
