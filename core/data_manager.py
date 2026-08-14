"""Database helpers for users, categories, transactions, incomes, and JSON persistence."""
import copy
import json
import os
import shutil
import uuid

DATABASE_FILE = "Database.json"

DEFAULT_CATEGORIES = [
    "food", "transport", "housing", "entertainment",
    "shopping", "health", "education", "miscellaneous",
]

DEFAULT_USER_TEMPLATE = {
    "currency": "USD",
    "categories": DEFAULT_CATEGORIES.copy(),
    "budget_limits": {},
    "transactions": [],
    "incomes": [],
    "password_hash": "",
    "failed_attempts": 0,
    "lockout_until": 0,
}


def default_user_profile():
    """Return a fresh copy of the default user template."""
    return copy.deepcopy(DEFAULT_USER_TEMPLATE)


def set_database_file(filename):
    """Set the active database file path."""
    global DATABASE_FILE
    DATABASE_FILE = filename


def load_database():
    """Load database from file or return empty structure if missing or corrupt."""
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
        try:
            shutil.copy(DATABASE_FILE, f"{DATABASE_FILE}.corrupt.bak")
        except OSError:
            pass
        return {"users": {}}


def save_database(data):
    """Write database safely using temporary file replacement."""
    temp_file = f"{DATABASE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temp_file, DATABASE_FILE)


def normalize_username(name):
    """Normalize username by trimming and title-casing."""
    if not name:
        return ""
    return name.strip().title()


def _migrate_user_data(raw_data):
    """Migrate legacy user profile schemas to support transactions, incomes, and custom categories."""
    profile = default_user_profile()
    profile.update(raw_data)

    if "categories" not in profile or not profile["categories"]:
        profile["categories"] = DEFAULT_CATEGORIES.copy()

    if "budget_limit" in profile and "budget_limits" not in raw_data:
        profile["budget_limits"] = profile.pop("budget_limit")

    if "transactions" not in profile:
        profile["transactions"] = []

    if "incomes" not in profile:
        profile["incomes"] = []

    if not profile["transactions"] and "current_expenses" in profile:
        for cat, amount in profile["current_expenses"].items():
            if amount > 0:
                profile["transactions"].append({
                    "id": f"legacy_{uuid.uuid4().hex[:8]}",
                    "date": "2026-01-01",
                    "category": cat.lower().strip(),
                    "amount": round(float(amount), 2),
                    "note": "Initial balance",
                })

    return profile


def load_user(username):
    """Load user profile or return default template with schema migration."""
    norm_name = normalize_username(username)
    if not norm_name:
        return default_user_profile()
    database = load_database()
    raw = database["users"].get(norm_name)
    if raw is None:
        return default_user_profile()
    return _migrate_user_data(raw)


def save_user(username, user_data_dict):
    """Persist a user profile to the database."""
    norm_name = normalize_username(username)
    if not norm_name:
        return
    database = load_database()
    database["users"][norm_name] = user_data_dict
    save_database(database)


def delete_user_data(username):
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


def user_exists(username):
    """Check if username exists in database."""
    norm_name = normalize_username(username)
    if not norm_name:
        return False
    return norm_name in get_all_usernames()