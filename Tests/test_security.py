"""
Security Module Unit Tests
==========================
Validates hashing, verification, complexity checks, and brute-force lockouts.
"""
import pytest
from core.security import SecurityManager


@pytest.fixture(autouse=True)
def reset_security_state():
    """Ensure brute-force tracking dictionaries are cleared before and after each test."""
    SecurityManager._failed_attempts.clear()
    SecurityManager._lockout_until.clear()
    yield
    SecurityManager._failed_attempts.clear()
    SecurityManager._lockout_until.clear()


def test_password_hashing_and_verification():
    """Passwords hash correctly and match their verification check."""
    pwd = "SecurePassword1"
    hashed = SecurityManager.hash_password(pwd)
    assert ":" in hashed
    assert SecurityManager.verify_password(hashed, pwd) is True
    assert SecurityManager.verify_password(hashed, "WrongPassword") is False


def test_password_strength_validation():
    """Complexity enforcement checks criteria strictly."""
    assert SecurityManager.validate_password_strength("short1A")[0] is False
    assert SecurityManager.validate_password_strength("nouppercase1")[0] is False
    assert SecurityManager.validate_password_strength("NOLOWERCASE1")[0] is False
    assert SecurityManager.validate_password_strength("NoDigitsHere")[0] is False
    assert SecurityManager.validate_password_strength("ValidPass1")[0] is True


def test_brute_force_lockout(monkeypatch):
    """Three failed login attempts must trigger an active lockout."""
    hashed_pw = SecurityManager.hash_password("ValidPass1")
    # Return the user dictionary directly to avoid key/normalization mismatches in the test mock
    monkeypatch.setattr("core.security.load_user", lambda name: {"password_hash": hashed_pw})

    # 3 failed attempts
    assert SecurityManager.verify_login("lockoutuser", "WrongPass1") is False
    assert SecurityManager.verify_login("lockoutuser", "WrongPass2") is False
    assert SecurityManager.verify_login("lockoutuser", "WrongPass3") is False
    
    # Verify lockout is active and blocks correct passwords during the window
    assert SecurityManager.get_lockout_remaining("lockoutuser") > 0
    assert SecurityManager.verify_login("lockoutuser", "ValidPass1") is False