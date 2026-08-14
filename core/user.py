"""User profile model and user collection manager."""
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
    """Represents a single user profile with budgets and expenses."""

    def __init__(self, name: str):
        self.name = normalize_username(name)
        if not self.name:
            raise ValueError("Username cannot be blank.")

        is_existing = self.name in get_all_usernames()
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")
        self.budget_limit = copy.deepcopy(user_data.get("budget_limit", {}))
        self.current_expenses = copy.deepcopy(user_data.get("current_expenses", {}))
        self.password_hash = user_data.get("password_hash", "")
        self.failed_attempts = user_data.get("failed_attempts", 0)
        self.lockout_until = user_data.get("lockout_until", 0)

        if not is_existing:
            self.save()

    def to_dict(self):
        """Convert profile to dictionary for JSON persistence."""
        return {
            "currency": self.currency,
            "budget_limit": self.budget_limit,
            "current_expenses": self.current_expenses,
            "password_hash": self.password_hash,
            "failed_attempts": self.failed_attempts,
            "lockout_until": self.lockout_until,
        }

    def save(self):
        """Write profile state to database."""
        save_user(self.name, self.to_dict())

    def set_budget_limit(self, category_clean, limit):
        """Set spending limit for category."""
        category = category_clean.lower().strip()
        limit_float = float(limit)
        if limit_float < 0:
            raise ValueError("Budget limit cannot be negative.")
        self.budget_limit[category] = limit_float
        self.save()
        return self

    def check_budget(self, category):
        """Get budget limit for category (0.0 if not set)."""
        return self.budget_limit.get(category.lower().strip(), 0.0)

    def change_currency(self, amount, from_currency, to_currency):
        """Convert amount between currencies."""
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency):
        """Convert all budgets and expenses to a new currency."""
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

    def reset_category(self, category_lower):
        """Reset budget and expense history for a category."""
        category = category_lower.lower().strip()
        removed = {
            "budget_limit": self.budget_limit.pop(category, None),
            "expense": self.current_expenses.pop(category, None),
        }
        self.save()
        return removed

    # Alias for backward compatibility
    purge = reset_category

    def total_expenses_of_user(self):
        """Sum all expenses across categories."""
        return sum(self.current_expenses.values())


class Users:
    """Provides lookup and management operations across all user profiles."""

    def show_users(self):
        """Return list of all registered usernames."""
        return get_all_usernames()

    def delete_user(self, name):
        """Delete user profile. Return True if user existed."""
        return delete_user_data(name)

    def get_user(self, name):
        """Load user profile or None if username not found."""
        formatted_name = normalize_username(name)
        if formatted_name and formatted_name in self.show_users():
            return User_class(formatted_name)
        return None

    def add_user(self, name):
        """Create and return a new user profile, or False if username exists or invalid."""
        formatted_name = normalize_username(name)
        if not formatted_name or formatted_name in self.show_users():
            return False
        return User_class(formatted_name)