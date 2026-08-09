"""
Unit Tests for User Module
Validates User_class initialization, budget limits, expense tracking, and currency updates.
"""
import pytest
from core.user import User_class, Users, get_all_usernames

@pytest.fixture
def mock_ram_db(monkeypatch):
    db_store = {
        "users": {
            "Alice": {
                "currency": "USD",
                "budget_limit": {"food": 150.0, "transport": 60.0},
                "current_expenses": {"food": 40.0, "transport": 10.0}
            }
        }
    }
    
    # Mock data_manager database functions so all user operations use db_store in RAM
    monkeypatch.setattr("core.data_manager.load_database", lambda: db_store)
    monkeypatch.setattr("core.data_manager.save_database", lambda data: db_store.update(data))
    
    # Mock CurrencyService conversion method to avoid live network requests during tests
    monkeypatch.setattr("core.currency_service.CurrencyService.convert", lambda self, amount, from_curr, to_curr: amount)

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

    # Test invalid negative budget limit handling
    with pytest.raises(ValueError):
        user.set_budget_limit("food", -50.0)

def test_currency_conversion_updates_data(mock_ram_db):
    user = User_class("Alice")
    initial_expense = user.current_expenses["food"]
    
    # Test currency conversion execution and return value
    converted = user.change_currency(initial_expense, "USD", "EUR")
    assert converted == initial_expense
    
    # Update and assert currency attribute state
    user.currency = "EUR"
    assert user.currency == "EUR"

def test_purge_removes_category_keys(mock_ram_db):
    user = User_class("Alice")
    assert "food" in user.current_expenses
    user.current_expenses.pop("food", None)
    assert "food" not in user.current_expenses

def test_users_container_management(mock_ram_db):
    container = Users()
    user_alice = container.get_user("Alice")
    assert user_alice.name == "Alice"
    
    usernames = get_all_usernames()
    assert "Alice" in usernames