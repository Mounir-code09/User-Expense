"""
DataManager Unit Tests
======================

Verifies the persistence layer responsible for reading/writing the JSON database.

Why these tests matter
----------------------
``data_manager.py`` is the single source of truth for all user records. A regression
here would silently corrupt or lose financial data, so every public function is
covered: loading, saving, deleting, category validation, and username normalization.

The ``clean_test_db`` fixture redirects the module to a throwaway temp file for each
test, so the real ``Database.json`` is never touched.
"""
import json
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
    """
    Point ``core.data_manager`` at a fresh, empty database file for every test.

    ``autouse=True`` injects this fixture automatically, guaranteeing test isolation:
    no test can leak user records into the project's real ``Database.json``.
    """
    test_file = tmp_path / "test_db.json"
    with open(test_file, "w", encoding="utf-8") as file:
        json.dump({"users": {}}, file)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))


def test_load_database_behavior(monkeypatch):
    """
    Loading must return an empty ``{"users": {}}`` structure both for a fresh file
    and for a missing file, so the app never crashes on a corrupt/absent database.
    """
    db_data = load_database()
    assert db_data == {"users": {}}

    # Point to a path that does not exist; the loader must gracefully fall back.
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", "non_existent_file.json")
    fallback_data = load_database()
    assert fallback_data == {"users": {}}


def test_category_validation():
    """
    ``cat_v`` must accept only the canonical categories, ignoring case and padding,
    and reject everything else (including empty strings and unknown words).
    """
    assert cat_v("food") is True
    assert cat_v("  FOOD  ") is True          # case- and whitespace-insensitive
    assert cat_v("  RENT  ") is False         # not in VALID_CATEGORIES
    assert cat_v("invalid_category") is False
    assert cat_v("") is False


def test_normalize_username():
    """Usernames are trimmed and title-cased so lookups stay consistent."""
    assert normalize_username("  alice  ") == "Alice"
    assert normalize_username("JOHN") == "John"


def test_save_and_load_user():
    """A saved profile must round-trip exactly and register the user as existing."""
    username = "Charlie"
    profile_data = {
        "currency": "USD",
        "budget_limit": {"food": 100.0},
        "current_expenses": {},
        "password_hash": "salt:hash",
    }
    save_user(username, profile_data)
    assert load_user(username) == profile_data
    assert username in get_all_usernames()
    assert user_exists(username) is True


def test_load_non_existent_user_returns_fallback_template():
    """
    Unknown users receive a blank profile template (with an empty password hash),
    which is the safe default before a real account is registered.
    """
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
