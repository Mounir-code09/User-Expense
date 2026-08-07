"""
UI Actions & Dialog Handlers
Encapsulates CTkInputDialog prompts and CTkMessagebox notifications.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from data_manager import cat_v

class UIActions:
    def __init__(self, user, user_tracker, users_container):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container

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

    def set_budget(self):
        cat = self._get_valid_category("Set Budget")
        if not cat: return
        dialog = ctk.CTkInputDialog(text=f"Budget limit ({self.user.currency}):", title="Set Budget")
        raw_limit = dialog.get_input()
        if raw_limit:
            try:
                self.user.set_budget_limit(cat, raw_limit)
                CTkMessagebox(title="Success", message=f"Budget set for {cat}.", icon="check")
            except ValueError as e:
                CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def add_expense(self):
        cat = self._get_valid_category("Add Expense")
        if not cat: return
        dialog = ctk.CTkInputDialog(text=f"Amount ({self.user.currency}):", title="Add Expense")
        raw_amount = dialog.get_input()
        if raw_amount:
            try:
                amount = float(raw_amount)
                limit = self.user.budget_limit.get(cat)
                current = self.tracker.expenseReport.get(cat, 0.0)
                
                if limit and (current + amount) > limit:
                    msg = CTkMessagebox(title="Warning", message="Exceeds budget limit! Save anyway?", icon="warning", option_1="No", option_2="Yes")
                    if msg.get() != "Yes": return

                self.tracker.add_expense(cat, amount)
                CTkMessagebox(title="Success", message=f"Added {amount:.2f} {self.user.currency} to {cat}.", icon="check")
            except ValueError:
                CTkMessagebox(title="Error", message="Please enter a valid number.", icon="cancel")

    def show_status(self, parent_window):
        win = ctk.CTkToplevel(parent_window)
        win.title("Financial Dashboard")
        win.geometry("500x380")
        box = ctk.CTkTextbox(win, font=("Consolas", 12))
        box.pack(fill="both", expand=True, padx=10, pady=10)
        box.insert("1.0", self.tracker.get_status_report())
        box.configure(state="disabled")

    def total_expenses(self):
        total = self.tracker.total_expenses_of_user()
        CTkMessagebox(title="Total", message=f"Total spent: {total:.2f} {self.user.currency}", icon="info")