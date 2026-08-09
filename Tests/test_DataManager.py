"""
DataManager Unit Test Pipeline
"""
import pytest
import json
from core.data_manager import (
    load_database, load_user, save_user, 
    delete_user_data, get_all_usernames, cat_v
)

@pytest.fixture(autouse=True)
def clean_test_db(tmp_path, monkeypatch):
    test_file = tmp_path / "test_db.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"users": {}}, f)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))

def test_load_database_behavior(clean_test_db, monkeypatch):
    db_data = load_database()
    assert db_data == {"users": {}}
    
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", "non_existent_file.json")
    fallback_data = load_database()
    assert fallback_data == {"users": {}}

def test_category_validation():
    assert cat_v("food") is True
    assert cat_v("  RENT  ") is False  
    assert cat_v("invalid_category") is False
    assert cat_v("") is False

def test_save_and_load_user():
    username = "Charlie"
    profile_data = {"currency": "USD", "budget_limit": {"food": 100.0}, "current_expenses": {}}
    save_user(username, profile_data)
    assert load_user(username) == profile_data
    assert username in get_all_usernames()

def test_load_non_existent_user_returns_fallback_template():
    assert load_user("UnknownUser") == {"currency": "USD", "budget_limit": {}, "current_expenses": {}}

def test_delete_user_data():
    username = "David"
    save_user(username, {"currency": "USD", "budget_limit": {}, "current_expenses": {}})
    assert delete_user_data(username) is True
    assert username not in get_all_usernames()
    assert delete_user_data("NonExistent") is False