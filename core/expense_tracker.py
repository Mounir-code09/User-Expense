"""Expense tracking calculations and status reporting."""


class ExpenseTracker:
    """Tracks user spending against configured category budgets."""

    def __init__(self, user):
        self.user = user

    @property
    def expenseReport(self):
        """Dynamic dictionary of current category spending."""
        return self.user.get_category_expenses()

    def add_expense(self, category_lower, amount, note="", date=None):
        """Add an expense transaction to user profile."""
        self.user.add_transaction(category_lower, amount, note, date)
        return self.user.get_category_expenses().get(category_lower.lower().strip(), 0.0)

    def remove_expense(self, category_lower, amount):
        """Subtract expense from category by adding an offsetting adjustment."""
        category = category_lower.lower().strip()
        if not self.user.is_valid_category(category):
            raise ValueError(f"'{category}' is not a recognized category.")

        amount_float = float(amount)
        if amount_float <= 0:
            raise ValueError("Removal amount must be greater than zero.")

        current = self.expenseReport.get(category, 0.0)
        if amount_float > current:
            raise ValueError(
                f"Cannot remove {amount_float:.2f} {self.user.currency}. "
                f"Current spending in '{category}' is only {current:.2f}."
            )

        # Record negative adjustment transaction to preserve audit history
        self.user.add_transaction(
            category, -amount_float, note="Expense removal adjustment", allow_negative=True
        )

    def get_status_report(self):
        """Generate formatted financial summary text."""
        report = [
            f"===== Financial Summary for {self.user.name} =====",
            f"Account Base Currency: {self.user.currency}",
            "-" * 64,
            f"{'Category':<16} | {'Spent':<10} | {'Limit':<12} | {'Status':<16}",
            "-" * 64,
        ]

        for category in self.user.categories:
            spent = self.expenseReport.get(category, 0.0)
            limit = self.user.budget_limits.get(category, "No Limit")
            status = "✅ OK" if limit == "No Limit" or spent <= limit else "❌ OVER"
            limit_str = f"{limit:.2f}" if isinstance(limit, (int, float)) else limit
            report.append(
                f"{category.capitalize():<16} | {spent:<10.2f} | {limit_str:<12} | {status:<16}"
            )

        report.append("-" * 64)
        total_spent = self.total_expenses_of_user()
        total_budget = sum(self.user.budget_limits.values())
        report.append(f"Total Spent: {total_spent:.2f} {self.user.currency} | Total Budget: {total_budget:.2f} {self.user.currency}")
        return "\n".join(report)

    def search_expenses(self, category_lower):
        """Get spending for category or None if no records exist."""
        return self.expenseReport.get(category_lower.lower().strip())

    def total_expenses_of_user(self):
        """Sum all recorded expenses across transactions."""
        return self.user.total_expenses_of_user()