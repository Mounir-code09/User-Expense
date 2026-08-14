"""Security, authentication, password hashing, and lockout unit tests."""
import json
import pytest
from core.security import SecurityManager
from core.data_manager import load_user, save_user, user_exists


@pytest.fixture(autouse=True)
def clean_test_db(tmp_path, monkeypatch):
    """Use a temporary database file for each test."""
    test_file = tmp_path / "test_sec_db.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"users": {}}, f)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(test_file))


def test_hash_and_verify_password():
    """Passwords hash to salt:hash strings and verify accurately."""
    hashed = SecurityManager.hash_password("MyPassword123")
    assert ":" in hashed
    assert SecurityManager.verify_password(hashed, "MyPassword123") is True
    assert SecurityManager.verify_password(hashed, "WrongPassword") is False
    assert SecurityManager.verify_password("invalid_format", "MyPassword123") is False


def test_password_strength_validation():
    """Enforce length, upper, lower, and digit requirements."""
    valid, _ = SecurityManager.validate_password_strength("ValidPass1")
    assert valid is True

    # Empty
    valid, msg = SecurityManager.validate_password_strength("")
    assert valid is False
    assert "required" in msg.lower()

    # Too short
    valid, msg = SecurityManager.validate_password_strength("Short1")
    assert valid is False
    assert "8 characters" in msg.lower()

    # Missing uppercase
    valid, msg = SecurityManager.validate_password_strength("nouppercase1")
    assert valid is False
    assert "uppercase" in msg.lower()

    # Missing lowercase
    valid, msg = SecurityManager.validate_password_strength("NOLOWERCASE1")
    assert valid is False
    assert "lowercase" in msg.lower()

    # Missing digit
    valid, msg = SecurityManager.validate_password_strength("NoDigitsHere")
    assert valid is False
    assert "digit" in msg.lower()


def test_password_match_validation():
    """Verify password and confirmation matching."""
    valid, _ = SecurityManager.validate_password_match("Secret123", "Secret123")
    assert valid is True

    valid, msg = SecurityManager.validate_password_match("Secret123", "Different123")
    assert valid is False
    assert "do not match" in msg.lower()

    valid, msg = SecurityManager.validate_password_match("", "Secret123")
    assert valid is False

    valid, msg = SecurityManager.validate_password_match("Secret123", "")
    assert valid is False


def test_register_user_success_and_duplicates():
    """Register a new user and reject duplicates."""
    success, msg = SecurityManager.register_user("Alice", "StrongPass1", "StrongPass1")
    assert success is True
    assert msg == ""
    assert user_exists("Alice") is True

    # Duplicate registration
    success, msg = SecurityManager.register_user("Alice", "StrongPass1", "StrongPass1")
    assert success is False
    assert "already exists" in msg.lower()

    # Empty username
    success, msg = SecurityManager.register_user("", "StrongPass1", "StrongPass1")
    assert success is False
    assert "required" in msg.lower()


def test_verify_login_and_lockout():
    """Test login verification and temporary lockout after 3 failed attempts."""
    SecurityManager.register_user("Bob", "StrongPass1", "StrongPass1")

    # Non-existent user
    assert SecurityManager.verify_login("NonExistent", "StrongPass1") is False

    # Correct login
    assert SecurityManager.verify_login("Bob", "StrongPass1") is True

    # Failed attempts
    assert SecurityManager.verify_login("Bob", "WrongPass1") is False
    assert SecurityManager.verify_login("Bob", "WrongPass2") is False
    assert SecurityManager.verify_login("Bob", "WrongPass3") is False

    # Account should now be locked
    remaining = SecurityManager.get_lockout_remaining("Bob")
    assert remaining > 0

    # Even correct password fails during lockout
    assert SecurityManager.verify_login("Bob", "StrongPass1") is False