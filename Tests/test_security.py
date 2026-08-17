import json
import pytest
from core.security import SecurityManager
from core.data_manager import user_exists
from core.exceptions import AccountLockedError, AuthenticationError, PasswordValidationError


@pytest.fixture(autouse=True)
def clean_test_db(tmp_path, monkeypatch):
    f = tmp_path / "test_sec_db.json"
    with open(f, "w", encoding="utf-8") as fp:
        json.dump({"users": {}}, fp)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(f))


def test_hash_and_verify():
    hashed = SecurityManager.hash_password("MyPassword123")
    assert ":" in hashed
    assert SecurityManager.verify_password(hashed, "MyPassword123")
    assert not SecurityManager.verify_password(hashed, "WrongPassword")
    assert not SecurityManager.verify_password("invalid_format", "MyPassword123")


def test_password_strength_raises_on_invalid():
    with pytest.raises(PasswordValidationError, match="required"):
        SecurityManager.validate_password_strength("")
    with pytest.raises(PasswordValidationError, match="8 characters"):
        SecurityManager.validate_password_strength("Short1")
    with pytest.raises(PasswordValidationError, match="uppercase"):
        SecurityManager.validate_password_strength("nouppercase1")
    with pytest.raises(PasswordValidationError, match="lowercase"):
        SecurityManager.validate_password_strength("NOLOWERCASE1")
    with pytest.raises(PasswordValidationError, match="digit"):
        SecurityManager.validate_password_strength("NoDigitsHere")


def test_password_strength_valid():
    SecurityManager.validate_password_strength("ValidPass1")  # no exception


def test_password_match_raises():
    with pytest.raises(PasswordValidationError, match="do not match"):
        SecurityManager.validate_password_match("Secret123", "Different123")
    with pytest.raises(PasswordValidationError):
        SecurityManager.validate_password_match("", "Secret123")
    with pytest.raises(PasswordValidationError):
        SecurityManager.validate_password_match("Secret123", "")


def test_password_match_valid():
    SecurityManager.validate_password_match("Secret123", "Secret123")  # no exception


def test_register_success_and_duplicate():
    SecurityManager.register_user("Alice", "StrongPass1", "StrongPass1",
                                   security_question="First pet?", security_answer="Fluffy")
    assert user_exists("Alice")

    with pytest.raises(AuthenticationError, match="already exists"):
        SecurityManager.register_user("Alice", "StrongPass1", "StrongPass1",
                                       security_question="First pet?", security_answer="Fluffy")


def test_register_rejects_blank_username():
    with pytest.raises(AuthenticationError, match="required"):
        SecurityManager.register_user("", "StrongPass1", "StrongPass1",
                                       security_question="First pet?", security_answer="Fluffy")


def test_register_requires_security_question_and_answer():
    with pytest.raises(AuthenticationError, match="Security question is required"):
        SecurityManager.register_user("NoQUser", "StrongPass1", "StrongPass1", security_question="", security_answer="Answer")

    with pytest.raises(PasswordValidationError, match="at least 3 characters"):
        SecurityManager.register_user("ShortAUser", "StrongPass1", "StrongPass1", security_question="Question?", security_answer="ab")


def test_authenticate_success():
    SecurityManager.register_user("Bob", "StrongPass1", "StrongPass1",
                                   security_question="First pet?", security_answer="Fluffy")
    assert SecurityManager.authenticate("Bob", "StrongPass1") is True


def test_authenticate_wrong_password_raises():
    SecurityManager.register_user("Carol", "StrongPass1", "StrongPass1",
                                   security_question="First pet?", security_answer="Fluffy")
    with pytest.raises(AuthenticationError):
        SecurityManager.authenticate("Carol", "WrongPassword1")


def test_authenticate_nonexistent_user_raises():
    with pytest.raises(AuthenticationError):
        SecurityManager.authenticate("Ghost", "StrongPass1")


def test_lockout_after_failures():
    SecurityManager.register_user("Dave", "StrongPass1", "StrongPass1",
                                   security_question="First pet?", security_answer="Fluffy")

    for _ in range(3):
        try:
            SecurityManager.authenticate("Dave", "WrongPass1")
        except AuthenticationError:
            pass

    remaining = SecurityManager.get_lockout_remaining("Dave")
    assert remaining > 0

    with pytest.raises(AccountLockedError) as exc_info:
        SecurityManager.authenticate("Dave", "StrongPass1")
    assert int(str(exc_info.value)) > 0


def test_verify_login_backward_compat():
    SecurityManager.register_user("Eve", "StrongPass1", "StrongPass1",
                                   security_question="First pet?", security_answer="Fluffy")
    assert SecurityManager.verify_login("Eve", "StrongPass1") is True
    assert SecurityManager.verify_login("Eve", "WrongPass1") is False
    assert SecurityManager.verify_login("NonExistent", "StrongPass1") is False


def test_change_password_flow():
    SecurityManager.register_user("Frank", "OldPassword1", "OldPassword1",
                                   security_question="First pet?", security_answer="Fluffy")
    assert SecurityManager.authenticate("Frank", "OldPassword1") is True

    # Wrong current password
    with pytest.raises(AuthenticationError, match="incorrect"):
        SecurityManager.change_password("Frank", "WrongOld1", "NewPassword2", "NewPassword2")

    # Mismatched confirmation
    with pytest.raises(PasswordValidationError, match="do not match"):
        SecurityManager.change_password("Frank", "OldPassword1", "NewPassword2", "Mismatch2")

    # Same new password as old password
    with pytest.raises(PasswordValidationError, match="same as the current password"):
        SecurityManager.change_password("Frank", "OldPassword1", "OldPassword1", "OldPassword1")

    # Weak new password
    with pytest.raises(PasswordValidationError, match="8 characters"):
        SecurityManager.change_password("Frank", "OldPassword1", "Short1", "Short1")

    # Successful change
    assert SecurityManager.change_password("Frank", "OldPassword1", "NewPassword2", "NewPassword2") is True
    assert SecurityManager.authenticate("Frank", "NewPassword2") is True
    with pytest.raises(AuthenticationError):
        SecurityManager.authenticate("Frank", "OldPassword1")


def test_security_question_and_recovery_flow():
    SecurityManager.register_user("Grace", "Password123", "Password123",
                                   security_question="First pet?", security_answer="Fluffy")
    assert SecurityManager.get_security_question("Grace") == "First pet?"

    with pytest.raises(AuthenticationError, match="User not found"):
        SecurityManager.get_security_question("NonExistent")

    # Incorrect answer
    with pytest.raises(AuthenticationError, match="incorrect"):
        SecurityManager.recover_password("Grace", "WrongAnswer", "NewPass456", "NewPass456")

    # Successful recovery (case-insensitive answer)
    assert SecurityManager.recover_password("Grace", "fluffy", "NewPass456", "NewPass456") is True
    assert SecurityManager.authenticate("Grace", "NewPass456") is True


def test_security_question_persists_after_user_saves(tmp_path, monkeypatch):
    import json
    from core.user import User
    f = tmp_path / "test_persist_sec.json"
    with open(f, "w", encoding="utf-8") as fp:
        json.dump({"users": {}}, fp)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(f))

    SecurityManager.register_user("PersistUser", "Password123", "Password123",
                                   security_question="Secret question?", security_answer="SecretAnswer")
    
    # Load user via domain model and perform save operations
    u = User("PersistUser")
    u.add_transaction("food", 50.0)
    u.save()

    # Verify that security question still exists and can be retrieved
    assert SecurityManager.get_security_question("PersistUser") == "Secret question?"
    assert SecurityManager.recover_password("PersistUser", "secretanswer", "NewPass999", "NewPass999") is True