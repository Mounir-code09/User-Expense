"""
UI Actions Module
-----------------
Event handlers and user-facing notifications for the expense tracker dashboard.

This module contains `UIActions` controller
that maps each dashboard button to a business-logic operation. All reusable pop-up
dialogs live in the separate `core.modals` module so that presentation code is
not mixed with orchestration code here.

Every input path validates categories through ``cat_v`` and normalizes usernames through
``normalize_username`` so data stays consistent with the core layer.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .data_manager import cat_v, VALID_CATEGORIES, normalize_username
from .modals import (
    CTkDropdownDialog,
    CTkInputModal,
    SwitchAccountModal,
)
from .security import SecurityManager
from .theme import (
    CARD_BG, PRIMARY, PRIMARY_HOVER,
)


class UIActions:
    """Maps dashboard buttons to business-logic operations with input validation."""

    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root

    def category_dropdown_menu(self, prompt_title: str):
        """
        Show a category picker and return the normalized lowercase key.

        Returns ``None`` when the user cancels or selects an invalid category.
        """
        formatted_options = [cat.capitalize() for cat in VALID_CATEGORIES]
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
        if not cat_v(normalized):
            CTkMessagebox(title="Invalid Category", message="The selected category is not recognized.", icon="cancel")
            return None
        return normalized

    def set_budget(self):
        """Prompt for a category and an amount, then store the budget limit."""
        category = self.category_dropdown_menu("set a budget for")
        if not category:
            return
        dialog = CTkInputModal(
            title="Set Budget",
            text=f"Budget limit ({self.user.currency}):",
            master=self.root,
        )
        raw_limit = dialog.get_input()
        if not raw_limit:
            return
        try:
            self.user.set_budget_limit(category, raw_limit)
            CTkMessagebox(
                title="Budget Saved",
                message=f"Limit for {category} set to {float(raw_limit):.2f} {self.user.currency}.",
                icon="check",
            )
        except ValueError as exc:
            CTkMessagebox(title="Invalid Input", message=str(exc), icon="cancel")

    def check_budget(self):
        """Prompt for a category and display its configured budget limit."""
        category = self.category_dropdown_menu("check the budget for")
        if not category:
            return
        budget = self.user.check_budget(category)
        CTkMessagebox(
            title="Budget Check",
            message=f"Current limit for {category}: {budget:.2f} {self.user.currency}",
            icon="info",
        )

    def add_expense(self):
        """Prompt for a category and an amount, then record the expense."""
        category = self.category_dropdown_menu("add an expense to")
        if not category:
            return
        dialog = CTkInputModal(
            title="Add Expense",
            text=f"Amount for {category} ({self.user.currency}):",
            master=self.root,
        )
        raw_amount = dialog.get_input()
        if not raw_amount:
            return
        try:
            amount = float(raw_amount)
            if amount <= 0.0:
                CTkMessagebox(title="Invalid Amount", message="Please enter a positive amount.", icon="cancel")
                return

            budget_limit = self.user.budget_limit.get(category)
            current_spending = self.tracker.expenseReport.get(category, 0.0)

            # Warn before exceeding a configured budget limit, but let the user override.
            if budget_limit is not None and budget_limit > 0 and (current_spending + amount) > budget_limit:
                msg = CTkMessagebox(
                    title="Over Budget",
                    message=(
                        f"Adding {amount:.2f} {self.user.currency} will exceed the "
                        f"{category} limit.\nSave the transaction anyway?"
                    ),
                    icon="warning", option_1="No", option_2="Yes",
                )
                if msg.get() != "Yes":
                    return

            self.tracker.add_expense(category, amount)
            CTkMessagebox(
                title="Expense Recorded",
                message=f"Logged {amount:.2f} {self.user.currency} under {category}.",
                icon="check",
            )
        except ValueError:
            CTkMessagebox(title="Invalid Input", message="Please enter a valid number.", icon="cancel")

    def remove_expense(self):
        """Prompt for a category and an amount, then subtract spending from it."""
        category = self.category_dropdown_menu("remove an expense from")
        if not category:
            return
        current_spent = self.tracker.expenseReport.get(category, 0.0)
        if current_spent <= 0:
            CTkMessagebox(title="No Expenses", message=f"No spending recorded in '{category}'.", icon="info")
            return

        dialog = CTkInputModal(
            title="Remove Expense",
            text=f"Current spending: {current_spent:.2f} {self.user.currency}\nAmount to remove:",
            master=self.root,
        )
        raw_amount = dialog.get_input()
        if not raw_amount:
            return
        try:
            amount = float(raw_amount)
            self.tracker.remove_expense(category, amount)
            CTkMessagebox(
                title="Expense Removed",
                message=f"Removed {amount:.2f} {self.user.currency} from {category}.",
                icon="check",
            )
        except ValueError as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel")

    def purge(self):
        """Prompt for a category and clear both its budget and its expense history."""
        category = self.category_dropdown_menu("purge")
        if not category:
            return
        removed = self.user.purge(category)
        CTkMessagebox(
            title="Category Purged",
            message=(
                f"Cleared all data for {category}.\n"
                f"  Budget removed: {removed['budget_limit']}\n"
                f"  Expenses removed: {removed['expense']}"
            ),
            icon="check",
        )

    def change_account_currency(self, new_currency: str, currency_selector):
        """
        Re-denominate all stored data into a new base currency.

        The user confirms the conversion first; on refusal the selector is reset.
        """
        if self.user.currency == new_currency:
            return
        msg = CTkMessagebox(
            title="Convert Currency",
            message=f"Convert all stored data from {self.user.currency} to {new_currency}?",
            icon="question", option_1="Yes", option_2="No",
        )
        if msg.get() == "Yes":
            self.user.convert_account_currency(new_currency)
            currency_selector.set(new_currency)
            CTkMessagebox(
                title="Currency Updated",
                message=f"All amounts are now recorded in {new_currency}.",
                icon="check",
            )
        else:
            currency_selector.set(self.user.currency)

    def show_status(self):
        """Open a read-only window displaying the full financial status report."""
        status_win = ctk.CTkToplevel(self.root)
        status_win.title("Financial Status Dashboard")
        status_win.geometry("560x420")
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
        """Open a Matplotlib pie chart of the logged expense distribution."""
        from .chart_viewer import ChartViewer
        ChartViewer.show_expense_pie_chart(
            parent_root=self.root,
            expense_data=self.tracker.expenseReport,
            currency=self.user.currency,
        )

    def total_expenses(self):
        """Display the combined spending across every category."""
        total = self.tracker.total_expenses_of_user()
        CTkMessagebox(
            title="Total Expenses",
            message=f"Combined spending: {total:.2f} {self.user.currency}",
            icon="info",
        )

    def show_users(self):
        """List every registered username in a message box."""
        users_list = self.users.show_users()
        if users_list:
            CTkMessagebox(title="Registered Users", message="Active profiles:\n\n" + "\n".join(users_list), icon="info")
        else:
            CTkMessagebox(title="Registered Users", message="No profiles found.", icon="info")

    def switch_user_profile(self):
        """Open the account-switch dialog and transition to the chosen profile."""
        modal = SwitchAccountModal(self.users, master=self.root)
        new_username = modal.get_username()
        if new_username:
            self.root.switch_user_workflow(new_username)

    def get_user(self):
        """Look up another profile after re-authenticating the active user."""
        auth_dialog = CTkInputModal(
            title="Authorization Required",
            text=f"Enter the password for '{self.user.name}' to continue:",
            show="*",
            master=self.root,
        )
        auth_pass = auth_dialog.get_input()
        if not auth_pass:
            return

        if not SecurityManager.verify_login(self.user.name, auth_pass):
            CTkMessagebox(title="Access Denied", message="Incorrect password.", icon="cancel", master=self.root)
            return

        dialog = CTkInputModal(title="Find User", text="Enter the username to look up:", master=self.root)
        raw_name = dialog.get_input()
        if not raw_name:
            return

        search_name = normalize_username(raw_name)
        target_user = self.users.get_user(search_name)
        if target_user:
            info = f"Profile: {target_user.name}\nCurrency: {target_user.currency}\n\nBudget Limits:\n"
            if target_user.budget_limit:
                for cat, limit in target_user.budget_limit.items():
                    info += f"  • {cat.capitalize()}: {limit:.2f} {target_user.currency}\n"
            else:
                info += "  (none configured)\n"
            total_spent = sum(target_user.current_expenses.values())
            info += f"\nTotal Spent: {total_spent:.2f} {target_user.currency}"
            CTkMessagebox(title=f"Profile: {search_name}", message=info, icon="info")
        else:
            CTkMessagebox(title="Not Found", message=f"No profile named '{search_name}'.", icon="cancel")

    def delete_user(self):
        """
        Delete a user profile after password confirmation.

        Because passwords live in the same database record, deletion is fully atomic —
        no orphaned credentials remain.
        """
        dialog = CTkInputModal(title="Delete User", text="Enter the username to delete:", master=self.root)
        raw_name = dialog.get_input()
        if not raw_name:
            return

        del_name = normalize_username(raw_name)
        if del_name not in self.users.show_users():
            CTkMessagebox(title="Not Found", message="That profile does not exist.", icon="cancel")
            return

        pwd_dialog = CTkInputModal(
            title="Confirm Identity",
            text=f"Enter the password for '{del_name}':",
            show="*",
            master=self.root,
        )
        password = pwd_dialog.get_input()
        if not password:
            return

        if not SecurityManager.verify_login(del_name, password):
            CTkMessagebox(title="Deletion Denied", message="Incorrect password.", icon="cancel")
            return

        msg = CTkMessagebox(
            title="Confirm Deletion",
            message=f"Permanently delete '{del_name}'?\nThis removes all financial data and credentials.",
            icon="warning", option_1="Yes", option_2="No",
        )
        if msg.get() == "Yes":
            self.users.delete_user(del_name)
            CTkMessagebox(title="Deleted", message=f"Profile '{del_name}' has been removed.", icon="check")
            if del_name == self.user.name:
                self.root.switch_user_workflow()

    def exit_app(self):
        """Gracefully close the application on the next event-loop tick."""
        self.root.after(0, self.root.on_close)
