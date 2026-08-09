"""
Security Module
---------------
Handles PBKDF2 password hashing, password strength validation, user registration,
login verification, and brute-force protection (lockout after 3 failed attempts).
"""
import hashlib
import os
import time
from .data_manager import load_user, save_user, normalize_username, user_exists


class SecurityManager:
    """Manages authentication credentials and brute-force protection."""

    # Brute-force protection state tracking
    _failed_attempts = {}
    _lockout_until = {}

    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30  # Lockout duration in seconds after 3 failed attempts

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"{salt.hex()}:{pwd_hash.hex()}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        """Verify a provided password against a stored salt:hash string."""
        try:
            salt_hex, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100_000)
            return pwd_hash.hex() == hash_hex
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str):
        """
        Validate password complexity:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
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
    def register_user(username: str, password: str) -> bool:
        """Register a new user profile with a hashed password stored atomically in the database."""
        norm_name = normalize_username(username)
        if user_exists(norm_name):
            return False

        user_data = load_user(norm_name)
        user_data["password_hash"] = SecurityManager.hash_password(password)
        save_user(norm_name, user_data)
        return True

    @staticmethod
    def get_lockout_remaining(username: str) -> int:
        """Return remaining lockout seconds for a user, or 0 if not locked out."""
        norm_name = normalize_username(username)
        current_time = time.time()
        if norm_name in SecurityManager._lockout_until:
            remaining = int(SecurityManager._lockout_until[norm_name] - current_time)
            if remaining > 0:
                return remaining
            else:
                # Expired
                del SecurityManager._lockout_until[norm_name]
                SecurityManager._failed_attempts[norm_name] = 0
        return 0

    @staticmethod
    def verify_login(username: str, password: str) -> bool:
        """
        Verify login credentials, enforcing an in-memory brute-force lockout 
        after 3 consecutive failures for 30 seconds.
        """
        norm_name = normalize_username(username)
        current_time = time.time()

        # Check if the user is currently locked out
        if SecurityManager.get_lockout_remaining(norm_name) > 0:
            return False

        user_data = load_user(norm_name)
        stored_hash = user_data.get("password_hash", "")

        if not stored_hash:
            return False

        if SecurityManager.verify_password(stored_hash, password):
            # Successful login: reset failure counters
            SecurityManager._failed_attempts[norm_name] = 0
            if norm_name in SecurityManager._lockout_until:
                del SecurityManager._lockout_until[norm_name]
            return True
        else:
            # Failed attempt: increment counter and check threshold
            attempts = SecurityManager._failed_attempts.get(norm_name, 0) + 1
            SecurityManager._failed_attempts[norm_name] = attempts

            if attempts >= SecurityManager.MAX_ATTEMPTS:
                SecurityManager._lockout_until[norm_name] = current_time + SecurityManager.LOCKOUT_DURATION

            return False