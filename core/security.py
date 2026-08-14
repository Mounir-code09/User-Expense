"""Password security, validation, and lockout management."""
import hashlib
import hmac
import os
import time

from .data_manager import (
    default_user_profile,
    load_user,
    normalize_username,
    save_user,
    user_exists,
)


class SecurityManager:
    """Handles password hashing, validation, registration, and lockouts."""

    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30

    @staticmethod
    def _get_security_meta(username):
        """Helper to get user data with lockout fields initialized."""
        user_data = load_user(username)
        user_data.setdefault("failed_attempts", 0)
        user_data.setdefault("lockout_until", 0)
        return user_data

    @staticmethod
    def hash_password(password):
        """Hash a password using PBKDF2-SHA256 with a random salt."""
        salt = os.urandom(16).hex()
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
        ).hex()
        return f"{salt}:{pwd_hash}"

    @staticmethod
    def verify_password(stored_hash, provided_password):
        """Verify provided password against stored salt:hash string."""
        try:
            salt, expected_hash = stored_hash.split(":")
            pwd_hash = hashlib.pbkdf2_hmac(
                "sha256", provided_password.encode("utf-8"), bytes.fromhex(salt), 100_000
            ).hex()
            return hmac.compare_digest(pwd_hash, expected_hash)
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password):
        """Validate password meets length and character requirements."""
        if not password or not password.strip():
            return False, "Password is required."
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit."
        return True, ""

    @staticmethod
    def validate_password_match(password, confirm):
        """Verify that password and confirmation match."""
        if not password:
            return False, "Password is required."
        if not confirm:
            return False, "Password confirmation is required."
        if password != confirm:
            return False, "Passwords do not match."
        return True, ""

    @staticmethod
    def register_user(username, password, confirm):
        """Register a new user profile after validation."""
        norm_name = normalize_username(username)
        if not norm_name:
            return False, "Username is required."

        if user_exists(norm_name):
            return False, "Username already exists."

        match_valid, match_msg = SecurityManager.validate_password_match(password, confirm)
        if not match_valid:
            return False, match_msg

        strength_valid, strength_msg = SecurityManager.validate_password_strength(password)
        if not strength_valid:
            return False, strength_msg

        profile = default_user_profile()
        profile["password_hash"] = SecurityManager.hash_password(password)
        save_user(norm_name, profile)
        return True, ""

    @staticmethod
    def get_lockout_remaining(username):
        """Return remaining lockout duration in seconds."""
        norm_name = normalize_username(username)
        if not norm_name:
            return 0

        user_data = SecurityManager._get_security_meta(norm_name)
        lockout_until = user_data.get("lockout_until", 0)
        if lockout_until <= 0:
            return 0

        remaining = int(lockout_until - time.time())
        if remaining > 0:
            return remaining

        # Lockout period expired: reset lockout state
        user_data["lockout_until"] = 0
        user_data["failed_attempts"] = 0
        save_user(norm_name, user_data)
        return 0

    @staticmethod
    def verify_login(username, password):
        """Authenticate user credentials and handle brute-force lockout."""
        norm_name = normalize_username(username)
        if not user_exists(norm_name):
            return False

        if SecurityManager.get_lockout_remaining(norm_name) > 0:
            return False

        user_data = SecurityManager._get_security_meta(norm_name)
        if SecurityManager.verify_password(user_data.get("password_hash", ""), password):
            user_data["failed_attempts"] = 0
            user_data["lockout_until"] = 0
            save_user(norm_name, user_data)
            return True

        user_data["failed_attempts"] += 1
        if user_data["failed_attempts"] >= SecurityManager.MAX_ATTEMPTS:
            user_data["lockout_until"] = time.time() + SecurityManager.LOCKOUT_DURATION

        save_user(norm_name, user_data)
        return False