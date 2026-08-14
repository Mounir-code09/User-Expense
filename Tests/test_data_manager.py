"""Data persistence, custom categories, schema migration, and user management tests."""
import json
import os
import pytest
from core.data_manager import (
    load_database,
    load_user,
    save_user,
    delete_user_data,
    get_all_usernames,
    user_exists,
    normalize_username,
    DEFAULT_USER_TEMPLATE,
    DEFAULT_CATEGORIES,
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


def test_normalize_username():
    """Normalize usernames to title-case for consistent lookups."""
    assert normalize_username("  alice  ") == "Alice"
    assert normalize_username("JOHN") == "John"


def test_save_and_load_user():
    """Saved profiles round-trip correctly and register as existing users."""
    username = "Charlie"
    profile_data = {
        "currency": "USD",
        "categories": DEFAULT_CATEGORIES.copy(),
        "budget_limits": {"food": 100.0},
        "transactions": [
            {"id": "tx_1", "date": "2026-08-14", "category": "food", "amount": 25.0, "note": "Groceries"}
        ],
        "password_hash": "salt:hash",
        "failed_attempts": 0,
        "lockout_until": 0,
    }
    save_user(username, profile_data)
    loaded = load_user(username)
    assert loaded["currency"] == "USD"
    assert loaded["budget_limits"]["food"] == 100.0
    assert len(loaded["transactions"]) == 1
    assert username in get_all_usernames()
    assert user_exists(username) is True


def test_legacy_schema_migration():
    """Legacy user profile dictionaries are automatically migrated to modern schema."""
    legacy_profile = {
        "currency": "EUR",
        "budget_limit": {"transport": 50.0},
        "current_expenses": {"transport": 20.0},
        "password_hash": "legacy:hash",
    }
    save_user("LegacyUser", legacy_profile)
    migrated = load_user("LegacyUser")

    assert migrated["currency"] == "EUR"
    assert "budget_limits" in migrated
    assert migrated["budget_limits"]["transport"] == 50.0
    assert "transactions" in migrated
    assert len(migrated["transactions"]) == 1
    assert migrated["transactions"][0]["category"] == "transport"
    assert migrated["transactions"][0]["amount"] == 20.0


def test_load_non_existent_user_returns_fallback_template():
    """Unknown users receive blank profile template with empty password hash."""
    template = load_user("UnknownUser")
    assert template["currency"] == DEFAULT_USER_TEMPLATE["currency"]
    assert template["password_hash"] == ""
    assert "categories" in template


def test_delete_user_data():
    """Deleting removes the record and returns True only when the user existed."""
    username = "David"
    save_user(username, DEFAULT_USER_TEMPLATE.copy())
    assert delete_user_data(username) is True
    assert username not in get_all_usernames()
    assert delete_user_data("NonExistent") is False
