"""Ferramentas MCP para consultar transações financeiras locais."""

from mcp.server.fastmcp import FastMCP

from finance_watcher.mcp_server.db import (
    find_recurring_charges as query_recurring_charges,
    get_monthly_summary as query_monthly_summary,
    list_transactions as query_transactions,
    seed_database,
)

mcp = FastMCP("FinanceWatcher")


@mcp.tool()
def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """Lista transações por período e categoria. Datas usam formato AAAA-MM-DD."""
    return query_transactions(start_date, end_date, category)


@mcp.tool()
def get_monthly_summary(year: int, month: int) -> dict:
    """Resume despesas do mês em centavos, incluindo totais por categoria."""
    return query_monthly_summary(year, month)


@mcp.tool()
def find_recurring_charges() -> list[dict]:
    """Encontra despesas semelhantes cobradas em pelo menos dois meses."""
    return query_recurring_charges()


def main() -> None:
    seed_database()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
