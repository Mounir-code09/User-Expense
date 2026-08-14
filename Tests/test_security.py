"""Password hashing, validation, and login security tests."""
import pytest
from core.security import SecurityManager


@pytest.fixture(autouse=True)
def reset_security_state():
    """Clear brute-force tracking before and after each test."""
    SecurityManager._failed_attempts.clear()
    SecurityManager._lockout_until.clear()
    yield
    SecurityManager._failed_attempts.clear()
    SecurityManager._lockout_until.clear()


def test_password_hashing_and_verification():
    """Verify password hashing and matching works correctly."""
    pwd = "SecurePassword1"
    hashed = SecurityManager.hash_password(pwd)
    assert ":" in hashed
    assert SecurityManager.verify_password(hashed, pwd) is True
    assert SecurityManager.verify_password(hashed, "WrongPassword") is False


def test_password_strength_validation():
    """Validate password strength rules are enforced."""
    assert SecurityManager.validate_password_strength("short1A") == (False, "Password must be at least 8 characters long.")
    assert SecurityManager.validate_password_strength("nouppercase1") == (False, "Password must contain at least one uppercase letter.")
    assert SecurityManager.validate_password_strength("NOLOWERCASE1") == (False, "Password must contain at least one lowercase letter.")
    assert SecurityManager.validate_password_strength("NoDigitsHere") == (False, "Password must contain at least one digit.")
    assert SecurityManager.validate_password_strength("ValidPass1") == (True, "")


def test_password_confirmation_validation():
    """Verify password confirmation matching is enforced."""
    assert SecurityManager.validate_password_match("ValidPass1", "ValidPass1") == (True, "")
    assert SecurityManager.validate_password_match("ValidPass1", "WrongPass1") == (False, "Passwords do not match.")
    assert SecurityManager.validate_password_match("", "ValidPass1") == (False, "Password is required.")
    assert SecurityManager.validate_password_match("ValidPass1", "") == (False, "Password confirmation is required.")


def test_register_user_rejects_blank_values():
    """Reject registration with empty username or password."""
    assert SecurityManager.register_user("  ", "ValidPass1", "ValidPass1") == (False, "Username is required.")
    # Whitespace-only password fails strength check (too short)
    result = SecurityManager.register_user("Alice", "   ", "   ")
    assert result[0] is False
    assert "characters" in result[1]


def test_brute_force_lockout(monkeypatch):
    """Verify 3 failed attempts trigger 30-second lockout."""
    hashed_pw = SecurityManager.hash_password("ValidPass1")
    monkeypatch.setattr("core.security.load_user", lambda name: {"password_hash": hashed_pw})

    assert SecurityManager.verify_login("lockoutuser", "WrongPass1") is False
    assert SecurityManager.verify_login("lockoutuser", "WrongPass2") is False
    assert SecurityManager.verify_login("lockoutuser", "WrongPass3") is False
    
    assert SecurityManager.get_lockout_remaining("lockoutuser") > 0
    assert SecurityManager.verify_login("lockoutuser", "ValidPass1") is False


def test_register_user_password_mismatch(monkeypatch):
    """Reject registration when passwords don't match."""
    monkeypatch.setattr("core.security.user_exists", lambda name: False)
    result = SecurityManager.register_user("NewUser", "ValidPass1", "DifferentPass1")
    assert result == (False, "Passwords do not match.")


def test_register_user_weak_password(monkeypatch):
    """Reject registration with weak password."""
    monkeypatch.setattr("core.security.user_exists", lambda name: False)
    result = SecurityManager.register_user("NewUser", "weak", "weak")
    assert result[0] is False
    assert "characters" in result[1] or "uppercase" in result[1] or "lowercase" in result[1]


def test_register_user_success(monkeypatch):
    """Successfully register new user with matching passwords."""
    monkeypatch.setattr("core.security.user_exists", lambda name: False)
    monkeypatch.setattr("core.security.load_user", lambda name: {})
    monkeypatch.setattr("core.security.save_user", lambda name, data: None)
    
    result = SecurityManager.register_user("NewUser", "ValidPass1", "ValidPass1")
    assert result == (True, "")


def test_register_user_existing_username(monkeypatch):
    """Reject registration for existing username."""
    monkeypatch.setattr("core.security.user_exists", lambda name: True)
    result = SecurityManager.register_user("ExistingUser", "ValidPass1", "ValidPass1")
    assert result[0] is False
    assert "already exists" in result[1]