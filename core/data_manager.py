import copy
from datetime import datetime
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
    "templates": {
        "expenses": [],
        "incomes": [],
    },
    "password_hash": "",
    "security_question": "",
    "security_answer_hash": "",
    "failed_attempts": 0,
    "lockout_until": 0,
    "payee_rules": {},
    "savings_goals": [],
}


def default_user_profile():
    return copy.deepcopy(DEFAULT_USER_TEMPLATE)


def set_database_file(filename):
    global DATABASE_FILE
    DATABASE_FILE = filename


def load_database():
    if not os.path.exists(DATABASE_FILE):
        return {"users": {}}
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
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
    temp = f"{DATABASE_FILE}.tmp"
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp, DATABASE_FILE)
    except OSError:
        if os.path.exists(temp):
            os.remove(temp)
        raise


def normalize_username(name):
    if not name:
        return ""
    return name.strip().title()


def _migrate_user_data(raw_data):
    profile = default_user_profile()
    profile.update(raw_data)

    if not profile.get("categories"):
        profile["categories"] = DEFAULT_CATEGORIES.copy()

    if "budget_limit" in profile and "budget_limits" not in raw_data:
        profile["budget_limits"] = profile.pop("budget_limit")

    profile.setdefault("transactions", [])
    profile.setdefault("incomes", [])
    profile.setdefault("templates", {"expenses": [], "incomes": []})
    profile["templates"].setdefault("expenses", [])
    profile["templates"].setdefault("incomes", [])
    profile.setdefault("security_question", "")
    profile.setdefault("security_answer_hash", "")
    profile.setdefault("payee_rules", {})
    profile.setdefault("savings_goals", [])

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
    norm = normalize_username(username)
    if not norm:
        return default_user_profile()
    db = load_database()
    raw = db["users"].get(norm)
    if raw is None:
        return default_user_profile()
    return _migrate_user_data(raw)


def save_user(username, user_data_dict):
    norm = normalize_username(username)
    if not norm:
        return
    db = load_database()
    db["users"][norm] = user_data_dict
    save_database(db)


def delete_user_data(username):
    norm = normalize_username(username)
    if not norm:
        return False
    db = load_database()
    if norm in db["users"]:
        del db["users"][norm]
        save_database(db)
        return True
    return False


def get_all_usernames():
    return list(load_database()["users"].keys())


def user_exists(username):
    norm = normalize_username(username)
    if not norm:
        return False
    return norm in get_all_usernames()


def create_timestamped_backup(backup_dir="backups", max_backups=10):
    if not os.path.exists(DATABASE_FILE):
        return None
    try:
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"Database_backup_{ts}.json")
        shutil.copy2(DATABASE_FILE, backup_path)

        existing = [
            os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
            if f.startswith("Database_backup_") and f.endswith(".json")
        ]
        if len(existing) > max_backups:
            existing.sort(key=os.path.getmtime)
            for old_file in existing[:-max_backups]:
                try:
                    os.remove(old_file)
                except OSError:
                    pass
        return backup_path
    except OSError:
        return None