"""
Data Manager Module
-------------------
Handles JSON database persistence, user record CRUD operations, and category validation.

All user data — including salted password hashes — lives in a single ``Database.json`` file.
Writes use atomic replacement (``.tmp`` → rename) to prevent corruption during crashes.
"""
import os
import json
import copy

DATABASE_FILE = "Database.json"

# Canonical expense categories accepted by the application
VALID_CATEGORIES = [
    "food", "transport", "housing", "entertainment",
    "shopping", "health", "education", "miscellaneous",
]

# Default profile template returned for users that do not yet exist in the database
DEFAULT_USER_TEMPLATE = {
    "currency": "USD",
    "budget_limit": {},
    "current_expenses": {},
    "password_hash": "",
}


def default_user_profile():
    """
    Return a brand-new, fully independent copy of the default profile template.

    This ensures that each new user gets their own dict, so changes to one profile
    do not accidentally mutate the template or other users' data.
    """
    return copy.deepcopy(DEFAULT_USER_TEMPLATE)


def set_database_file(filename: str):
    """Point the module at a specific database file (used at application startup)."""
    global DATABASE_FILE
    DATABASE_FILE = filename


def load_database():
    """
    Load the full database from disk.

    Returns an empty ``{"users": {}}`` structure when the file is missing or corrupt,
    allowing the application to recover gracefully instead of crashing.
    """
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            data.setdefault("users", {})
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}}


def save_database(data: dict):
    """
    Persist the database atomically.

    Data is first written to a temporary file, then renamed over the target path so a
    crash mid-write never leaves a half-written JSON document.
    """
    temp_file = f"{DATABASE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temp_file, DATABASE_FILE)


def load_user(username: str):
    """Return a user's profile dict, or the default template if the user is new."""
    database = load_database()
    if username in database["users"]:
        return database["users"][username]
    return default_user_profile()


def save_user(username: str, user_data_dict: dict):
    """Create or overwrite a user record inside the database."""
    database = load_database()
    database["users"][username] = user_data_dict
    save_database(database)


def delete_user_data(username: str):
    """
    Permanently remove a user record (profile, expenses, budget, and password hash).

    Returns ``True`` when the user existed and was deleted, ``False`` otherwise.
    """
    database = load_database()
    if username in database["users"]:
        del database["users"][username]
        save_database(database)
        return True
    return False


def get_all_usernames():
    """Return a list of every registered username currently stored in the database."""
    database = load_database()
    return list(database["users"].keys())


def user_exists(username: str):
    """Check whether a username already has a record in the database."""
    return username in get_all_usernames()


def cat_v(category_name: str):
    """
    Validate a category string against the allowed list.

    Returns ``True`` when the normalized category is recognized, ``False`` otherwise.
    """
    if not category_name:
        return False
    return category_name.lower().strip() in VALID_CATEGORIES


def normalize_username(name: str):
    """
    Normalize a raw username for consistent storage and lookup.

    Strips surrounding whitespace and applies title-casing (e.g. ``"alice"`` → ``"Alice"``).
    """
    return name.strip().title()
