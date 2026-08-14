"""Dashboard actions and input handling for the expense app."""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .data_manager import VALID_CATEGORIES, cat_v
from .modals import CTkDropdownDialog, CTkInputModal, SwitchAccountModal
from .theme import CARD_BG, PRIMARY, PRIMARY_HOVER


class UIActions:
    """Maps dashboard buttons to operations with input validation."""

    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root

    def category_dropdown_menu(self, prompt_title):
        """Show category picker and return normalized key or None."""
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
        """Prompt for category and amount, then save budget limit."""
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

    def add_expense(self):
        """Prompt for category and amount, record expense with budget warning."""
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
        """Prompt for category and amount to subtract from expenses."""
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

    def reset_category(self):
        """Clear budget and expense history for selected category."""
        category = self.category_dropdown_menu("reset")
        if not category:
            return
        removed = self.user.reset_category(category)
        CTkMessagebox(
            title="Category Reset",
            message=(
                f"Reset all data for {category}.\n"
                f"  Budget removed: {removed['budget_limit']}\n"
                f"  Expenses removed: {removed['expense']}"
            ),
            icon="check",
        )

    # Alias for backward compatibility
    purge = reset_category

    def change_account_currency(self, new_currency, currency_selector):
        """Convert all budgets and expenses to new currency with user confirmation."""
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
        """Display window with financial status report."""
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
        """Open pie chart of logged expense distribution."""
        from .chart_viewer import ChartViewer
        ChartViewer.show_expense_pie_chart(
            parent_root=self.root,
            expense_data=self.tracker.expenseReport,
            currency=self.user.currency,
        )

    def switch_user_profile(self):
        """Open account switch dialog and switch profile."""
        modal = SwitchAccountModal(self.users, master=self.root)
        new_username = modal.get_username()
        if new_username:
            self.root.switch_user_workflow(new_username)

    def exit_app(self):
        """Gracefully close the application."""
        self.root.after(0, self.root.on_close)
