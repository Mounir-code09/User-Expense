"""Expense tracking calculations and status reporting."""
from .data_manager import VALID_CATEGORIES, cat_v


class ExpenseTracker:
    """Tracks user spending against configured category budgets."""

    def __init__(self, user):
        self.user = user
        self.expenseReport = self.user.current_expenses

    def add_expense(self, category_lower: str, amount):
        """Add expense to category and persist to user profile."""
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

    def remove_expense(self, category_lower: str, amount):
        """Subtract expense from category."""
        category = category_lower.lower().strip()

        if not cat_v(category):
            raise ValueError(f"'{category}' is not a recognized expense category.")

        amount_float = float(amount)
        if amount_float <= 0:
            raise ValueError("Removal amount must be greater than zero.")

        current = self.expenseReport.get(category, 0.0)
        if amount_float > current:
            raise ValueError(
                f"Cannot remove {amount_float:.2f} {self.user.currency}. "
                f"Current spending in '{category}' is only {current:.2f}."
            )

        remaining = round(current - amount_float, 2)
        if remaining == 0:
            self.expenseReport.pop(category, None)
        else:
            self.expenseReport[category] = remaining

        self.user.save()

    def get_status_report(self):
        """Generate formatted financial summary text."""
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
        """Get spending for category or None if no records exist."""
        return self.expenseReport.get(category_lower.lower().strip())

    def total_expenses_of_user(self):
        """Sum all recorded expenses across categories."""
        return sum(self.expenseReport.values())