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
    test_file = tmp_path / "test_db.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"users": {}}, f)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))


def test_load_missing_file(monkeypatch):
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", "non_existent_file.json")
    assert load_database() == {"users": {}}


def test_load_empty_db():
    assert load_database() == {"users": {}}


def test_corrupt_db_creates_backup(tmp_path, monkeypatch):
    f = tmp_path / "corrupt.json"
    f.write_text("{invalid_json:")
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(f))

    assert load_database() == {"users": {}}
    assert os.path.exists(f"{f}.corrupt.bak")


def test_empty_username_rejected():
    assert normalize_username("") == ""
    assert normalize_username("   ") == ""
    assert not user_exists("")
    assert not delete_user_data("")
    save_user("", {"currency": "USD"})
    assert "" not in get_all_usernames()


def test_normalize_username():
    assert normalize_username("  alice  ") == "Alice"
    assert normalize_username("JOHN") == "John"


def test_save_load_roundtrip():
    profile = {
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
    save_user("Charlie", profile)
    loaded = load_user("Charlie")
    assert loaded["currency"] == "USD"
    assert loaded["budget_limits"]["food"] == 100.0
    assert len(loaded["transactions"]) == 1
    assert user_exists("Charlie")


def test_legacy_schema_migration():
    legacy = {
        "currency": "EUR",
        "budget_limit": {"transport": 50.0},
        "current_expenses": {"transport": 20.0},
        "password_hash": "legacy:hash",
    }
    save_user("LegacyUser", legacy)
    migrated = load_user("LegacyUser")

    assert migrated["currency"] == "EUR"
    assert "budget_limits" in migrated
    assert migrated["budget_limits"]["transport"] == 50.0
    assert len(migrated["transactions"]) == 1
    assert migrated["transactions"][0]["category"] == "transport"
    assert migrated["transactions"][0]["amount"] == 20.0


def test_load_unknown_user_returns_blank_profile():
    profile = load_user("UnknownUser")
    assert profile["currency"] == DEFAULT_USER_TEMPLATE["currency"]
    assert profile["password_hash"] == ""
    assert "categories" in profile


def test_delete_user():
    save_user("David", DEFAULT_USER_TEMPLATE.copy())
    assert delete_user_data("David")
    assert "David" not in get_all_usernames()
    assert not delete_user_data("NonExistent")


def test_create_backup_creates_file(tmp_path, monkeypatch):
    from core.data_manager import create_timestamped_backup
    db_file = tmp_path / "Database.json"
    db_file.write_text('{"users": {}}')
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(db_file))
    backup_dir = tmp_path / "backups"
    result = create_timestamped_backup(backup_dir=str(backup_dir))
    assert result is not None
    assert os.path.exists(result)
    assert os.path.basename(result).startswith("Database_backup_")


def test_create_backup_no_db_returns_none(tmp_path, monkeypatch):
    from core.data_manager import create_timestamped_backup
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(tmp_path / "missing.json"))
    result = create_timestamped_backup(backup_dir=str(tmp_path / "backups"))
    assert result is None


def test_create_backup_prunes_old_files(tmp_path, monkeypatch):
    from core.data_manager import create_timestamped_backup
    db_file = tmp_path / "Database.json"
    db_file.write_text('{"users": {}}')
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(db_file))
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    # Create 12 dummy backup files older than what we'll create next
    for i in range(12):
        old = backup_dir / f"Database_backup_2025-01-{i+1:02d}_000000.json"
        old.write_text("{}")

    create_timestamped_backup(backup_dir=str(backup_dir), max_backups=10)
    remaining = list(backup_dir.glob("Database_backup_*.json"))
    assert len(remaining) <= 10
