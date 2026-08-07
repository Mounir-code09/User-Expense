"""
UI Actions & Dialog Handlers
Encapsulates CTkInputDialog prompts, logic, and CTkMessagebox notifications.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from data_manager import cat_v

class UIActions:
    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root

    def _get_valid_category(self, prompt_title):
        dialog = ctk.CTkInputDialog(text="Enter category name:", title=prompt_title)
        category = dialog.get_input()
        if not category:
            return None
        clean_cat = category.lower().strip()
        if not cat_v(clean_cat):
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel")
            return None
        return clean_cat

    def change_account_currency(self, new_currency, currency_selector):
        if self.user.currency == new_currency:
            return
            
        msg = CTkMessagebox(
            title="Convert Portfolio", 
            message=f"Convert all stored budgets and expenses from {self.user.currency} to {new_currency}?",
            icon="question", option_1="Yes", option_2="No"
        )
        if msg.get() == "Yes":
            self.user.convert_account_currency(new_currency)
            currency_selector.set(new_currency)
            CTkMessagebox(title="Converted", message=f"Portfolio is now natively recorded in {new_currency}.", icon="check")
        else:
            currency_selector.set(self.user.currency)

    def set_budget(self):
        cat = self._get_valid_category("Set Budget")
        if not cat: return
        dialog = ctk.CTkInputDialog(text=f"Budget limit amount ({self.user.currency}):", title="Set Budget")
        raw_limit = dialog.get_input()
        if not raw_limit: return
        try:
            self.user.set_budget_limit(cat, raw_limit)
            CTkMessagebox(title="Budget Set", message=f"Budget set to {float(raw_limit):.2f} {self.user.currency}", icon="check")
        except ValueError as e:
            CTkMessagebox(title="Invalid Input", message=str(e), icon="cancel")

    def check_budget(self):
        cat = self._get_valid_category("Check Budget")
        if not cat: return
        budget = self.user.check_budget(cat)
        CTkMessagebox(title="Budget Check", message=f"Current limit for {cat}: {budget:.2f} {self.user.currency}", icon="info")

    def purge(self):
        cat = self._get_valid_category("Purge Budget")
        if not cat: return
        self.user.purge(cat)
        CTkMessagebox(title="Purge Budget", message=f"Purged budget and history metrics for {cat}.", icon="check")

    def add_expense(self):
        cat = self._get_valid_category("Add Expense")
        if not cat: return
        dialog = ctk.CTkInputDialog(text=f"Amount for {cat} ({self.user.currency}):", title="Add Expense")
        raw_amount = dialog.get_input()
        if not raw_amount: return

        try:
            amount = float(raw_amount)
            if amount <= 0.0:
                CTkMessagebox(title="Invalid Input", message="Please enter a positive amount.", icon="cancel")
                return
            
            budget_limit = self.user.budget_limit.get(cat)
            current_spending = self.tracker.expenseReport.get(cat, 0.0)
            
            if budget_limit and (current_spending + amount) > budget_limit:            
                msg = CTkMessagebox(
                    title="Over Budget Warning", 
                    message=f"Adding {amount:.2f} {self.user.currency} will exceed limits for {cat}.\nSave transaction regardless?",
                    icon="warning", option_1="No", option_2="Yes"
                )
                if msg.get() != "Yes":
                    return

            self.tracker.add_expense(cat, amount)
            CTkMessagebox(title="Expense Added", message=f"Recorded {amount:.2f} {self.user.currency} under {cat}.", icon="check")
        except ValueError:
            CTkMessagebox(title="Invalid Input", message="Please enter a valid numeric value.", icon="cancel")

    def show_status(self):
        status_win = ctk.CTkToplevel(self.root)
        status_win.title("Financial Status Dashboard")
        status_win.geometry("540x400")
        
        text_widget = ctk.CTkTextbox(status_win, font=("Consolas", 12), activate_scrollbars=True)
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", self.tracker.get_status_report())
        text_widget.configure(state="disabled")
        
        close_btn = ctk.CTkButton(status_win, text="Close View", command=status_win.destroy)
        close_btn.pack(fill="x", padx=15, pady=(0, 15))
        status_win.transient(self.root)   
        status_win.focus_set()

    def search_expenses(self):
        cat = self._get_valid_category("Search Expense")
        if not cat: return
        result = self.tracker.search_expenses(cat) 
        if result is not None:
            CTkMessagebox(title="Search Result", message=f"{self.user.name} spent {result:.2f} {self.user.currency} on {cat}", icon="info") 
        else:
            CTkMessagebox(title="Search Result", message="No transaction records found for this category.", icon="info")

    def total_expenses(self):
        total = self.tracker.total_expenses_of_user()
        CTkMessagebox(title="Total Aggregate Expenses", message=f"Total user footprint portfolio costs: {total:.2f} {self.user.currency}", icon="info")

    def show_users(self):
        users_list = self.users.show_users() 
        if users_list:
            CTkMessagebox(title="Users List", message="Current Users:\n\n" + "\n".join(users_list), icon="info") 
        else:
            CTkMessagebox(title="Users List", message="No active logs mapped.", icon="info")

    def delete_user(self):
        d = ctk.CTkInputDialog(text="Enter username to delete:", title="Delete User")
        raw_del_name = d.get_input()
        if not raw_del_name: return
        
        del_name = raw_del_name.strip().capitalize()
        if del_name == self.user.name:
            CTkMessagebox(title="Error", message="You cannot delete the currently active configuration profile.", icon="cancel")
            return

        if del_name in self.users.show_users():
            msg = CTkMessagebox(title="Confirmation", message=f"Permanently wipe {del_name}'s database file records?", icon="question", option_1="Yes", option_2="No")
            if msg.get() == "Yes":
                self.users.delete_user(del_name) 
                CTkMessagebox(title="Deleted User", message=f"Successfully scrubbed {del_name}.", icon="check")
        else:
            CTkMessagebox(title="Error", message="Profile record does not exist.", icon="cancel")

    def get_user(self):
        d = ctk.CTkInputDialog(text="Enter username to find:", title="Find User")
        raw_search_name = d.get_input()
        if not raw_search_name: return
        
        search_name = raw_search_name.capitalize()
        target_user = self.users.get_user(search_name)
        if target_user:
            info_message = f"User Profile: {target_user.name}\nBase Currency: {target_user.currency}\n===================\nBudget Limits:\n"
            if target_user.budget_limit: 
                for category, limit in target_user.budget_limit.items():
                    info_message += f"  - {category.capitalize()}: {limit:.2f} {target_user.currency}\n"
            else:
                info_message += "  No thresholds configured.\n"
            total_spent = sum(target_user.current_expenses.values())
            info_message += f"\nTotal Spent footprint: {total_spent:.2f} {target_user.currency}"                                 
            CTkMessagebox(title=f"Profile Found: {search_name}", message=info_message, icon="info")
        else:
            CTkMessagebox(title="Error", message=f"User '{search_name}' does not match configuration stores.", icon="cancel")

    def exit_app(self):
        CTkMessagebox(title="Exit", message="State saved completely. Goodbye!", icon="info") 
        self.root.after(800, lambda: self.root.quit())