"""User profile, transactions, custom categories, CSV export, and container tests."""
import os
import pytest
from core.user import User, Users
from core.data_manager import get_all_usernames, DEFAULT_CATEGORIES


@pytest.fixture
def mock_ram_db(monkeypatch):
    db_store = {
        "users": {
            "Alice": {
                "currency": "USD",
                "categories": DEFAULT_CATEGORIES.copy(),
                "budget_limits": {"food": 150.0, "transport": 60.0},
                "transactions": [
                    {"id": "tx_1", "date": "2026-08-10", "category": "food", "amount": 40.0, "note": "Groceries"},
                    {"id": "tx_2", "date": "2026-08-12", "category": "transport", "amount": 10.0, "note": "Bus pass"},
                ],
                "password_hash": "ab" * 16 + ":" + "cd" * 32,
                "failed_attempts": 0,
                "lockout_until": 0,
            }
        }
    }

    monkeypatch.setattr("core.data_manager.load_database", lambda: db_store)
    monkeypatch.setattr("core.data_manager.save_database", lambda data: db_store.update(data))
    monkeypatch.setattr(
        "core.currency_service.CurrencyService.convert",
        lambda self, amount, from_curr, to_curr: amount,
    )


def test_user_initialization_loads_correct_data(mock_ram_db):
    user = User("Alice")
    assert user.name == "Alice"
    assert user.currency == "USD"
    assert user.budget_limits["food"] == 150.0
    assert len(user.transactions) == 2


def test_user_blank_name_raises_error(mock_ram_db):
    with pytest.raises(ValueError, match="blank"):
        User("")
    with pytest.raises(ValueError, match="blank"):
        User("   ")


def test_add_custom_category(mock_ram_db):
    user = User("Alice")
    user.add_custom_category("Subscriptions")
    assert user.is_valid_category("subscriptions") is True
    assert "subscriptions" in user.categories

    with pytest.raises(ValueError, match="already exists"):
        user.add_custom_category("subscriptions")
    with pytest.raises(ValueError, match="blank"):
        user.add_custom_category("")


def test_add_and_delete_transaction(mock_ram_db):
    user = User("Alice")
    tx = user.add_transaction("food", 25.50, note="Dinner", date="2026-08-14")
    assert tx["amount"] == 25.50
    assert tx["note"] == "Dinner"
    assert len(user.transactions) == 3

    assert user.delete_transaction(tx["id"]) is True
    assert len(user.transactions) == 2
    assert user.delete_transaction("non_existent_id") is False


def test_transaction_filtering(mock_ram_db):
    user = User("Alice")
    food_txs = user.get_transactions(category="food")
    assert len(food_txs) == 1
    assert food_txs[0]["category"] == "food"

    aug_txs = user.get_transactions(month="2026-08")
    assert len(aug_txs) == 2


def test_dynamic_financial_metrics(mock_ram_db):
    user = User("Alice")
    assert user.total_expenses_of_user() == 50.0

    rem_budget = user.get_remaining_budget()
    # Total budget = 150 + 60 = 210, total spent = 50 -> remaining = 160
    assert rem_budget == 160.0

    top_cat, top_amt = user.get_top_category()
    assert top_cat == "Food"
    assert top_amt == 40.0


def test_set_budget_limit_valid_and_invalid(mock_ram_db):
    user = User("Alice")
    user.set_budget_limit("food", 200.0)
    assert user.budget_limits["food"] == 200.0

    user.set_budget_limit("Transport", 75.0)
    assert user.check_budget("transport") == 75.0

    with pytest.raises(ValueError):
        user.set_budget_limit("food", -50.0)


def test_reset_category_clears_budget_and_transactions(mock_ram_db):
    user = User("Alice")
    removed = user.reset_category("food")
    assert removed["budget_limit"] == 150.0
    assert removed["expense"] == 40.0
    assert "food" not in user.budget_limits
    assert all(tx["category"] != "food" for tx in user.transactions)


def test_csv_export(tmp_path, mock_ram_db):
    user = User("Alice")
    export_file = tmp_path / "alice_export.csv"
    user.export_to_csv(str(export_file))
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Transaction ID,Date,Category,Amount,Currency,Note" in content
        assert "Food" in content
        assert "40.00" in content


def test_users_container_management(mock_ram_db):
    container = Users()
    user_alice = container.get_user("Alice")
    assert user_alice.name == "Alice"
    assert "Alice" in get_all_usernames()

    assert container.add_user("Alice") is False
    assert container.get_user("NonExistent") is None

    assert container.delete_user("Alice") is True
    assert "Alice" not in get_all_usernames()
