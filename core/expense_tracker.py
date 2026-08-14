"""Expense logic and summary reporting."""
from .data_manager import VALID_CATEGORIES, cat_v
from .user import User_class


class ExpenseTracker:
    """Tracks user spending and budget-aware summaries."""

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
        """Subtract expense from category. Raise ValueError for invalid inputs."""
        category = category.lower().strip()

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

        if remaining == 0:
            self.expenseReport.pop(category, None)
        else:
            self.expenseReport[category] = remaining

        self.user.save()

    def get_status_report(self):
        """Generate plain-text financial summary showing spent vs budget per category."""
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
        """Get total spending for category or None if no records exist."""
        return self.expenseReport.get(category_lower.lower().strip())

    def total_expenses_of_user(self):
            """Sum all recorded expenses."""
            return sum(self.expenseReport.values())