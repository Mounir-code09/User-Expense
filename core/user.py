"""
User Entities Module
--------------------
Manages user profile data structures, budget limits, and currency conversion.

Each ``User_class`` instance mirrors one record in ``Database.json``. New profiles are
persisted on first creation; existing profiles are loaded without redundant writes.
"""
import copy

from .data_manager import (
    load_user,
    save_user,
    get_all_usernames,
    delete_user_data,
    normalize_username,
)
from .currency_service import currency_service


class User_class:
    """Represents a single user's financial profile and preferences."""

    def __init__(self, name: str):
        self.name = normalize_username(name)

        is_existing = self.name in get_all_usernames()
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")

        # Defensive copies: the loaded dict is the app's own live database record.
        # Assigning the nested dicts by reference would let *any* caller mutate the
        # shared database object in place, producing cross-user bugs. Copying isolates
        # this instance so later edits write back cleanly via ``save()``.
        self.budget_limit = copy.deepcopy(user_data.get("budget_limit", {}))
        self.current_expenses = copy.deepcopy(user_data.get("current_expenses", {}))
        self.password_hash = user_data.get("password_hash", "")

        # Persist only when this is a brand-new profile (e.g. after registration)
        if not is_existing:
            self.save()

    def to_dict(self):
        """Serialize the profile to a dictionary suitable for JSON storage."""
        return {
            "currency": self.currency,
            "budget_limit": self.budget_limit,
            "current_expenses": self.current_expenses,
            "password_hash": self.password_hash,
        }

    def save(self):
        """Write the current profile state to the database."""
        save_user(self.name, self.to_dict())

    def set_budget_limit(self, category_clean: str, limit):
        """
        Set a spending limit for a category.

        Category keys are always normalized to lowercase to stay consistent with
        ``check_budget`` and the expense tracker.
        """
        category = category_clean.lower().strip()
        limit_float = float(limit)
        if limit_float < 0:
            raise ValueError("Financial limits cannot assume negative constraints.")
        self.budget_limit[category] = limit_float
        self.save()
        return self

    def check_budget(self, category: str):
        """Return the budget limit for a category (``0.0`` when none is configured)."""
        return self.budget_limit.get(category.lower().strip(), 0.0)

    def change_currency(self, amount, from_currency: str, to_currency: str):
        """Convert an amount between two currencies via the shared exchange service."""
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency: str):
        """
        Re-denominate all stored budgets and expenses into a new base currency.

        No-op when the target currency matches the current one.
        """
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
        """
        Remove a category's budget limit and expense history.

        Returns a summary of what was removed::

            {"budget_limit": <float or None>, "expense": <float or None>}
        """
        category = category_lower.lower().strip()
        removed = {
            "budget_limit": self.budget_limit.pop(category, None),
            "expense": self.current_expenses.pop(category, None),
        }
        self.save()
        return removed

    def total_expenses_of_user(self):
        """Return the sum of all logged expenses across every category."""
        return sum(self.current_expenses.values())


class Users:
    """Container providing lookup and management operations across all profiles."""

    def show_users(self):
        """Return every username currently stored in the database."""
        return get_all_usernames()

    def delete_user(self, name: str):
        """
        Permanently delete a user record (financial data and password hash).

        Returns ``True`` when the user existed and was removed.
        """
        return delete_user_data(normalize_username(name))

    def get_user(self, name: str):
        """Load an existing user profile, or ``None`` if the username is unknown."""
        formatted_name = normalize_username(name)
        if formatted_name in self.show_users():
            return User_class(formatted_name)
        return None

    def add_user(self, name: str):
        """
        Return a ``User_class`` for an existing profile.

        Returns ``False`` when the username is not registered — use
        ``SecurityManager.register_user`` to create new accounts with credentials.
        """
        formatted_name = normalize_username(name)
        if formatted_name in self.show_users():
            return User_class(formatted_name)
        return False