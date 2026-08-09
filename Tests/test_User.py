"""
User Entities Unit Tests
========================

Validates :class:`core.user.User_class` and :class:`core.user.Users`.
"""
import pytest
from core.user import User_class, Users
from core.data_manager import get_all_usernames


@pytest.fixture
def mock_ram_db(monkeypatch):
    db_store = {
        "users": {
            "Alice": {
                "currency": "USD",
                "budget_limit": {"food": 150.0, "transport": 60.0},
                "current_expenses": {"food": 40.0, "transport": 10.0},
                "password_hash": "ab" * 16 + ":" + "cd" * 32,
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
    user = User_class("Alice")
    assert user.name == "Alice"
    assert user.currency == "USD"
    assert user.budget_limit["food"] == 150.0
    assert user.current_expenses["food"] == 40.0


def test_set_budget_limit_valid_and_invalid(mock_ram_db):
    user = User_class("Alice")
    user.set_budget_limit("food", 200.0)
    assert user.budget_limit["food"] == 200.0

    user.set_budget_limit("Transport", 75.0)
    assert user.check_budget("transport") == 75.0

    with pytest.raises(ValueError):
        user.set_budget_limit("food", -50.0)


def test_total_expenses_of_user(mock_ram_db):
    user = User_class("Alice")
    assert user.total_expenses_of_user() == 50.0


def test_currency_conversion_updates_data(mock_ram_db):
    user = User_class("Alice")
    initial_expense = user.current_expenses["food"]
    converted = user.change_currency(initial_expense, "USD", "EUR")
    assert converted == initial_expense


def test_purge_removes_category_keys(mock_ram_db):
    user = User_class("Alice")
    assert "food" in user.current_expenses
    assert "food" in user.budget_limit

    removed = user.purge("food")
    assert removed == {"budget_limit": 150.0, "expense": 40.0}
    assert "food" not in user.current_expenses
    assert "food" not in user.budget_limit


def test_users_container_management(mock_ram_db):
    container = Users()
    user_alice = container.get_user("Alice")
    assert user_alice.name == "Alice"
    assert "Alice" in get_all_usernames()

    assert container.delete_user("Alice") is True
    assert "Alice" not in get_all_usernames()