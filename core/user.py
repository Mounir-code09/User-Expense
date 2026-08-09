"""
User Entities Module
Manages user profile data structures and currency conversion delegators.
"""
from .data_manager import load_user, save_user, get_all_usernames, delete_user_data
from .currency_service import currency_service

class User_class:
    def __init__(self, name):
        self.name = name.strip().capitalize()

        # Load existing user profile data from storage
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")
        self.budget_limit = user_data.get("budget_limit", {})
        self.current_expenses = user_data.get("current_expenses", {})

        # Automatically save new users upon initialization
        self.save()

    def to_dict(self):
        return {
            "currency": self.currency,
            "budget_limit": self.budget_limit,
            "current_expenses": self.current_expenses
        }

    def save(self):
        save_user(self.name, self.to_dict())

    def set_budget_limit(self, category_clean, limit):           
        limit_float = float(limit)
        if limit_float < 0:
            raise ValueError("Financial limits cannot assume negative constraints.")
        self.budget_limit[category_clean] = limit_float    
        self.save()
        return self

    def check_budget(self, category):
        return self.budget_limit.get(category.lower().strip(), 0.0)

    def change_currency(self, amount, from_currency, to_currency):
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency):
        if self.currency == new_currency:
            return
            
        # Recalculate and convert all saved budget thresholds to the new currency
        for cat, limit in self.budget_limit.items():
            self.budget_limit[cat] = self.change_currency(limit, self.currency, new_currency)
            
        # Recalculate and convert all logged expenses to the new currency
        for cat, expense in self.current_expenses.items():
            self.current_expenses[cat] = self.change_currency(expense, self.currency, new_currency)
            
        self.currency = new_currency
        self.save()

    def purge(self, category_lower):    
        self.budget_limit.pop(category_lower, None)
        self.current_expenses.pop(category_lower, None)
        self.save()
        return self.budget_limit.get(category_lower, 0.0)

class Users:
    def show_users(self):
        return get_all_usernames()
    
    def delete_user(self, name):       
        delete_user_data(name)
        
    def get_user(self, name):
        formatted_name = name.strip().capitalize()
        if formatted_name in self.show_users():
            return User_class(formatted_name)
        return None