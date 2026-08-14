"""CustomTkinter modal dialogs for authentication, inputs, transactions, incomes, and filters."""
from datetime import datetime
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .data_manager import normalize_username
from .security import SecurityManager
from .theme import (
    APP_BG, BODY, CARD_BG, CARD_BORDER, DANGER, DANGER_HOVER, MUTED,
    PRIMARY, PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER, TITLE, format_amount,
)


class BaseModal(ctk.CTkToplevel):
    """Base modal dialog window with centering."""

    def __init__(self, master, title, width=420, height=340):
        super().__init__(master)
        self.master = master
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=APP_BG)
        self.resizable(False, False)

        self.update_idletasks()
        if master:
            x = master.winfo_x() + (master.winfo_width() // 2) - (width // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (height // 2)
            self.geometry(f"+{x}+{y}")

        self.transient(master)
        self.grab_set()
        self._result = None

    def get_result(self):
        """Wait for window to close and return result."""
        self.wait_window(self)
        return self._result


class SignInModal(BaseModal):
    """User login dialog with username and password inputs."""

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Sign In", width=420, height=360)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG, border_width=2, border_color=CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        accent = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=PRIMARY)
        accent.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="Welcome Back", font=("Segoe UI", 20, "bold"), text_color=TITLE).pack(pady=(0, 15))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12))
        self.user_entry.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(4, 20))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Sign In", width=320, height=40, font=("Segoe UI", 13, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        raw_name = self.user_entry.get()
        password = self.pass_entry.get()
        username = normalize_username(raw_name)

        if not username or not password:
            CTkMessagebox(title="Error", message="All fields are required.", icon="cancel", master=self.master)
            return

        if not SecurityManager.verify_login(username, password):
            remaining = SecurityManager.get_lockout_remaining(username)
            if remaining > 0:
                CTkMessagebox(
                    title="Account Locked",
                    message=f"Too many failed attempts. Account is locked for {remaining} more seconds.",
                    icon="warning", master=self.master,
                )
            else:
                CTkMessagebox(title="Access Denied", message="Invalid username or password.", icon="cancel", master=self.master)
            return

        self._username_result = username
        self.destroy()

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class SignUpModal(BaseModal):
    """User registration dialog with password complexity enforcement."""

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Create Account", width=420, height=460)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG, border_width=2, border_color=CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        accent = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=SUCCESS)
        accent.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="New Account", font=("Segoe UI", 20, "bold"), text_color=TITLE).pack(pady=(0, 10))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12))
        self.user_entry.pack(pady=(2, 10))

        ctk.CTkLabel(inner, text="Password (min 8 chars, Upper, Lower, Digit):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(2, 8))

        ctk.CTkLabel(inner, text="Re-enter Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.confirm_pass_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.confirm_pass_entry.pack(pady=(2, 18))
        self.confirm_pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Register & Sign In", width=320, height=40, font=("Segoe UI", 13, "bold"),
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        raw_name = self.user_entry.get()
        password = self.pass_entry.get()
        confirm_password = self.confirm_pass_entry.get()
        username = normalize_username(raw_name)

        if not username or not password or not confirm_password:
            CTkMessagebox(title="Error", message="All fields are required.", icon="cancel", master=self.master)
            return

        success, message = SecurityManager.register_user(username, password, confirm_password)
        if not success:
            title = "Password Mismatch" if "match" in message.lower() else "Error"
            CTkMessagebox(title=title, message=message, icon="warning", master=self.master)
            return

        self._username_result = username
        self.destroy()

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class SwitchAccountModal(BaseModal):
    """Modal for switching accounts, strictly filtering out the active user."""

    def __init__(self, users_container, current_user=None, master=None):
        super().__init__(master, title="Switch Account", width=380, height=340)
        self.users = users_container
        self.current_user = normalize_username(current_user) if current_user else ""
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Select Account to Switch To:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))

        all_users = self.users.show_users()
        available_users = [u for u in all_users if normalize_username(u) != self.current_user]

        if not available_users:
            menu_values = ["No Other Accounts Available"]
            self.has_targets = False
        else:
            menu_values = available_users
            self.has_targets = True

        self.user_menu = ctk.CTkOptionMenu(inner, values=menu_values, width=320, height=36)
        self.user_menu.pack(pady=(0, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(0, 20))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Switch Account", width=320, height=38,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        if not self.has_targets:
            CTkMessagebox(title="No Other Accounts", message="There are no other user accounts registered to switch to.", icon="info", master=self.master)
            return

        selected = self.user_menu.get()
        password = self.pass_entry.get()

        if not selected or selected == "No Other Accounts Available":
            CTkMessagebox(title="Error", message="Please select a valid user account.", icon="cancel", master=self.master)
            return

        if not password:
            CTkMessagebox(title="Error", message="Password is required to switch accounts.", icon="cancel", master=self.master)
            return

        username = normalize_username(selected)
        if username == self.current_user:
            CTkMessagebox(title="Error", message="You are already logged into this account.", icon="warning", master=self.master)
            return

        if not SecurityManager.verify_login(username, password):
            remaining = SecurityManager.get_lockout_remaining(username)
            if remaining > 0:
                CTkMessagebox(
                    title="Account Locked",
                    message=f"Too many failed attempts. Account is locked for {remaining} more seconds.",
                    icon="warning", master=self.master,
                )
            else:
                CTkMessagebox(title="Access Denied", message="Invalid password for this account.", icon="cancel", master=self.master)
            return

        self._username_result = username
        self.destroy()

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class CTkInputModal(BaseModal):
    """Prompt modal for text input."""

    def __init__(self, title, text, show=None, master=None):
        super().__init__(master, title=title, width=380, height=220)
        self.text = text
        self.show = show
        self._input_result = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text=self.text, font=("Segoe UI", 12), text_color=BODY, wraplength=340).pack(pady=(0, 10))

        self.entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show=self.show if self.show else "")
        self.entry.pack(pady=(0, 15))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Confirm", width=320, height=36,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        self._input_result = self.entry.get().strip()
        self.destroy()

    def get_input(self):
        self.wait_window(self)
        return self._input_result


class CTkDropdownDialog(BaseModal):
    """Dropdown selector dialog."""

    def __init__(self, title, text, values, master=None):
        super().__init__(master, title=title, width=380, height=220)
        self.text = text
        self.values = values
        self._selection_result = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text=self.text, font=("Segoe UI", 12), text_color=BODY).pack(pady=(0, 10))

        self.dropdown = ctk.CTkOptionMenu(inner, values=self.values, width=320, height=36)
        self.dropdown.pack(pady=(0, 15))
        if self.values:
            self.dropdown.set(self.values[0])

        ctk.CTkButton(
            inner, text="Select", width=320, height=36,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        self._selection_result = self.dropdown.get()
        self.destroy()

    def get_input(self):
        self.wait_window(self)
        return self._selection_result


class AddExpenseModal(BaseModal):
    """Enhanced dialog for logging an expense with automatic up-to-date dates and validation."""

    def __init__(self, categories, currency="USD", master=None):
        super().__init__(master, title="Record New Expense", width=440, height=460)
        self.categories = [c.capitalize() for c in categories]
        self.currency = currency
        self._expense_data = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="Category:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.cat_menu = ctk.CTkOptionMenu(inner, values=self.categories, width=380, height=34)
        self.cat_menu.pack(pady=(2, 10))
        if self.categories:
            self.cat_menu.set(self.categories[0])

        ctk.CTkLabel(inner, text=f"Amount ({self.currency}):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.amount_entry = ctk.CTkEntry(inner, width=380, height=34, font=("Segoe UI", 12), placeholder_text="e.g. 1,250.00 or 45.99")
        self.amount_entry.pack(pady=(2, 10))

        ctk.CTkLabel(inner, text="Note / Description (Optional):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.note_entry = ctk.CTkEntry(
            inner, width=380, height=34, font=("Segoe UI", 12),
            placeholder_text="e.g. Weekly grocery shopping at Lidl",
        )
        self.note_entry.pack(pady=(2, 10))

        ctk.CTkLabel(inner, text="Date (YYYY-MM-DD):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.date_entry = ctk.CTkEntry(inner, width=380, height=34, font=("Segoe UI", 12))
        
        current_today = datetime.now().strftime("%Y-%m-%d")
        self.date_entry.insert(0, current_today)
        self.date_entry.pack(pady=(2, 18))
        self.date_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Save Expense", width=380, height=40, font=("Segoe UI", 13, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        category = self.cat_menu.get().lower().strip()
        raw_amount = self.amount_entry.get().strip().replace(",", "").replace(" ", "")
        note = self.note_entry.get().strip()[:200]
        raw_date = self.date_entry.get().strip()

        if not raw_amount:
            CTkMessagebox(title="Input Error", message="Please enter an expense amount.", icon="cancel", master=self.master)
            return

        try:
            amount = float(raw_amount)
            if amount <= 0:
                CTkMessagebox(title="Invalid Amount", message="Amount must be greater than zero.", icon="cancel", master=self.master)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Amount", message="Please enter a valid numeric amount.", icon="cancel", master=self.master)
            return

        if not raw_date:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(raw_date, "%Y-%m-%d")
                date_str = raw_date
            except ValueError:
                CTkMessagebox(
                    title="Invalid Date Format",
                    message="Date must be in YYYY-MM-DD format (e.g. 2026-08-14), or left blank for today.",
                    icon="warning", master=self.master,
                )
                return

        self._expense_data = {
            "category": category,
            "amount": amount,
            "note": note,
            "date": date_str,
        }
        self.destroy()

    def get_expense_data(self):
        self.wait_window(self)
        return self._expense_data


class AddIncomeModal(BaseModal):
    """Dialog for logging an income source with date, amount, and note."""

    def __init__(self, currency="USD", master=None):
        super().__init__(master, title="Record Income", width=440, height=440)
        self.currency = currency
        self._income_data = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="Income Source:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.source_menu = ctk.CTkOptionMenu(
            inner, values=["Salary", "Freelance", "Investment", "Business", "Gift", "Other"],
            width=380, height=34,
        )
        self.source_menu.pack(pady=(2, 10))
        self.source_menu.set("Salary")

        ctk.CTkLabel(inner, text=f"Amount ({self.currency}):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.amount_entry = ctk.CTkEntry(inner, width=380, height=34, font=("Segoe UI", 12), placeholder_text="e.g. 3,500.00")
        self.amount_entry.pack(pady=(2, 10))

        ctk.CTkLabel(inner, text="Note / Description (Optional):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.note_entry = ctk.CTkEntry(inner, width=380, height=34, font=("Segoe UI", 12), placeholder_text="e.g. Monthly salary paycheck")
        self.note_entry.pack(pady=(2, 10))

        ctk.CTkLabel(inner, text="Date (YYYY-MM-DD):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.date_entry = ctk.CTkEntry(inner, width=380, height=34, font=("Segoe UI", 12))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(pady=(2, 18))
        self.date_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Save Income", width=380, height=40, font=("Segoe UI", 13, "bold"),
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        source = self.source_menu.get().strip()
        raw_amount = self.amount_entry.get().strip().replace(",", "").replace(" ", "")
        note = self.note_entry.get().strip()[:200]
        raw_date = self.date_entry.get().strip()

        if not raw_amount:
            CTkMessagebox(title="Input Error", message="Please enter an income amount.", icon="cancel", master=self.master)
            return

        try:
            amount = float(raw_amount)
            if amount <= 0:
                CTkMessagebox(title="Invalid Amount", message="Amount must be greater than zero.", icon="cancel", master=self.master)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Amount", message="Please enter a valid numeric amount.", icon="cancel", master=self.master)
            return

        if not raw_date:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(raw_date, "%Y-%m-%d")
                date_str = raw_date
            except ValueError:
                CTkMessagebox(
                    title="Invalid Date Format",
                    message="Date must be in YYYY-MM-DD format (e.g. 2026-08-14), or left blank for today.",
                    icon="warning", master=self.master,
                )
                return

        self._income_data = {
            "source": source,
            "amount": amount,
            "note": note,
            "date": date_str,
        }
        self.destroy()

    def get_income_data(self):
        self.wait_window(self)
        return self._income_data


class TransactionHistoryModal(ctk.CTkToplevel):
    """Scrollable ledger dialog with thousands-separated amounts and enhanced note searching."""

    def __init__(self, user, master=None):
        super().__init__(master)
        self.user = user
        self.master = master
        self.title("Transaction History Ledger")
        self.geometry("780x560")
        self.minsize(680, 460)
        self.configure(fg_color=APP_BG)
        self.transient(master)
        self.focus_set()

        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="📜 Expense Transactions", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(side="left")

        filter_cats = ["All Categories"] + [c.capitalize() for c in self.user.categories]
        self.filter_menu = ctk.CTkOptionMenu(
            top_frame, values=filter_cats, width=150, height=32,
            command=lambda val: self._refresh_list(),
        )
        self.filter_menu.pack(side="right", padx=(10, 0))

        self.search_entry = ctk.CTkEntry(top_frame, width=200, height=32, placeholder_text="Search notes or categories…")
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_list())

        header = ctk.CTkFrame(self, height=36, fg_color=PRIMARY)
        header.pack(fill="x", padx=20, pady=(5, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Date", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=95).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Category", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Amount", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Description / Note", font=("Segoe UI", 11, "bold"), text_color="#ffffff").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(header, text="Action", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=70).pack(side="right", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=CARD_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self._refresh_list()

    def _refresh_list(self):
        try:
            for widget in self.scroll_frame.winfo_children():
                widget.destroy()

            selected_cat = self.filter_menu.get()
            search_query = self.search_entry.get().lower().strip()

            transactions = self.user.get_transactions()
            if selected_cat != "All Categories":
                transactions = [tx for tx in transactions if tx.get("category", "").lower() == selected_cat.lower()]
            if search_query:
                transactions = [
                    tx for tx in transactions
                    if search_query in tx.get("note", "").lower() or search_query in tx.get("category", "").lower()
                ]

            if not transactions:
                ctk.CTkLabel(
                    self.scroll_frame, text="No matching transactions found.",
                    font=("Segoe UI", 12), text_color=MUTED,
                ).pack(pady=40)
                return

            for idx, tx in enumerate(transactions):
                row_bg = CARD_BG if idx % 2 == 0 else ("#f8fafc", "#23163e")
                row = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, height=38)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                tx_id = tx.get("id")
                date_str = tx.get("date", "")
                cat_str = tx.get("category", "").capitalize()
                amount_val = tx.get("amount", 0.0)
                amount_str = format_amount(amount_val, self.user.currency)
                note_str = tx.get("note", "") if tx.get("note") else "—"

                ctk.CTkLabel(row, text=date_str, font=("Segoe UI", 11), width=95, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=cat_str, font=("Segoe UI", 11, "bold"), width=110, text_color=PRIMARY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=amount_str, font=("Segoe UI", 11, "bold"), width=110, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note_str, font=("Segoe UI", 11), text_color=MUTED if note_str == "—" else BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                del_btn = ctk.CTkButton(
                    row, text="Delete", width=60, height=24, font=("Segoe UI", 10, "bold"),
                    fg_color=DANGER, hover_color=DANGER_HOVER,
                    command=lambda tid=tx_id: self._delete_tx(tid),
                )
                del_btn.pack(side="right", padx=5)
        except Exception:
            pass

    def _delete_tx(self, tx_id):
        msg = CTkMessagebox(
            title="Confirm Delete",
            message="Permanently delete this transaction?",
            icon="warning", option_1="Yes", option_2="No", master=self,
        )
        if msg.get() == "Yes":
            self.user.delete_transaction(tx_id)
            self._refresh_list()


class IncomeHistoryModal(ctk.CTkToplevel):
    """Scrollable income ledger dialog with search and deletion capabilities."""

    def __init__(self, user, master=None):
        super().__init__(master)
        self.user = user
        self.master = master
        self.title("Income Ledger")
        self.geometry("780x520")
        self.minsize(680, 420)
        self.configure(fg_color=APP_BG)
        self.transient(master)
        self.focus_set()

        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="💰 Income History", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(side="left")

        self.search_entry = ctk.CTkEntry(top_frame, width=220, height=32, placeholder_text="Search source or notes…")
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_list())

        header = ctk.CTkFrame(self, height=36, fg_color=SUCCESS)
        header.pack(fill="x", padx=20, pady=(5, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Date", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=95).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Source", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=120).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Amount", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Description / Note", font=("Segoe UI", 11, "bold"), text_color="#ffffff").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(header, text="Action", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=70).pack(side="right", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=CARD_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self._refresh_list()

    def _refresh_list(self):
        try:
            for widget in self.scroll_frame.winfo_children():
                widget.destroy()

            search_query = self.search_entry.get().lower().strip()
            incomes = self.user.get_incomes()

            if search_query:
                incomes = [
                    inc for inc in incomes
                    if search_query in inc.get("note", "").lower() or search_query in inc.get("source", "").lower()
                ]

            if not incomes:
                ctk.CTkLabel(
                    self.scroll_frame, text="No income entries found.",
                    font=("Segoe UI", 12), text_color=MUTED,
                ).pack(pady=40)
                return

            for idx, inc in enumerate(incomes):
                row_bg = CARD_BG if idx % 2 == 0 else ("#f8fafc", "#23163e")
                row = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, height=38)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                inc_id = inc.get("id")
                date_str = inc.get("date", "")
                source_str = inc.get("source", "Income")
                amount_val = inc.get("amount", 0.0)
                amount_str = format_amount(amount_val, self.user.currency)
                note_str = inc.get("note", "") if inc.get("note") else "—"

                ctk.CTkLabel(row, text=date_str, font=("Segoe UI", 11), width=95, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=source_str, font=("Segoe UI", 11, "bold"), width=120, text_color=SUCCESS).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=amount_str, font=("Segoe UI", 11, "bold"), width=110, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note_str, font=("Segoe UI", 11), text_color=MUTED if note_str == "—" else BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                del_btn = ctk.CTkButton(
                    row, text="Delete", width=60, height=24, font=("Segoe UI", 10, "bold"),
                    fg_color=DANGER, hover_color=DANGER_HOVER,
                    command=lambda iid=inc_id: self._delete_inc(iid),
                )
                del_btn.pack(side="right", padx=5)
        except Exception:
            pass

    def _delete_inc(self, inc_id):
        msg = CTkMessagebox(
            title="Confirm Delete",
            message="Permanently delete this income record?",
            icon="warning", option_1="Yes", option_2="No", master=self,
        )
        if msg.get() == "Yes":
            self.user.delete_income(inc_id)
            self._refresh_list()