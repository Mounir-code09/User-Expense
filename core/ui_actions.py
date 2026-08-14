"""Dashboard actions, dialog management, and ledger operations."""
import os
from tkinter import filedialog
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .modals import (
    AddExpenseModal,
    CTkDropdownDialog,
    CTkInputModal,
    SwitchAccountModal,
    TransactionHistoryModal,
)
from .theme import CARD_BG, PRIMARY, PRIMARY_HOVER


class UIActions:
    """Maps dashboard buttons to operations with input validation."""

    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root

    def _refresh_dashboard(self):
        """Helper to trigger metric card update on root window if supported."""
        if hasattr(self.root, "refresh_summary_cards"):
            self.root.refresh_summary_cards()

    def category_dropdown_menu(self, prompt_title):
        """Show category picker and return normalized key or None."""
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

    def set_budget(self):
        """Prompt for category and amount, then save budget limit."""
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
            self.user.set_budget_limit(category, raw_limit)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Budget Saved",
                message=f"Limit for {category.capitalize()} set to {float(raw_limit):.2f} {self.user.currency}.",
                icon="check", master=self.root,
            )
        except ValueError as exc:
            CTkMessagebox(title="Invalid Input", message=str(exc), icon="cancel", master=self.root)

    def add_expense(self):
        """Prompt for category, amount, note, and date, then record transaction."""
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

        if budget_limit > 0 and (current_spending + amount) > budget_limit:
            msg = CTkMessagebox(
                title="Over Budget Warning",
                message=(
                    f"Adding {amount:.2f} {self.user.currency} will exceed your "
                    f"budget for {category.capitalize()} ({budget_limit:.2f} {self.user.currency}).\n\n"
                    f"Record transaction anyway?"
                ),
                icon="warning", option_1="No", option_2="Yes", master=self.root,
            )
            if msg.get() != "Yes":
                return

        self.user.add_transaction(category, amount, note=note, date=date_str)
        self._refresh_dashboard()
        CTkMessagebox(
            title="Expense Recorded",
            message=f"Logged {amount:.2f} {self.user.currency} under {category.capitalize()}.",
            icon="check", master=self.root,
        )

    def remove_expense(self):
        """Subtract expense from category."""
        category = self.category_dropdown_menu("remove an expense from")
        if not category:
            return
        current_spent = self.user.get_category_expenses().get(category, 0.0)
        if current_spent <= 0:
            CTkMessagebox(title="No Expenses", message=f"No spending recorded in '{category.capitalize()}'.", icon="info", master=self.root)
            return

        dialog = CTkInputModal(
            title="Remove Expense",
            text=f"Current spending in {category.capitalize()}: {current_spent:.2f} {self.user.currency}\nAmount to subtract:",
            master=self.root,
        )
        raw_amount = dialog.get_input()
        if not raw_amount:
            return
        try:
            amount = float(raw_amount)
            self.tracker.remove_expense(category, amount)
            self._refresh_dashboard()
            CTkMessagebox(
                title="Expense Removed",
                message=f"Subtracted {amount:.2f} {self.user.currency} from {category.capitalize()}.",
                icon="check", master=self.root,
            )
        except ValueError as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def show_transactions(self):
        """Open scrollable transaction ledger modal."""
        modal = TransactionHistoryModal(self.user, master=self.root)
        self.root.wait_window(modal)
        self._refresh_dashboard()

    def add_custom_category(self):
        """Prompt user for new category name and add to profile."""
        dialog = CTkInputModal(
            title="New Category",
            text="Enter custom category name:",
            master=self.root,
        )
        cat_name = dialog.get_input()
        if not cat_name:
            return
        try:
            created = self.user.add_custom_category(cat_name)
            CTkMessagebox(
                title="Category Added",
                message=f"Custom category '{created.capitalize()}' added successfully!",
                icon="check", master=self.root,
            )
        except ValueError as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self.root)

    def export_to_csv(self):
        """Export all user transactions to a selected CSV file."""
        default_file = f"expenses_{self.user.name.lower()}.csv"
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Expenses to CSV",
            initialfile=default_file,
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        try:
            self.user.export_to_csv(filepath)
            CTkMessagebox(
                title="Export Complete",
                message=f"Transactions successfully exported to:\n{os.path.basename(filepath)}",
                icon="check", master=self.root,
            )
        except OSError as exc:
            CTkMessagebox(title="Export Failed", message=str(exc), icon="cancel", master=self.root)

    def reset_category(self):
        """Clear budget and expense history for selected category."""
        category = self.category_dropdown_menu("reset")
        if not category:
            return
        removed = self.user.reset_category(category)
        self._refresh_dashboard()
        CTkMessagebox(
            title="Category Reset",
            message=(
                f"Reset all data for {category.capitalize()}.\n"
                f"  Budget removed: {removed['budget_limit']}\n"
                f"  Expenses removed: {removed['expense']:.2f} {self.user.currency}"
            ),
            icon="check", master=self.root,
        )

    def change_account_currency(self, new_currency, currency_selector):
        """Convert all budgets and transactions to new currency with user confirmation."""
        if self.user.currency == new_currency:
            return
        msg = CTkMessagebox(
            title="Convert Currency",
            message=f"Convert all budgets and transactions from {self.user.currency} to {new_currency}?",
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
        """Display window with financial status report."""
        status_win = ctk.CTkToplevel(self.root)
        status_win.title("Financial Status Dashboard")
        status_win.geometry("580x440")
        status_win.configure(fg_color=CARD_BG)
        text_widget = ctk.CTkTextbox(status_win, font=("Consolas", 12), activate_scrollbars=True)
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", self.tracker.get_status_report())
        text_widget.configure(state="disabled")
        ctk.CTkButton(
            status_win, text="Close", command=status_win.destroy,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
        ).pack(fill="x", padx=15, pady=(0, 15))
        status_win.transient(self.root)
        status_win.focus_set()

    def show_chart(self):
        """Open 3-way interactive visual analytics window."""
        from .chart_viewer import ChartViewer
        ChartViewer.show_expense_pie_chart(parent_root=self.root, user=self.user)

    def switch_user_profile(self):
        """Open account switch dialog and switch profile."""
        modal = SwitchAccountModal(self.users, master=self.root)
        new_username = modal.get_username()
        if new_username:
            self.root.switch_user_workflow(new_username)

    def exit_app(self):
        """Gracefully close the application."""
        self.root.after(0, self.root.on_close)
