"""Consultas e carga de demonstração para o banco SQLite."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "transactions.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    transaction_date TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    transaction_type TEXT NOT NULL DEFAULT 'expense'
        CHECK (transaction_type IN ('expense', 'income'))
);
CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category
    ON transactions(category);
"""

# Valores fictícios, incluindo três meses para demonstrar detecção de recorrência.
SAMPLE_TRANSACTIONS = [
    ("2025-01-03", "Salário", "Renda", 450000, "income"),
    ("2025-01-05", "Mercado Central", "Mercado", 38472, "expense"),
    ("2025-01-08", "Netflix", "Assinaturas", 3990, "expense"),
    ("2025-01-10", "Academia Fit", "Saúde", 11990, "expense"),
    ("2025-01-12", "Internet Fibra", "Moradia", 9990, "expense"),
    ("2025-01-15", "Aluguel", "Moradia", 180000, "expense"),
    ("2025-01-18", "Spotify", "Assinaturas", 2190, "expense"),
    ("2025-01-22", "Delivery Sabor", "Restaurantes", 5680, "expense"),
    ("2025-02-03", "Salário", "Renda", 450000, "income"),
    ("2025-02-05", "Mercado Central", "Mercado", 42110, "expense"),
    ("2025-02-08", "Netflix", "Assinaturas", 3990, "expense"),
    ("2025-02-10", "Academia Fit", "Saúde", 11990, "expense"),
    ("2025-02-12", "Internet Fibra", "Moradia", 9990, "expense"),
    ("2025-02-15", "Aluguel", "Moradia", 180000, "expense"),
    ("2025-02-18", "Spotify", "Assinaturas", 2190, "expense"),
    ("2025-02-20", "Farmácia Popular", "Saúde", 7425, "expense"),
    ("2025-03-03", "Salário", "Renda", 450000, "income"),
    ("2025-03-05", "Mercado Central", "Mercado", 39725, "expense"),
    ("2025-03-08", "Netflix", "Assinaturas", 3990, "expense"),
    ("2025-03-10", "Academia Fit", "Saúde", 12990, "expense"),
    ("2025-03-12", "Internet Fibra", "Moradia", 10990, "expense"),
    ("2025-03-15", "Aluguel", "Moradia", 180000, "expense"),
    ("2025-03-18", "Spotify", "Assinaturas", 2190, "expense"),
]


def get_db_path() -> Path:
    """Retorna caminho do banco configurado ou caminho local padrão."""
    return Path(os.environ.get("FINANCE_WATCHER_DB", DEFAULT_DB_PATH)).expanduser()


@contextmanager
def connect(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: str | Path | None = None) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)


def seed_database(db_path: str | Path | None = None) -> None:
    """Cria schema e insere demonstração sem duplicar registros existentes."""
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if count == 0:
            connection.executemany(
                """INSERT INTO transactions
                   (transaction_date, description, category, amount_cents, transaction_type)
                   VALUES (?, ?, ?, ?, ?)""",
                SAMPLE_TRANSACTIONS,
            )


def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Lista transações com filtros opcionais e validação de datas ISO."""
    for value, name in ((start_date, "start_date"), (end_date, "end_date")):
        if value is not None:
            try:
                date.fromisoformat(value)
            except ValueError as error:
                raise ValueError(f"{name} deve usar formato AAAA-MM-DD") from error

    clauses = []
    parameters: list[str] = []
    if start_date:
        clauses.append("transaction_date >= ?")
        parameters.append(start_date)
    if end_date:
        clauses.append("transaction_date <= ?")
        parameters.append(end_date)
    if category:
        clauses.append("category = ? COLLATE NOCASE")
        parameters.append(category)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect(db_path) as connection:
        rows = connection.execute(
            f"""SELECT id, transaction_date, description, category,
                       amount_cents, transaction_type
                FROM transactions {where}
                ORDER BY transaction_date, id""",
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_monthly_summary(year: int, month: int, db_path: str | Path | None = None) -> dict[str, Any]:
    if not 1 <= month <= 12:
        raise ValueError("month deve estar entre 1 e 12")
    start = date(year, month, 1).isoformat()
    end = date(year + (month == 12), month % 12 + 1, 1).isoformat()
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT category, SUM(amount_cents) AS total_cents, COUNT(*) AS count
               FROM transactions
               WHERE transaction_date >= ? AND transaction_date < ?
                 AND transaction_type = 'expense'
               GROUP BY category ORDER BY total_cents DESC""",
            (start, end),
        ).fetchall()
    categories = [dict(row) for row in rows]
    return {
        "year": year,
        "month": month,
        "total_expenses_cents": sum(row["total_cents"] for row in categories),
        "transaction_count": sum(row["count"] for row in categories),
        "by_category": categories,
    }


def find_recurring_charges(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Retorna despesas presentes em 2+ meses, com variação máxima de 15%."""
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT description, category, COUNT(DISTINCT substr(transaction_date, 1, 7)) AS months,
                      MIN(amount_cents) AS min_cents, MAX(amount_cents) AS max_cents,
                      ROUND(AVG(amount_cents)) AS average_cents
               FROM transactions
               WHERE transaction_type = 'expense'
               GROUP BY description, category
               HAVING months >= 2 AND (MAX(amount_cents) - MIN(amount_cents)) <= MAX(amount_cents) * 0.15
               ORDER BY description"""
        ).fetchall()
    return [dict(row) for row in rows]


def seed_main() -> None:
    seed_database()
    print(f"Banco de demonstração pronto: {get_db_path()}")


if __name__ == "__main__":
    seed_main()
