"""User profile model and profile container."""
import copy

from .currency_service import currency_service
from .data_manager import (
    delete_user_data,
    get_all_usernames,
    load_user,
    normalize_username,
    save_user,
)


class User_class:
    """Represents one user profile and its saved financial data."""

    def __init__(self, name: str):
        self.name = normalize_username(name)

        is_existing = self.name in get_all_usernames()
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")
        self.budget_limit = copy.deepcopy(user_data.get("budget_limit", {}))
        self.current_expenses = copy.deepcopy(user_data.get("current_expenses", {}))
        self.password_hash = user_data.get("password_hash", "")

        if not is_existing:
            self.save()

    def to_dict(self):
        """Convert profile to dictionary for JSON storage."""
        return {
            "currency": self.currency,
            "budget_limit": self.budget_limit,
            "current_expenses": self.current_expenses,
            "password_hash": self.password_hash,
        }

    def save(self):
        """Write profile state to database."""
        save_user(self.name, self.to_dict())

    def set_budget_limit(self, category_clean: str, limit):
        """Set spending limit for category (normalized to lowercase)."""
        category = category_clean.lower().strip()
        limit_float = float(limit)
        if limit_float < 0:
            raise ValueError("Financial limits cannot assume negative constraints.")
        self.budget_limit[category] = limit_float
        self.save()
        return self

    def check_budget(self, category: str):
        """Get budget limit for category (0.0 if none set)."""
        return self.budget_limit.get(category.lower().strip(), 0.0)

    def change_currency(self, amount, from_currency: str, to_currency: str):
        """Convert amount between currencies using exchange service."""
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency: str):
        """Re-denominate all budgets and expenses to new currency."""
        if self.currency == new_currency:
            return

        for category, limit in self.budget_limit.items():
            self.budget_limit[category] = self.change_currency(
                limit, self.currency, new_currency
            )

        for category, expense in self.current_expenses.items():
            self.current_expenses[category] = self.change_currency(
                expense, self.currency, new_currency
            )

        self.currency = new_currency
        self.save()

    def purge(self, category_lower: str):
        """Remove category's budget and expense history. Return removed values."""
        category = category_lower.lower().strip()
        removed = {
            "budget_limit": self.budget_limit.pop(category, None),
            "expense": self.current_expenses.pop(category, None),
        }
        self.save()
        return removed

    def total_expenses_of_user(self):
        """Sum all expenses across categories."""
        return sum(self.current_expenses.values())


class Users:
    """Container providing lookup and management operations across all profiles."""

    def show_users(self):
        """Get list of all stored usernames."""
        return get_all_usernames()

    def delete_user(self, name: str):
        """Permanently delete user record. Return True if user existed."""
        return delete_user_data(normalize_username(name))

    def get_user(self, name: str):
        """Load user profile or None if username doesn't exist."""
        formatted_name = normalize_username(name)
        if formatted_name in self.show_users():
            return User_class(formatted_name)
        return None

    def add_user(self, name: str):
        """Load existing user profile or False if username not registered."""
        formatted_name = normalize_username(name)
        if formatted_name in self.show_users():
            return User_class(formatted_name)
        return False