"""Database helpers for users, categories, and JSON persistence."""
import copy
import json
import os
import shutil

DATABASE_FILE = "Database.json"

VALID_CATEGORIES = [
    "food", "transport", "housing", "entertainment",
    "shopping", "health", "education", "miscellaneous",
]

DEFAULT_USER_TEMPLATE = {
    "currency": "USD",
    "budget_limit": {},
    "current_expenses": {},
    "password_hash": "",
    "failed_attempts": 0,
    "lockout_until": 0,
}


def default_user_profile():
    """Return a copy of the default user template."""
    return copy.deepcopy(DEFAULT_USER_TEMPLATE)


def set_database_file(filename: str):
    """Set the active database file path."""
    global DATABASE_FILE
    DATABASE_FILE = filename


def load_database():
    """Load database from file or return empty structure if missing."""
    if not os.path.exists(DATABASE_FILE):
        return {"users": {}}
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                return {"users": {}}
            data.setdefault("users", {})
            return data
    except (json.JSONDecodeError, OSError):
        # Backup corrupted file before resetting
        try:
            shutil.copy(DATABASE_FILE, f"{DATABASE_FILE}.corrupt.bak")
        except OSError:
            pass
        return {"users": {}}


def save_database(data: dict):
    """Write database safely using temporary file replacement."""
    temp_file = f"{DATABASE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temp_file, DATABASE_FILE)


def normalize_username(name: str):
    """Normalize username by trimming and title-casing."""
    if not name:
        return ""
    return name.strip().title()


def load_user(username: str):
    """Load user profile or return default template."""
    norm_name = normalize_username(username)
    if not norm_name:
        return default_user_profile()
    database = load_database()
    return database["users"].get(norm_name, default_user_profile())


def save_user(username: str, user_data_dict: dict):
    """Persist a user profile to the database."""
    norm_name = normalize_username(username)
    if not norm_name:
        return
    database = load_database()
    database["users"][norm_name] = user_data_dict
    save_database(database)


def delete_user_data(username: str):
    """Delete user record. Return True if user existed."""
    norm_name = normalize_username(username)
    if not norm_name:
        return False
    database = load_database()
    if norm_name in database["users"]:
        del database["users"][norm_name]
        save_database(database)
        return True
    return False


def get_all_usernames():
    """Return list of all stored usernames."""
    database = load_database()
    return list(database["users"].keys())


def user_exists(username: str):
    """Check if username exists in database."""
    norm_name = normalize_username(username)
    if not norm_name:
        return False
    return norm_name in get_all_usernames()


def cat_v(category_name: str):
    """Validate if category is in VALID_CATEGORIES."""
    if not category_name:
        return False
    return category_name.lower().strip() in VALID_CATEGORIES