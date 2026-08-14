"""User profile, transactions, incomes, net savings, budget progress, custom categories, CSV export, and container tests."""
import os
import pytest
from core.user import User, Users
from core.data_manager import get_all_usernames, DEFAULT_CATEGORIES
from core.exceptions import (
    CategoryAlreadyExistsError,
    InvalidAmountError,
    InvalidCategoryError,
)
from core.theme import format_amount


@pytest.fixture
def mock_ram_db(monkeypatch):
    db_store = {
        "users": {
            "Alice": {
                "currency": "USD",
                "categories": DEFAULT_CATEGORIES.copy(),
                "budget_limits": {"food": 1500.0, "transport": 600.0},
                "transactions": [
                    {"id": "tx_1", "date": "2026-08-10", "category": "food", "amount": 450.0, "note": "Weekly grocery shopping at Lidl"},
                    {"id": "tx_2", "date": "2026-08-12", "category": "transport", "amount": 120.0, "note": "Monthly train commuter pass"},
                ],
                "incomes": [
                    {"id": "inc_1", "date": "2026-08-01", "source": "Salary", "amount": 3500.0, "note": "Monthly paycheck"},
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


def test_format_amount_utility():
    """Verify comma thousand-separator formatting."""
    assert format_amount(12345.67) == "12,345.67"
    assert format_amount(12345678.9) == "12,345,678.90"
    assert format_amount(50, "USD") == "50.00 USD"
    assert format_amount(-15200.5, "EUR") == "-15,200.50 EUR"
    assert format_amount("invalid") == "0.00"


def test_user_initialization_loads_correct_data(mock_ram_db):
    user = User("Alice")
    assert user.name == "Alice"
    assert user.currency == "USD"
    assert user.budget_limits["food"] == 1500.0
    assert len(user.transactions) == 2
    assert len(user.incomes) == 1


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

    with pytest.raises(CategoryAlreadyExistsError):
        user.add_custom_category("subscriptions")
    with pytest.raises(InvalidCategoryError):
        user.add_custom_category("")


def test_add_and_delete_transaction(mock_ram_db):
    user = User("Alice")
    tx = user.add_transaction("food", 250.50, note="Family dinner at restaurant", date="2026-08-14")
    assert tx["amount"] == 250.50
    assert tx["note"] == "Family dinner at restaurant"
    assert len(user.transactions) == 3

    assert user.delete_transaction(tx["id"]) is True
    assert len(user.transactions) == 2
    assert user.delete_transaction("non_existent_id") is False


def test_add_and_delete_income(mock_ram_db):
    user = User("Alice")
    inc = user.add_income("Freelance", 500.0, note="Website design client", date="2026-08-14")
    assert inc["source"] == "Freelance"
    assert inc["amount"] == 500.0
    assert len(user.incomes) == 2

    assert user.delete_income(inc["id"]) is True
    assert len(user.incomes) == 1
    assert user.delete_income("invalid_id") is False


def test_income_and_net_savings_calculations(mock_ram_db):
    user = User("Alice")
    assert user.total_income_of_user() == 3500.0
    assert user.total_expenses_of_user() == 570.0

    # Net Savings = 3500 - 570 = 2930.0
    assert user.get_net_savings() == 2930.0
    # Savings Rate = (2930 / 3500) * 100 = ~83.7%
    assert user.get_savings_rate() == 83.7


def test_category_budget_progress(mock_ram_db):
    user = User("Alice")
    progress = user.get_category_budget_progress()
    assert len(progress) == 2  # food and transport

    food_item = next(p for p in progress if p["category"] == "Food")
    assert food_item["spent"] == 450.0
    assert food_item["limit"] == 1500.0
    assert food_item["percentage"] == 30.0
    assert food_item["status"] == "success"


def test_transaction_filtering_and_notes(mock_ram_db):
    user = User("Alice")
    food_txs = user.get_transactions(category="food")
    assert len(food_txs) == 1
    assert "Lidl" in food_txs[0]["note"]

    aug_txs = user.get_transactions(month="2026-08")
    assert len(aug_txs) == 2


def test_dynamic_financial_metrics(mock_ram_db):
    user = User("Alice")
    assert user.total_expenses_of_user() == 570.0

    rem_budget = user.get_remaining_budget()
    assert rem_budget == 1530.0

    top_cat, top_amt = user.get_top_category()
    assert top_cat == "Food"
    assert top_amt == 450.0


def test_set_budget_limit_valid_and_invalid(mock_ram_db):
    user = User("Alice")
    user.set_budget_limit("food", 2000.0)
    assert user.budget_limits["food"] == 2000.0

    user.set_budget_limit("Transport", 750.0)
    assert user.check_budget("transport") == 750.0

    with pytest.raises(InvalidAmountError):
        user.set_budget_limit("food", -50.0)
    with pytest.raises(InvalidCategoryError):
        user.set_budget_limit("unknown_cat", 100.0)


def test_reset_category_clears_budget_and_transactions(mock_ram_db):
    user = User("Alice")
    removed = user.reset_category("food")
    assert removed["budget_limit"] == 1500.0
    assert removed["expense"] == 450.0
    assert "food" not in user.budget_limits
    assert all(tx["category"] != "food" for tx in user.transactions)


def test_csv_export(tmp_path, mock_ram_db):
    user = User("Alice")
    export_file = tmp_path / "alice_export.csv"
    user.export_to_csv(str(export_file))
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Type,ID,Date,Category/Source,Amount,Currency,Note" in content
        assert "Expense" in content
        assert "Income" in content
        assert "Food" in content
        assert "Salary" in content
        assert "3500.00" in content


def test_users_container_management(mock_ram_db):
    container = Users()
    user_alice = container.get_user("Alice")
    assert user_alice.name == "Alice"
    assert "Alice" in get_all_usernames()

    assert container.add_user("Alice") is False
    assert container.get_user("NonExistent") is None

    assert container.delete_user("Alice") is True
    assert "Alice" not in get_all_usernames()
