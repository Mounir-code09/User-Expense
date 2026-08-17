import os
from tkinter import filedialog
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .exceptions import (
    CategoryAlreadyExistsError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
)
from .modals import (
    AddExpenseModal,
    AddIncomeModal,
    ChangePasswordModal,
    CTkDropdownDialog,
    CTkInputModal,
    ImportStatementModal,
    IncomeHistoryModal,
    RecurringTemplatesModal,
    SavingsGoalsModal,
    SwitchAccountModal,
    TransactionHistoryModal,
)
from .theme import CARD_BG, PRIMARY, PRIMARY_HOVER, format_amount


class UIActions:

    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root

    def _get_active_month(self):
        if hasattr(self.root, "get_selected_month"):
            return self.root.get_selected_month()
        return None

    def _refresh_dashboard(self):
        try:
            if hasattr(self.root, "refresh_summary_cards") and self.root.winfo_exists():
                self.root.refresh_summary_cards()
        except Exception:
            pass

    def category_dropdown_menu(self, prompt_title):
        formatted_options = [cat.capitalize() for cat in self.user.categories]
        dialog = CTkDropdownDialog(
            title="Category Selection",
            text=f"Select a category to {prompt_title}:",
            values=formatted_options,
            master=self.root,
        )
        selected = dialog.get_input()
        if not selected:
            return None
        normalized = selected.lower().strip()
        if not self.user.is_valid_category(normalized):
            CTkMessagebox(title="Invalid Category", message="The selected category is not recognized.", icon="cancel", master=self.root)
            return None
        return normalized

    def set_budget(self, default_category=None):
        if default_category and self.user.is_valid_category(default_category):
            category = default_category.lower().strip()
        else:
            category = self.category_dropdown_menu("set a budget for")
            if not category:
                return

        dialog = CTkInputModal(
            title="Set Budget",
            text=f"Budget limit for {category.capitalize()} ({self.user.currency}):",
            master=self.root,
        )
        raw_limit = dialog.get_input()
        if not raw_limit:
            return
        try:
            limit_val = float(raw_limit.replace(",", "").replace(" ", ""))
            self.user.set_budget_limit(category, limit_val)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Budget Saved",
                message=f"Limit for {category.capitalize()} set to {format_amount(limit_val, self.user.currency)}.",
                icon="check", master=self.root,
            )
        except (InvalidAmountError, InvalidCategoryError, ValueError) as exc:
            CTkMessagebox(title="Invalid Input", message=str(exc), icon="cancel", master=self.root)

    def add_expense(self):
        modal = AddExpenseModal(self.user.categories, currency=self.user.currency, master=self.root)
        data = modal.get_expense_data()
        if not data:
            return

        category = data["category"]
        amount = data["amount"]
        note = data["note"]
        date_str = data["date"]

        budget_limit = self.user.budget_limits.get(category, 0.0)
        current_spending = self.user.get_category_expenses().get(category, 0.0)

        if budget_limit <= 0:
            prompt_box = CTkMessagebox(
                title="No Budget Set",
                message=(
                    f"No budget limit is currently set for {category.capitalize()}.\n\n"
                    f"Would you like to configure a budget limit first, or record the expense directly?"
                ),
                icon="question",
                option_1="Set Budget First",
                option_2="Record Directly",
                option_3="Cancel",
                master=self.root,
            )
            user_choice = prompt_box.get()
            if user_choice == "Cancel":
                return
            elif user_choice == "Set Budget First":
                dialog = CTkInputModal(
                    title="Set Budget",
                    text=f"Enter budget limit for {category.capitalize()} ({self.user.currency}):",
                    master=self.root,
                )
                raw_limit = dialog.get_input()
                if raw_limit:
                    try:
                        limit_val = float(raw_limit.replace(",", "").replace(" ", ""))
                        self.user.set_budget_limit(category, limit_val)
                        budget_limit = limit_val
                    except (InvalidAmountError, ValueError):
                        pass

        if budget_limit > 0 and (current_spending + amount) > budget_limit:
            msg = CTkMessagebox(
                title="Over Budget Warning",
                message=(
                    f"Adding {format_amount(amount, self.user.currency)} will exceed your "
                    f"budget for {category.capitalize()} ({format_amount(budget_limit, self.user.currency)}).\n\n"
                    f"Record transaction anyway?"
                ),
                icon="warning", option_1="No", option_2="Yes", master=self.root,
            )
            if msg.get() != "Yes":
                return

        try:
            self.user.add_transaction(category, amount, note=note, date_val=date_str)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Expense Recorded",
                message=f"Logged {format_amount(amount, self.user.currency)} under {category.capitalize()}.",
                icon="check", master=self.root,
            )
            self._check_budget_alerts()
        except (InvalidAmountError, InvalidCategoryError, InvalidDateError) as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def add_income(self):
        modal = AddIncomeModal(currency=self.user.currency, master=self.root)
        data = modal.get_income_data()
        if not data:
            return

        try:
            self.user.add_income(data["source"], data["amount"], note=data["note"], date_val=data["date"])
            self._refresh_dashboard()
            CTkMessagebox(
                title="Income Recorded",
                message=f"Logged {format_amount(data['amount'], self.user.currency)} from {data['source']}.",
                icon="check", master=self.root,
            )
        except (InvalidAmountError, InvalidDateError) as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def show_incomes(self):
        modal = IncomeHistoryModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()

    def remove_expense(self):
        category = self.category_dropdown_menu("remove an expense from")
        if not category:
            return
        current_spent = self.user.get_category_expenses().get(category, 0.0)
        if current_spent <= 0:
            CTkMessagebox(title="No Expenses", message=f"No spending recorded in '{category.capitalize()}'.", icon="info", master=self.root)
            return

        dialog = CTkInputModal(
            title="Remove Expense",
            text=f"Current spending in {category.capitalize()}: {format_amount(current_spent, self.user.currency)}\nAmount to subtract:",
            master=self.root,
        )
        raw_amount = dialog.get_input()
        if not raw_amount:
            return
        try:
            amount = float(raw_amount.replace(",", "").replace(" ", ""))
            self.tracker.remove_expense(category, amount)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Expense Removed",
                message=f"Subtracted {format_amount(amount, self.user.currency)} from {category.capitalize()}.",
                icon="check", master=self.root,
            )
        except (InvalidAmountError, InvalidCategoryError, ValueError) as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def show_transactions(self):
        modal = TransactionHistoryModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()

    def add_custom_category(self):
        dialog = CTkInputModal(title="New Category", text="Enter custom category name:", master=self.root)
        cat_name = dialog.get_input()
        if not cat_name:
            return
        try:
            created = self.user.add_custom_category(cat_name)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Category Added",
                message=f"Custom category '{created.capitalize()}' added successfully!",
                icon="check", master=self.root,
            )
        except (CategoryAlreadyExistsError, InvalidCategoryError) as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def manage_recurring_templates(self):
        modal = RecurringTemplatesModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()

    def manage_savings_goals(self):
        modal = SavingsGoalsModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()

    def change_password(self):
        modal = ChangePasswordModal(self.user.name, master=self.root)
        modal.is_successful()

    def export_to_csv(self):
        month = self._get_active_month()
        suffix = f"_{month}" if month else "_all_time"
        default_file = f"finance_export_{self.user.name.lower()}{suffix}.csv"
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Financial Records to CSV",
            initialfile=default_file,
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        try:
            self.user.export_to_csv(filepath, month=month)
            CTkMessagebox(
                title="Export Complete",
                message=f"Records successfully exported to:\n{os.path.basename(filepath)}",
                icon="check", master=self.root,
            )
        except OSError as exc:
            CTkMessagebox(title="Export Failed", message=str(exc), icon="cancel", master=self.root)

    def reset_category(self):
        category = self.category_dropdown_menu("reset")
        if not category:
            return
        removed = self.user.reset_category(category)
        self._refresh_dashboard()
        CTkMessagebox(
            title="Category Reset",
            message=(
                f"Reset all data for {category.capitalize()}.\n"
                f"  Budget removed: {format_amount(removed['budget_limit'] or 0.0, self.user.currency)}\n"
                f"  Expenses removed: {format_amount(removed['expense'], self.user.currency)}"
            ),
            icon="check", master=self.root,
        )

    def change_account_currency(self, new_currency, currency_selector):
        if self.user.currency == new_currency:
            return
        msg = CTkMessagebox(
            title="Convert Currency",
            message=f"Convert all budgets, transactions, and incomes from {self.user.currency} to {new_currency}?",
            icon="question", option_1="Yes", option_2="No", master=self.root,
        )
        if msg.get() == "Yes":
            self.user.convert_account_currency(new_currency)
            currency_selector.set(new_currency)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Currency Updated",
                message=f"All amounts are now recorded in {new_currency}.",
                icon="check", master=self.root,
            )
        else:
            currency_selector.set(self.user.currency)

    def show_status(self):
        month = self._get_active_month()
        status_win = ctk.CTkToplevel(self.root)
        status_win.title("Financial Status Dashboard")
        status_win.geometry("640x480")
        status_win.configure(fg_color=CARD_BG)
        text_widget = ctk.CTkTextbox(status_win, font=("Consolas", 12), activate_scrollbars=True)
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", self.tracker.get_status_report(month=month))
        text_widget.configure(state="disabled")
        ctk.CTkButton(
            status_win, text="Close", command=status_win.destroy,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
        ).pack(fill="x", padx=15, pady=(0, 15))
        status_win.transient(self.root)
        status_win.focus_set()

    def show_chart(self):
        from .chart_viewer import ChartViewer
        month = self._get_active_month()
        ChartViewer.show_expense_pie_chart(parent_root=self.root, user=self.user, month=month)

    def switch_user_profile(self):
        modal = SwitchAccountModal(self.users, current_user=self.user.name, master=self.root)
        new_username = modal.get_username()
        if new_username:
            self.root.switch_user_workflow(new_username)

    def exit_app(self):
        self.root.after(0, self.root.on_close)

    def _check_budget_alerts(self):
        month = self._get_active_month()
        alerts = self.user.get_budget_alerts(month=month)
        if not alerts:
            return
        danger = [a for a in alerts if a["level"] == "danger"]
        warning = [a for a in alerts if a["level"] == "warning"]
        if danger:
            lines = "\n".join(f"  • {a['message']}" for a in danger)
            CTkMessagebox(
                title="Budget Exceeded!",
                message=f"You have gone over budget:\n{lines}",
                icon="cancel", master=self.root,
            )
        elif warning:
            lines = "\n".join(f"  • {a['message']}" for a in warning)
            CTkMessagebox(
                title="Budget Warning",
                message=f"You are approaching your budget limit:\n{lines}",
                icon="warning", master=self.root,
            )

    def import_bank_statement(self):
        modal = ImportStatementModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()
