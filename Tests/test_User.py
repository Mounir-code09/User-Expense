"""
User Class Calculations Testing Suite
"""
import pytest
from unittest.mock import Mock
from User import User_class, Users


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
    
    monkeypatch.setattr("User.load_user", lambda name: db_store["users"].get(name, {"currency": "USD", "budget_limit": {}, "current_expenses": {}}))
    monkeypatch.setattr("User.save_user", lambda name, data: db_store["users"].__setitem__(name, data))
    monkeypatch.setattr("User.get_all_usernames", lambda: list(db_store["users"].keys()))
    
    # Block network requests and inject static exchange rates via currency_service
    monkeypatch.setattr("User.currency_service.fetch_rates_async", lambda: None)
    monkeypatch.setattr("User.currency_service.rates", {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 155.50, "CAD": 1.37
    })


    def mock_delete(name):
        if name in db_store["users"]:
            del db_store["users"][name]
            return True
        return False
        
    monkeypatch.setattr("User.delete_user_data", mock_delete)
    return db_store

def test_user_initialization_loads_correct_data(mock_ram_db):
    user = User_class("Alice")
    assert user.currency == "USD"
    assert user.budget_limit["food"] == 150.0
    assert user.current_expenses["food"] == 40.0

def test_set_budget_limit_valid_and_invalid(mock_ram_db):
    user = User_class("Alice")
    user.set_budget_limit("shopping", "75.50")
    assert user.budget_limit["shopping"] == 75.50
    
    with pytest.raises(ValueError):
        user.set_budget_limit("food", "-20.0")

def test_currency_conversion_updates_data(mock_ram_db):
    user = User_class("Alice")
    user.convert_account_currency("EUR")
    
    assert user.currency == "EUR"
    # Validates Alice's $150.00 Food budget accurately transformed into EUR format and wrote to store
    expected = round((150.0 / 1.0) * 0.92, 2)
    assert user.budget_limit["food"] == expected

def test_purge_removes_category_keys(mock_ram_db):
    user = User_class("Alice")
    user.purge("food")
    assert "food" not in user.budget_limit
    assert "food" not in user.current_expenses

def test_users_container_management(mock_ram_db):
    manager = Users()
    assert "Alice" in manager.show_users()
    manager.delete_user("Alice")
    assert manager.get_user("Alice") is None