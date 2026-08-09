"""
Expense Tracking Module
-----------------------
Handles transaction updates and formatted status reports in the user's base currency.

This business layer is the *single gate* for mutating spending data. It therefore
re-validates every input (positive amounts, known categories) even though the GUI
already checks it — defence in depth against any caller (GUI, tests, scripts) that
might otherwise bypass the validation in ``ui_actions.py``.
"""
from .user import User_class
from .data_manager import VALID_CATEGORIES, cat_v


class ExpenseTracker:
    """Tracks and reports spending for a single user profile."""

    def __init__(self, user: User_class):
        self.user = user
        self.expenseReport = self.user.current_expenses

    def add_expense(self, category_lower: str, amount):
        category = category_lower.lower().strip()

        if not cat_v(category):
            raise ValueError(f"'{category}' is not a recognized expense category.")

        amount_float = float(amount)
        if amount_float <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        current_spending = self.expenseReport.get(category, 0.0)
        new_spending = current_spending + amount_float
        self.expenseReport[category] = round(new_spending, 2)
        self.user.save()
        return self.expenseReport[category]

    def remove_expense(self, category: str, amount: float):
        """
        Subtract an expense from a category.

        raises ValueError when the amount is non-positive, the category is invalid,
            or the amount exceeds current spending.
        """
        category = category.lower().strip()

        # Validate the category so a typo doesn't silently subtract from a stray key.
        if not cat_v(category):
            raise ValueError(f"'{category}' is not a recognized expense category.")

        amount = float(amount)
        if amount <= 0:
            raise ValueError("Removal amount must be greater than zero.")

        current = self.expenseReport.get(category, 0.0)
        if amount > current:
            raise ValueError(
                f"Cannot remove {amount:.2f} {self.user.currency}. "
                f"Current spending in '{category}' is only {current:.2f}."
            )

        remaining = round(current - amount, 2)

        # A category that reaches exactly zero is removed from the report entirely.
        # This keeps the data clean and prevents a lot of "0.00" rows from piling up.
        if remaining == 0:
            self.expenseReport.pop(category, None)
        else:
            self.expenseReport[category] = remaining

        self.user.save()

    def get_status_report(self):
        """Build a plain-text financial summary table for all standard categories."""
        report = [
            f"===== Financial Summary for {self.user.name} =====",
            f"Account Base Currency: {self.user.currency}",
            "-" * 62,
            f"{'Category':<15} | {'Spent':<10} | {'Limit':<12} | {'Status':<15}",
            "-" * 62,
        ]

        for category in VALID_CATEGORIES:
            spent = self.expenseReport.get(category, 0.0)
            limit = self.user.budget_limit.get(category, "No Limit")
            status = "✅ OK" if limit == "No Limit" or spent <= limit else "❌ OVER"
            limit_str = f"{limit:.2f}" if isinstance(limit, (int, float)) else limit
            report.append(
                f"{category.capitalize():<15} | {spent:<10.2f} | {limit_str:<12} | {status:<15}"
            )

        return "\n".join(report)

    def search_expenses(self, category_lower: str):
        """Return spending for a category, or ``None`` when no records exist."""
        return self.expenseReport.get(category_lower.lower().strip())