"""Expense tracking calculations and status reporting."""
from .exceptions import InvalidAmountError, InvalidCategoryError
from .theme import format_amount


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
            raise InvalidCategoryError(f"'{category}' is not a recognized category.")

        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError("Removal amount must be a valid number.")

        if amount_float <= 0:
            raise InvalidAmountError("Removal amount must be greater than zero.")

        current = self.expenseReport.get(category, 0.0)
        if amount_float > current:
            raise InvalidAmountError(
                f"Cannot remove {format_amount(amount_float, self.user.currency)}. "
                f"Current spending in '{category}' is only {format_amount(current, self.user.currency)}."
            )

        self.user.add_transaction(
            category, -amount_float, note="Expense removal adjustment", allow_negative=True
        )

    def get_status_report(self):
        """Generate formatted financial summary text with comma-separated amounts."""
        report = [
            f"===== Financial Summary for {self.user.name} =====",
            f"Account Base Currency: {self.user.currency}",
            "-" * 66,
            f"{'Category':<16} | {'Spent':<12} | {'Limit':<14} | {'Status':<16}",
            "-" * 66,
        ]

        for category in self.user.categories:
            spent = self.expenseReport.get(category, 0.0)
            limit = self.user.budget_limits.get(category, "No Limit")
            status = "✅ OK" if limit == "No Limit" or spent <= limit else "❌ OVER"
            limit_str = f"{limit:,.2f}" if isinstance(limit, (int, float)) else limit
            report.append(
                f"{category.capitalize():<16} | {spent:<12,.2f} | {limit_str:<14} | {status:<16}"
            )

        report.append("-" * 66)
        total_spent = self.total_expenses_of_user()
        total_income = self.user.total_income_of_user()
        net_savings = self.user.get_net_savings()
        savings_rate = self.user.get_savings_rate()
        total_budget = sum(self.user.budget_limits.values())

        report.append(
            f"Total Spent:    {format_amount(total_spent, self.user.currency)}\n"
            f"Total Income:   {format_amount(total_income, self.user.currency)}\n"
            f"Net Savings:    {format_amount(net_savings, self.user.currency)} ({savings_rate}%)\n"
            f"Total Budget:   {format_amount(total_budget, self.user.currency)}"
        )
        return "\n".join(report)

    def search_expenses(self, category_lower):
        """Get spending for category or None if no records exist."""
        return self.expenseReport.get(category_lower.lower().strip())

    def total_expenses_of_user(self):
        """Sum all recorded expenses across transactions."""
        return self.user.total_expenses_of_user()