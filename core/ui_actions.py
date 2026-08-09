"""
UI Actions & Dialog Handlers
Encapsulates CTkInputDialog prompts, logic, and CTkMessagebox notifications.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from .data_manager import cat_v, VALID_CATEGORIES


class CTkDropdownDialog(ctk.CTkToplevel):
    """
    Custom modal dialog providing a dropdown selection menu.
    Designed to prevent phantom background root windows associated with standard CTk dialogues.
    """
    def __init__(self, title="Select Option", text="Choose an item:", values=None, **kwargs):
        super().__init__(**kwargs)
        
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Enforce modal behavior: bind to parent window and lock focus
        self.transient(self.master)
        self.grab_set()
        
        self.user_selection = None
        self.values = values if values else ["Option 1", "Option 2"]
        
        self.label = ctk.CTkLabel(self, text=text, font=("Arial", 14))
        self.label.pack(pady=(15, 5))
        
        self.dropdown = ctk.CTkOptionMenu(self, values=self.values)
        self.dropdown.pack(pady=10)
        
        self.btn_ok = ctk.CTkButton(self, text="OK", width=100, command=self.on_confirm)
        self.btn_ok.pack(pady=(5, 15))
        
        # Calculate screen coordinates to center the modal relative to the parent window
        self.update_idletasks()
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
            
        # Suspend execution until the dialog window is destroyed
        self.wait_window()

    def on_confirm(self):
        """Captures selected option and safely terminates the dialog window."""
        self.user_selection = self.dropdown.get()
        self.destroy()

    def get_input(self):
        """Returns the user's dropdown choice."""
        return self.user_selection


class CTkInputModal(ctk.CTkToplevel):
    """
    Custom input modal replacing standard CTkInputDialog elements 
    to eliminate persistent phantom Tk root instances.
    """
    def __init__(self, title="Input", text="Enter value:", **kwargs):
        super().__init__(**kwargs)
        
        self.title(title)
        self.geometry("320x160")
        self.resizable(False, False)
        
        # Establish window transience and input grab control
        self.transient(self.master)
        self.grab_set()
        
        self.user_input = None
        
        self.label = ctk.CTkLabel(self, text=text, font=("Arial", 13), wraplength=280)
        self.label.pack(pady=(20, 10), padx=20)
        
        self.entry = ctk.CTkEntry(self, width=240, height=32)
        self.entry.pack(pady=(0, 15))
        self.entry.focus()
        # Bind the Enter key for keyboard accessibility (quick submission)
        self.entry.bind("<Return>", lambda event: self.on_confirm())
        
        self.btn_ok = ctk.CTkButton(self, text="OK", width=100, command=self.on_confirm)
        self.btn_ok.pack(pady=(0, 15))
        
        # Center the modal dynamically relative to the parent application window
        self.update_idletasks()
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
            
        # Pause event flow until user interaction completes
        self.wait_window()

    def on_confirm(self):
        """Extracts text entry string and closes the input modal."""
        self.user_input = self.entry.get()
        self.destroy()

    def get_input(self):
        """Returns the captured input string."""
        return self.user_input


class UIActions:
    """
    Controller layer handling UI event responses, validation sequences,
    and delegation to underlying financial models.
    """
    def __init__(self, user, user_tracker, users_container, app_root):
        self.user = user
        self.tracker = user_tracker
        self.users = users_container
        self.root = app_root
        self.cat_selection = cat_v

    def category_dropdown_menu(self, prompt_title):
        """Presents a formatted category selection menu to the user."""
        formatted_options = [cat.capitalize() for cat in VALID_CATEGORIES]
        
        dialog = CTkDropdownDialog(
            title="Category Selection",
            text=f"Select a category to {prompt_title}:",
            values=formatted_options,
            master=self.root
        )
        
        selected_option = dialog.get_input()
        if not selected_option:
            return None
            
        return selected_option.lower().strip()

    def change_account_currency(self, new_currency, currency_selector):
        """Handles multi-currency conversions across stored budgets and expense accounts."""
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
        """Prompts for and configures budget upper-limit thresholds per category."""
        cat = self.category_dropdown_menu("Set Budget")
        if not cat: return
        
        dialog = CTkInputModal(title="Set Budget", text=f"Budget limit amount ({self.user.currency}):", master=self.root)
        raw_limit = dialog.get_input()
        if not raw_limit: return
        try:
            self.user.set_budget_limit(cat, raw_limit)
            CTkMessagebox(title="Budget Set", message=f"Budget set to {float(raw_limit):.2f} {self.user.currency}", icon="check")
        except ValueError as e:
            CTkMessagebox(title="Invalid Input", message=str(e), icon="cancel")

    def check_budget(self):
        """Retrieves and displays the active limit for a given expense category."""
        cat = self.category_dropdown_menu("Check Budget")
        if not cat: return
        budget = self.user.check_budget(cat)
        CTkMessagebox(title="Budget Check", message=f"Current limit for {cat}: {budget:.2f} {self.user.currency}", icon="info")

    def purge(self):
        """Clears budget limits and historical data metrics for a chosen category."""
        cat = self.category_dropdown_menu("Purge Budget")
        if not cat: return
        self.user.purge(cat)
        CTkMessagebox(title="Purge Budget", message=f"Purged budget and history metrics for {cat}.", icon="check")

    def add_expense(self):
        """Validates and logs financial transactions, triggering warnings if budgets are breached."""
        cat = self.category_dropdown_menu("Add Expense")
        if not cat: return
        
        dialog = CTkInputModal(title="Add Expense", text=f"Amount for {cat} ({self.user.currency}):", master=self.root)
        raw_amount = dialog.get_input()
        if not raw_amount: return

        try:
            amount = float(raw_amount)
            if amount <= 0.0:
                CTkMessagebox(title="Invalid Input", message="Please enter a positive amount.", icon="cancel")
                return
            
            budget_limit = self.user.budget_limit.get(cat)
            current_spending = self.tracker.expenseReport.get(cat, 0.0)
            
            # Evaluate budget compliance prior to saving transaction
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

    def remove_expense(self):
        """Handles deduction of funds from specified spending categories safely."""
        cat = self.category_dropdown_menu("Remove Expense")
        if not cat: return
        
        current_spent = self.tracker.expenseReport.get(cat, 0.0)
        if current_spent <= 0:
            CTkMessagebox(title="No Expenses", message=f"No logged expenses to remove in '{cat}'.", icon="info")
            return

        dialog = CTkInputModal(
            title="Remove Expense",
            text=f"Current spending in {cat}: {current_spent:.2f} {self.user.currency}\nAmount to remove:", 
            master=self.root
        )
        raw_amount = dialog.get_input()
        if not raw_amount: return

        try:
            amount = float(raw_amount)
            if amount <= 0:
                CTkMessagebox(title="Invalid Input", message="Please enter an amount greater than zero.", icon="cancel")
                return
                
            self.tracker.remove_expense(cat, amount)
            CTkMessagebox(title="Success", message=f"Removed {amount:.2f} {self.user.currency} from {cat}.", icon="check")
        except ValueError as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

    def show_status(self):
        """Generates a text-based status dashboard window mapping budget health."""
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
        """Queries expenditure values for a targeted category."""
        cat = self.category_dropdown_menu("Search Expense")
        if not cat: return
        result = self.tracker.search_expenses(cat) 
        if result is not None:
            CTkMessagebox(title="Search Result", message=f"{self.user.name} spent {result:.2f} {self.user.currency} on {cat}", icon="info") 
        else:
            CTkMessagebox(title="Search Result", message="No transaction records found for this category.", icon="info")

    def show_chart(self):
        """Lazy-loads and displays the visual pie-chart representation of expenses."""
        from .chart_viewer import ChartViewer
        ChartViewer.show_expense_pie_chart(
            parent_root=self.root, 
            expense_data=self.tracker.expenseReport, 
            currency=self.user.currency
        )

    def total_expenses(self):
        """Computes and presents the cumulative sum of all logged expenses."""
        total = self.tracker.total_expenses_of_user()
        CTkMessagebox(title="Total Aggregate Expenses", message=f"Total user footprint portfolio costs: {total:.2f} {self.user.currency}", icon="info")

    def show_users(self):
        """Lists all profiles tracked within the database store."""
        users_list = self.users.show_users() 
        if users_list:
            CTkMessagebox(title="Users List", message="Current Users:\n\n" + "\n".join(users_list), icon="info") 
        else:
            CTkMessagebox(title="Users List", message="No active logs mapped.", icon="info")

    def delete_user(self):
        """Permanently scrubs target user profile records from configuration files."""
        dialog = CTkInputModal(title="Delete User", text="Enter username to delete:", master=self.root)
        raw_del_name = dialog.get_input()
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
        """Looks up specific user configuration metrics and summarizes financial history."""
        dialog = CTkInputModal(title="Find User", text="Enter username to find:", master=self.root)
        raw_search_name = dialog.get_input()
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
        """Triggers application shutdown sequence via root window close binding."""
        self.root.after(0, self.root.on_close)