"""Password handling and login checks."""

import hashlib
import os
import time

from .data_manager import load_user, normalize_username, save_user, user_exists


class SecurityManager:
    """Handles password hashing, validation, and login lockouts."""

    _failed_attempts = {}
    _lockout_until = {}

    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30

    @staticmethod
    def hash_password(password: str):
        """Hash password with PBKDF2-SHA256 and random salt."""
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"{salt.hex()}:{pwd_hash.hex()}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str):
        """Verify provided password against stored hash."""
        try:
            salt_hex, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100_000)
            return pwd_hash.hex() == hash_hex
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str):
        """Check password meets requirements: 8+ chars, upper, lower, digit. Returns (bool, str)."""
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit."
        return True, ""

    @staticmethod
    def validate_password_match(password: str, confirm_password: str):
        """Verify password confirmation matches password. Returns (bool, str)."""
        if not password or not password.strip():
            return False, "Password is required."
        if not confirm_password or not confirm_password.strip():
            return False, "Password confirmation is required."
        if password != confirm_password:
            return False, "Passwords do not match."
        return True, ""

    @staticmethod
    def register_user(username: str, password: str, confirm_password: str) :
        """Register user with validated username and matching passwords. Returns (bool, str)."""
        norm_name = normalize_username(username)
        if not norm_name or not norm_name.strip():
            return False, "Username is required."

        if user_exists(norm_name):
            return False, f"Username '{norm_name}' already exists."

        is_valid, msg = SecurityManager.validate_password_strength(password)
        if not is_valid:
            return False, msg

        is_match, msg = SecurityManager.validate_password_match(password, confirm_password)
        if not is_match:
            return False, msg

        user_data = load_user(norm_name)
        user_data["password_hash"] = SecurityManager.hash_password(password)
        save_user(norm_name, user_data)
        return True, ""

    @staticmethod
    def get_lockout_remaining(username: str):
        """Return the remaining lockout time in seconds."""
        norm_name = normalize_username(username)
        current_time = time.time()
        if norm_name in SecurityManager._lockout_until:
            remaining = int(SecurityManager._lockout_until[norm_name] - current_time)
            if remaining > 0:
                return remaining
            del SecurityManager._lockout_until[norm_name]
            SecurityManager._failed_attempts[norm_name] = 0
        return 0

    @staticmethod
    def verify_login(username: str, password: str):
        """Authenticate user and enforce 3-attempt lockout for 30 seconds."""
        norm_name = normalize_username(username)
        if not norm_name:
            return False

        current_time = time.time()
        if SecurityManager.get_lockout_remaining(norm_name) > 0:
            return False

        user_data = load_user(norm_name)
        stored_hash = user_data.get("password_hash", "")

        if not stored_hash:
            return False

        if SecurityManager.verify_password(stored_hash, password):
            SecurityManager._failed_attempts[norm_name] = 0
            if norm_name in SecurityManager._lockout_until:
                del SecurityManager._lockout_until[norm_name]
            return True

        attempts = SecurityManager._failed_attempts.get(norm_name, 0) + 1
        SecurityManager._failed_attempts[norm_name] = attempts

        if attempts >= SecurityManager.MAX_ATTEMPTS:
            SecurityManager._lockout_until[norm_name] = current_time + SecurityManager.LOCKOUT_DURATION

        return False