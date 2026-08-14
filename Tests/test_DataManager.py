"""Data persistence and user record management tests."""
import json
import os
import pytest
from core.data_manager import (
    load_database,
    load_user,
    save_user,
    delete_user_data,
    get_all_usernames,
    cat_v,
    user_exists,
    normalize_username,
    DEFAULT_USER_TEMPLATE,
)


@pytest.fixture(autouse=True)
def clean_test_db(tmp_path, monkeypatch):
    """Use fresh test database for each test to avoid contaminating real data."""
    test_file = tmp_path / "test_db.json"
    with open(test_file, "w", encoding="utf-8") as file:
        json.dump({"users": {}}, file)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))


def test_load_database_behavior(monkeypatch):
    """Load returns empty structure for missing or empty files."""
    db_data = load_database()
    assert db_data == {"users": {}}

    monkeypatch.setattr("core.data_manager.DATABASE_FILE", "non_existent_file.json")
    fallback_data = load_database()
    assert fallback_data == {"users": {}}


def test_corrupted_database_backup(tmp_path, monkeypatch):
    """Corrupted json creates a backup and resets gracefully."""
    test_file = tmp_path / "corrupt_db.json"
    with open(test_file, "w", encoding="utf-8") as file:
        file.write("{invalid_json:")
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))

    db_data = load_database()
    assert db_data == {"users": {}}
    assert os.path.exists(f"{test_file}.corrupt.bak")


def test_empty_username_handling():
    """Empty and whitespace usernames are safely rejected."""
    assert normalize_username("") == ""
    assert normalize_username("   ") == ""
    assert user_exists("") is False
    assert delete_user_data("") is False

    save_user("", {"currency": "USD"})
    assert "" not in get_all_usernames()


def test_category_validation():
    """Validate categories are case-insensitive and only allow canonical names."""
    assert cat_v("food") is True
    assert cat_v("  FOOD  ") is True
    assert cat_v("  RENT  ") is False
    assert cat_v("invalid_category") is False
    assert cat_v("") is False


def test_normalize_username():
    """Normalize usernames to title-case for consistent lookups."""
    assert normalize_username("  alice  ") == "Alice"
    assert normalize_username("JOHN") == "John"


def test_save_and_load_user():
    """Saved profiles round-trip correctly and register as existing users."""
    username = "Charlie"
    profile_data = {
        "currency": "USD",
        "budget_limit": {"food": 100.0},
        "current_expenses": {},
        "password_hash": "salt:hash",
        "failed_attempts": 0,
        "lockout_until": 0,
    }
    save_user(username, profile_data)
    assert load_user(username) == profile_data
    assert username in get_all_usernames()
    assert user_exists(username) is True


def test_load_non_existent_user_returns_fallback_template():
    """Unknown users receive blank profile template with empty password hash."""
    template = load_user("UnknownUser")
    assert template["currency"] == DEFAULT_USER_TEMPLATE["currency"]
    assert template["password_hash"] == ""


def test_delete_user_data():
    """Deleting removes the record and returns True only when the user existed."""
    username = "David"
    save_user(username, DEFAULT_USER_TEMPLATE.copy())
    assert delete_user_data(username) is True
    assert username not in get_all_usernames()
    assert delete_user_data("NonExistent") is False
