# FinanceWatcher

Auditor pessoal de extratos e contratos. O projeto começa com ferramentas determinísticas para consultar transações em SQLite via Model Context Protocol (MCP); as próximas etapas adicionam um agente e busca em contratos.

## Requisitos

- Python 3.10 ou superior
- [`uv`](https://docs.astral.sh/uv/) (recomendado) ou `pip`

## Instalação e execução

```bash
uv sync --extra dev
uv run finance-watcher-seed
uv run finance-watcher-mcp
```

O servidor MCP usa transporte `stdio`, adequado para conexão com clientes MCP locais. Configure `FINANCE_WATCHER_DB` para apontar para outro arquivo SQLite. Sem configuração, o banco fica em `data/transactions.db`.

Para iniciar o banco manualmente:

```bash
uv run python -m finance_watcher.mcp_server.db
```

## Ferramentas MCP

- `list_transactions(start_date, end_date, category)`: lista transações dentro de intervalo ISO (`AAAA-MM-DD`); datas e categoria são opcionais.
- `get_monthly_summary(year, month)`: retorna total de despesas, quantidade e agrupamento por categoria.
- `find_recurring_charges()`: identifica descrições cobradas em pelo menos dois meses, com valores próximos.

Os dados gerados são inteiramente fictícios. Não use o banco de demonstração como registro financeiro real.

## Desenvolvimento

```bash
uv run pytest
```

## Roteiro

1. Consultas de extrato em SQLite e servidor MCP.
2. Agente com chamadas de ferramentas.
3. Indexação e consulta de contratos PDF com RAG.
