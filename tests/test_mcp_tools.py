from finance_watcher.mcp_server.db import (
    find_recurring_charges,
    get_monthly_summary,
    list_transactions,
    seed_database,
)


def test_seed_and_list_transactions(tmp_path):
    database = tmp_path / "transactions.db"
    seed_database(database)

    results = list_transactions("2025-01-01", "2025-01-31", "assinaturas", database)

    assert [row["description"] for row in results] == ["Netflix", "Spotify"]


def test_monthly_summary_excludes_income(tmp_path):
    database = tmp_path / "transactions.db"
    seed_database(database)

    summary = get_monthly_summary(2025, 1, database)

    assert summary["total_expenses_cents"] == 252312
    assert summary["transaction_count"] == 7


def test_recurring_charges_detects_stable_payments(tmp_path):
    database = tmp_path / "transactions.db"
    seed_database(database)

    charges = find_recurring_charges(database)
    descriptions = {charge["description"] for charge in charges}

    assert {"Netflix", "Spotify", "Aluguel", "Internet Fibra"} <= descriptions
    assert "Delivery Sabor" not in descriptions


def test_invalid_date_is_rejected(tmp_path):
    seed_database(tmp_path / "transactions.db")

    try:
        list_transactions(start_date="ontem", db_path=tmp_path / "transactions.db")
    except ValueError as error:
        assert "AAAA-MM-DD" in str(error)
    else:
        raise AssertionError("data inválida deveria ser rejeitada")
