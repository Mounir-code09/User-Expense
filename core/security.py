import hashlib
import hmac
import secrets
import time

from .data_manager import (
    default_user_profile,
    load_user,
    normalize_username,
    save_user,
    user_exists,
)
from .exceptions import (
    AccountLockedError,
    AuthenticationError,
    PasswordValidationError,
)


class SecurityManager:

    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30
    HASH_ITERATIONS = 600_000

    @staticmethod
    def _get_security_meta(username):
        user_data = load_user(username)
        user_data.setdefault("failed_attempts", 0)
        user_data.setdefault("lockout_until", 0)
        return user_data

    @staticmethod
    def hash_password(password):
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            SecurityManager.HASH_ITERATIONS,
        ).hex()
        return f"{salt}:{pwd_hash}"

    @staticmethod
    def verify_password(stored_hash, provided_password):
        try:
            parts = stored_hash.split(":", 1)
            if len(parts) != 2:
                return False
            salt, expected = parts
            pwd_hash = hashlib.pbkdf2_hmac(
                "sha256",
                provided_password.encode("utf-8"),
                bytes.fromhex(salt),
                SecurityManager.HASH_ITERATIONS,
            ).hex()
            if hmac.compare_digest(pwd_hash, expected):
                return True
            # Support legacy iterations
            legacy = hashlib.pbkdf2_hmac(
                "sha256",
                provided_password.encode("utf-8"),
                bytes.fromhex(salt),
                100_000,
            ).hex()
            return hmac.compare_digest(legacy, expected)
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password):
        if not password or not password.strip():
            raise PasswordValidationError("Password is required.")
        if len(password) < 8:
            raise PasswordValidationError("Password must be at least 8 characters long.")
        if len(password) > 128:
            raise PasswordValidationError("Password cannot exceed 128 characters.")
        if not any(c.isupper() for c in password):
            raise PasswordValidationError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            raise PasswordValidationError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password):
            raise PasswordValidationError("Password must contain at least one digit.")

    @staticmethod
    def validate_password_match(password, confirm):
        if not password:
            raise PasswordValidationError("Password is required.")
        if not confirm:
            raise PasswordValidationError("Password confirmation is required.")
        if password != confirm:
            raise PasswordValidationError("Passwords do not match.")

    @staticmethod
    def register_user(username, password, confirm, security_question="", security_answer=""):
        norm = normalize_username(username)
        if not norm:
            raise AuthenticationError("Username is required.")
        if len(norm) > 50:
            raise AuthenticationError("Username cannot exceed 50 characters.")
        if user_exists(norm):
            raise AuthenticationError("Username already exists.")

        SecurityManager.validate_password_match(password, confirm)
        SecurityManager.validate_password_strength(password)

        profile = default_user_profile()
        profile["password_hash"] = SecurityManager.hash_password(password)

        q = (security_question or "").strip()
        a = (security_answer or "").strip().lower()
        if not q:
            raise AuthenticationError("Security question is required.")
        if len(a) < 3:
            raise PasswordValidationError("Security answer must be at least 3 characters long.")

        profile["security_question"] = q
        profile["security_answer_hash"] = SecurityManager.hash_password(a)

        save_user(norm, profile)

    @staticmethod
    def get_security_question(username):
        norm = normalize_username(username)
        if not user_exists(norm):
            raise AuthenticationError("User not found.")
        user_data = load_user(norm)
        q = user_data.get("security_question", "").strip()
        if not q:
            raise AuthenticationError("No security question configured for this account.")
        return q

    @staticmethod
    def recover_password(username, security_answer, new_password, confirm_password):
        norm = normalize_username(username)
        if not user_exists(norm):
            raise AuthenticationError("User not found.")

        remaining = SecurityManager.get_lockout_remaining(norm)
        if remaining > 0:
            raise AccountLockedError(str(remaining))

        user_data = SecurityManager._get_security_meta(norm)
        stored_hash = user_data.get("security_answer_hash", "")
        if not stored_hash:
            raise AuthenticationError("No security question configured for this account.")

        answer_normalised = (security_answer or "").strip().lower()
        if not SecurityManager.verify_password(stored_hash, answer_normalised):
            user_data["failed_attempts"] = user_data.get("failed_attempts", 0) + 1
            if user_data["failed_attempts"] >= SecurityManager.MAX_ATTEMPTS:
                user_data["lockout_until"] = time.time() + SecurityManager.LOCKOUT_DURATION
            save_user(norm, user_data)
            raise AuthenticationError("Security answer is incorrect.")

        SecurityManager.validate_password_match(new_password, confirm_password)
        SecurityManager.validate_password_strength(new_password)

        user_data["password_hash"] = SecurityManager.hash_password(new_password)
        user_data["failed_attempts"] = 0
        user_data["lockout_until"] = 0
        save_user(norm, user_data)
        return True

    @staticmethod
    def change_password(username, current_password, new_password, confirm_password):
        norm = normalize_username(username)
        if not user_exists(norm):
            raise AuthenticationError("User not found.")

        user_data = SecurityManager._get_security_meta(norm)
        if not SecurityManager.verify_password(user_data.get("password_hash", ""), current_password):
            raise AuthenticationError("Current password is incorrect.")

        if current_password == new_password:
            raise PasswordValidationError("New password cannot be the same as the current password.")

        SecurityManager.validate_password_match(new_password, confirm_password)
        SecurityManager.validate_password_strength(new_password)

        user_data["password_hash"] = SecurityManager.hash_password(new_password)
        save_user(norm, user_data)
        return True

    @staticmethod
    def get_lockout_remaining(username):
        norm = normalize_username(username)
        if not norm:
            return 0
        user_data = SecurityManager._get_security_meta(norm)
        lockout_until = user_data.get("lockout_until", 0)
        if lockout_until <= 0:
            return 0
        remaining = int(lockout_until - time.time())
        if remaining > 0:
            return remaining
        user_data["lockout_until"] = 0
        user_data["failed_attempts"] = 0
        save_user(norm, user_data)
        return 0

    @staticmethod
    def authenticate(username, password):  # raises AccountLockedError or AuthenticationError; returns True on success
        norm = normalize_username(username)
        if not user_exists(norm):
            raise AuthenticationError("Invalid username or password.")

        remaining = SecurityManager.get_lockout_remaining(norm)
        if remaining > 0:
            raise AccountLockedError(str(remaining))

        user_data = SecurityManager._get_security_meta(norm)
        if SecurityManager.verify_password(user_data.get("password_hash", ""), password):
            user_data["failed_attempts"] = 0
            user_data["lockout_until"] = 0
            save_user(norm, user_data)
            return True

        user_data["failed_attempts"] += 1
        if user_data["failed_attempts"] >= SecurityManager.MAX_ATTEMPTS:
            user_data["lockout_until"] = time.time() + SecurityManager.LOCKOUT_DURATION

        save_user(norm, user_data)
        raise AuthenticationError("Invalid username or password.")

    @staticmethod
    def verify_login(username, password):  # boolean shim around authenticate() for backward compatibility
        try:
            return SecurityManager.authenticate(username, password)
        except (AuthenticationError, AccountLockedError):
            return False