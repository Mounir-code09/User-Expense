"""
Data Manager Module
Manages JSON database state preservation, user record mutations, 
and input validation configurations.
"""
import os
import json

DATABASE_FILE = "Database.json"
VALID_CATEGORIES = ["food", "transport", "housing", "entertainment", "shopping", "health", "education", "miscellaneous"]

def set_database_file(filename):
    global DATABASE_FILE
    DATABASE_FILE = filename

def load_database():
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}}

def save_database(data):
    temp_file = f"{DATABASE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, DATABASE_FILE)

def load_user(username):
    db = load_database()
    # Default template tracks the account's base currency
    return db["users"].get(username, {"currency": "USD", "budget_limit": {}, "current_expenses": {}})

def save_user(username, user_data_dict):
    db = load_database()
    db["users"][username] = user_data_dict
    save_database(db)

def delete_user_data(username):
    db = load_database()
    if username in db["users"]:
        del db["users"][username]
        save_database(db)
        return True
    return False

def get_all_usernames():
    db = load_database()
    return list(db["users"].keys())

def cat_v(category_name):
    if not category_name:
        return False
    return category_name.lower().strip() in VALID_CATEGORIES