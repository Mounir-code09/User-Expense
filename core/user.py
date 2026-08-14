"""User profile model, transaction ledger, and profile container."""
import copy
import csv
from datetime import datetime
import uuid

from .currency_service import currency_service
from .data_manager import (
    DEFAULT_CATEGORIES,
    delete_user_data,
    get_all_usernames,
    load_user,
    normalize_username,
    save_user,
)


class User:
    """Represents a single user financial profile with budgets and transactions."""

    def __init__(self, name):
        self.name = normalize_username(name)
        if not self.name:
            raise ValueError("Username cannot be blank.")

        is_existing = self.name in get_all_usernames()
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")
        self.categories = copy.deepcopy(user_data.get("categories", DEFAULT_CATEGORIES.copy()))
        self.budget_limits = copy.deepcopy(user_data.get("budget_limits", {}))
        self.transactions = copy.deepcopy(user_data.get("transactions", []))
        self.password_hash = user_data.get("password_hash", "")
        self.failed_attempts = user_data.get("failed_attempts", 0)
        self.lockout_until = user_data.get("lockout_until", 0)

        if not is_existing:
            self.save()

    @property
    def budget_limit(self):
        """Compatibility property for budget limits."""
        return self.budget_limits

    @budget_limit.setter
    def budget_limit(self, value):
        self.budget_limits = value

    @property
    def current_expenses(self):
        """Dynamic summary dictionary of spending per category."""
        return self.get_category_expenses()

    def to_dict(self):
        """Convert profile to dictionary for JSON persistence."""
        return {
            "currency": self.currency,
            "categories": self.categories,
            "budget_limits": self.budget_limits,
            "transactions": self.transactions,
            "password_hash": self.password_hash,
            "failed_attempts": self.failed_attempts,
            "lockout_until": self.lockout_until,
        }

    def save(self):
        """Write profile state to database."""
        save_user(self.name, self.to_dict())

    def is_valid_category(self, category):
        """Check if category is in user's category list."""
        if not category:
            return False
        return category.lower().strip() in [c.lower() for c in self.categories]

    def add_custom_category(self, category_name):
        """Add a custom category to the user's profile."""
        clean_name = category_name.lower().strip()
        if not clean_name:
            raise ValueError("Category name cannot be blank.")
        if clean_name in [c.lower() for c in self.categories]:
            raise ValueError(f"Category '{clean_name}' already exists.")
        self.categories.append(clean_name)
        self.save()
        return clean_name

    def set_budget_limit(self, category_clean, limit):
        """Set spending limit for category."""
        category = category_clean.lower().strip()
        if not self.is_valid_category(category):
            raise ValueError(f"'{category}' is not a recognized category.")
        limit_float = float(limit)
        if limit_float < 0:
            raise ValueError("Budget limit cannot be negative.")
        self.budget_limits[category] = round(limit_float, 2)
        self.save()
        return self

    def check_budget(self, category):
        """Get budget limit for category (0.0 if not set)."""
        return self.budget_limits.get(category.lower().strip(), 0.0)

    def add_transaction(self, category_clean, amount, note="", date=None, allow_negative=False):
        """Add an expense transaction with date and note."""
        category = category_clean.lower().strip()
        if not self.is_valid_category(category):
            raise ValueError(f"'{category}' is not a recognized category.")

        amount_float = float(amount)
        if not allow_negative and amount_float <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        elif allow_negative and amount_float == 0:
            raise ValueError("Adjustment amount cannot be zero.")

        if not date:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                date_str = date
            except ValueError:
                date_str = datetime.now().strftime("%Y-%m-%d")

        tx = {
            "id": f"tx_{uuid.uuid4().hex[:8]}",
            "date": date_str,
            "category": category,
            "amount": round(amount_float, 2),
            "note": note.strip() if note else "",
        }
        self.transactions.append(tx)
        self.save()
        return tx

    def delete_transaction(self, transaction_id):
        """Delete a single transaction by ID."""
        initial_count = len(self.transactions)
        self.transactions = [tx for tx in self.transactions if tx.get("id") != transaction_id]
        if len(self.transactions) < initial_count:
            self.save()
            return True
        return False

    def get_transactions(self, category=None, month=None):
        """Get list of transactions filtered by category or month (YYYY-MM)."""
        txs = self.transactions
        if category:
            cat_clean = category.lower().strip()
            txs = [tx for tx in txs if tx.get("category") == cat_clean]
        if month:
            txs = [tx for tx in txs if tx.get("date", "").startswith(month)]
        return sorted(txs, key=lambda tx: tx.get("date", ""), reverse=True)

    def get_category_expenses(self):
        """Calculate total spending per category from transactions."""
        totals = {cat.lower(): 0.0 for cat in self.categories}
        for tx in self.transactions:
            cat = tx.get("category", "").lower()
            if cat in totals:
                totals[cat] += tx.get("amount", 0.0)
            else:
                totals[cat] = tx.get("amount", 0.0)
        return {cat: round(amt, 2) for cat, amt in totals.items()}

    def total_expenses_of_user(self):
        """Sum all expenses across all transactions."""
        return round(sum(tx.get("amount", 0.0) for tx in self.transactions), 2)

    def get_remaining_budget(self):
        """Calculate total budget limit minus total spending."""
        total_budget = sum(self.budget_limits.values())
        return round(total_budget - self.total_expenses_of_user(), 2)

    def get_top_category(self):
        """Return (category, amount) with the highest spending."""
        expenses = self.get_category_expenses()
        active = {c: amt for c, amt in expenses.items() if amt > 0}
        if not active:
            return "None", 0.0
        top_cat = max(active, key=active.get)
        return top_cat.capitalize(), active[top_cat]

    def change_currency(self, amount, from_currency, to_currency):
        """Convert amount between currencies."""
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency):
        """Convert all budgets and transactions to a new currency."""
        if self.currency == new_currency:
            return

        for category, limit in self.budget_limits.items():
            self.budget_limits[category] = self.change_currency(
                limit, self.currency, new_currency
            )

        for tx in self.transactions:
            tx["amount"] = self.change_currency(
                tx["amount"], self.currency, new_currency
            )

        self.currency = new_currency
        self.save()

    def reset_category(self, category_lower):
        """Reset budget and expense history for a category."""
        category = category_lower.lower().strip()
        removed_budget = self.budget_limits.pop(category, None)
        removed_expenses = sum(
            tx["amount"] for tx in self.transactions if tx.get("category") == category
        )
        self.transactions = [tx for tx in self.transactions if tx.get("category") != category]
        self.save()
        return {
            "budget_limit": removed_budget,
            "expense": round(removed_expenses, 2),
        }

    purge = reset_category

    def export_to_csv(self, filepath):
        """Export all user transactions to a CSV file."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Transaction ID", "Date", "Category", "Amount", "Currency", "Note"])
            for tx in sorted(self.transactions, key=lambda t: t.get("date", "")):
                writer.writerow([
                    tx.get("id", ""),
                    tx.get("date", ""),
                    tx.get("category", "").capitalize(),
                    f"{tx.get('amount', 0.0):.2f}",
                    self.currency,
                    tx.get("note", ""),
                ])
        return filepath


User_class = User


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
            return User(formatted_name)
        return None

    def add_user(self, name):
        """Create and return a new user profile, or False if username exists or invalid."""
        formatted_name = normalize_username(name)
        if not formatted_name or formatted_name in self.show_users():
            return False
        return User(formatted_name)