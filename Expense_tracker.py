"""
Expense Tracking Calculations Module
Handles transaction updates and status matrix text generation based on native account currency.
"""
from User import User_class
from data_manager import VALID_CATEGORIES

class ExpenseTracker:
    def __init__(self, user: User_class):
        self.user = user
        self.expenseReport = self.user.current_expenses

    def add_expense(self, category_lower, amount):      
        current_spending = self.expenseReport.get(category_lower, 0.0)
        new_spending = current_spending + float(amount)
        self.expenseReport[category_lower] = round(new_spending, 2)
        self.user.save()
        return self.expenseReport[category_lower]
    
    def get_status_report(self):
        report = []
        report.append(f"===== Financial Summary for {self.user.name} =====")
        report.append(f"Account Base Currency: {self.user.currency}")
        report.append("-" * 62)
        report.append(f"{'Category':<15} | {'Spent':<10} | {'Limit':<12} | {'Status':<15}")
        report.append("-" * 62)
        
        for cat in VALID_CATEGORIES:
            spent = self.expenseReport.get(cat, 0.0)
            limit = self.user.budget_limit.get(cat, "No Limit")
            status = "✅ OK" if limit == "No Limit" or spent <= limit else "❌ OVER"
            
            limit_str = f"{limit:.2f}" if isinstance(limit, (int, float)) else limit
            report.append(f"{cat.capitalize():<15} | {spent:<9.2f} | {limit_str:<12} | {status:<15}")
            
        return "\n".join(report)

    def search_expenses(self, category_lower):
        return self.expenseReport.get(category_lower)

    def total_expenses_of_user(self):
        return sum(self.expenseReport.values())