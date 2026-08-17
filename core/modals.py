from datetime import date, datetime
import os
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .data_manager import normalize_username
from .security import SecurityManager
from .exceptions import (
    AccountLockedError,
    AuthenticationError,
    PasswordValidationError,
)
from .theme import (
    APP_BG, BODY, CARD_BG, CARD_BORDER, DANGER, DANGER_HOVER, MUTED,
    NEUTRAL, NEUTRAL_HOVER, PRIMARY, PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER,
    TITLE, WARNING, format_amount,
)


class BaseModal(ctk.CTkToplevel):

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
        self.wait_window(self)
        return self._result


class SignInModal(BaseModal):

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Sign In", width=420, height=400)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG, border_width=2, border_color=CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=PRIMARY).pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="Welcome Back", font=("Segoe UI", 20, "bold"), text_color=TITLE).pack(pady=(0, 15))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12))
        self.user_entry.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(4, 14))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Sign In", width=320, height=40, font=("Segoe UI", 13, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

        ctk.CTkButton(
            inner, text="Forgot Password?", width=320, height=32, font=("Segoe UI", 11),
            fg_color="transparent", hover_color=CARD_BORDER, text_color=MUTED,
            command=self._open_recovery,
        ).pack(pady=(8, 0))

    def _open_recovery(self):
        self.withdraw()
        modal = PasswordRecoveryModal(self.users, master=self.master)
        result = modal.get_username()
        if result:
            self._username_result = result
            self.destroy()
        else:
            self.deiconify()

    def _submit(self):
        username = normalize_username(self.user_entry.get())
        password = self.pass_entry.get()

        if not username or not password:
            CTkMessagebox(title="Error", message="All fields are required.", icon="cancel", master=self)
            return

        try:
            SecurityManager.authenticate(username, password)
            self._username_result = username
            self.destroy()
        except AccountLockedError as e:
            CTkMessagebox(
                title="Account Locked",
                message=f"Too many failed attempts. Account is locked for {e} more seconds.",
                icon="warning", master=self,
            )
        except AuthenticationError:
            CTkMessagebox(title="Access Denied", message="Invalid username or password.", icon="cancel", master=self)

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class SignUpModal(BaseModal):

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Create Account", width=440, height=660)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    SECURITY_QUESTIONS = [
        "What is a private recovery passphrase known only to you?",
        "What was the name of your first childhood school teacher?",
        "What was the make, model, and year of your first vehicle?",
        "In what city or town did your parents first meet?",
        "What was the name of the hospital where you were born?",
        "What is the middle name of your oldest relative?",
        "Custom question...",
    ]

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG, border_width=2, border_color=CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.94)

        ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=SUCCESS).pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=14)

        ctk.CTkLabel(inner, text="New Account", font=("Segoe UI", 20, "bold"), text_color=TITLE).pack(pady=(0, 8))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12))
        self.user_entry.pack(pady=(2, 6))

        ctk.CTkLabel(inner, text="Password (min 8 chars, Upper, Lower, Digit):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(2, 6))

        ctk.CTkLabel(inner, text="Re-enter Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.confirm_pass_entry = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), show="*")
        self.confirm_pass_entry.pack(pady=(2, 8))

        ctk.CTkFrame(inner, height=1, fg_color=CARD_BORDER).pack(fill="x", pady=4)
        ctk.CTkLabel(inner, text="Account Recovery Question", font=("Segoe UI", 10, "bold"), text_color=MUTED).pack(anchor="w")

        self.question_menu = ctk.CTkOptionMenu(
            inner, values=self.SECURITY_QUESTIONS, width=360, height=32,
            command=self._on_question_select,
        )
        self.question_menu.set(self.SECURITY_QUESTIONS[0])
        self.question_menu.pack(pady=(4, 4))

        self.custom_q_entry = ctk.CTkEntry(inner, width=360, height=32, font=("Segoe UI", 11), placeholder_text="Type your custom security question…")

        ctk.CTkLabel(inner, text="Security Answer (min 3 chars):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w", pady=(4, 0))
        self.answer_entry = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), placeholder_text="Enter secret answer")
        self.answer_entry.pack(pady=(2, 12))
        self.answer_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Register & Sign In", width=360, height=38, font=("Segoe UI", 13, "bold"),
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, text_color="#ffffff", command=self._submit,
        ).pack()

    def _on_question_select(self, choice):
        if choice == "Custom question...":
            self.custom_q_entry.pack(pady=(0, 4), before=self.answer_entry)
        else:
            self.custom_q_entry.pack_forget()

    def _submit(self):
        username = normalize_username(self.user_entry.get())
        password = self.pass_entry.get()
        confirm = self.confirm_pass_entry.get()
        choice = self.question_menu.get()
        if choice == "Custom question...":
            question = self.custom_q_entry.get().strip()
        else:
            question = choice
        answer = self.answer_entry.get().strip()

        if not username or not password or not confirm:
            CTkMessagebox(title="Error", message="Username and passwords are required.", icon="cancel", master=self)
            return

        if not question or not answer:
            CTkMessagebox(title="Error", message="Security question and answer are required for account recovery.", icon="cancel", master=self)
            return

        if len(answer) < 3:
            CTkMessagebox(title="Error", message="Security answer must be at least 3 characters long.", icon="warning", master=self)
            return

        try:
            SecurityManager.register_user(username, password, confirm, security_question=question, security_answer=answer)
            self._username_result = username
            self.destroy()
        except PasswordValidationError as e:
            title = "Password Mismatch" if "match" in str(e).lower() else "Password Error"
            CTkMessagebox(title=title, message=str(e), icon="warning", master=self)
        except AuthenticationError as e:
            CTkMessagebox(title="Registration Error", message=str(e), icon="cancel", master=self)

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class ChangePasswordModal(BaseModal):

    def __init__(self, username, master=None):
        super().__init__(master, title="Change Password", width=420, height=430)
        self.username = username
        self._success = False
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(inner, text="Update Password", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(pady=(0, 12))

        ctk.CTkLabel(inner, text="Current Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.current_pass = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.current_pass.pack(pady=(2, 8))

        ctk.CTkLabel(inner, text="New Password (min 8 chars, Upper, Lower, Digit):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.new_pass = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.new_pass.pack(pady=(2, 8))

        ctk.CTkLabel(inner, text="Confirm New Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.confirm_new_pass = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.confirm_new_pass.pack(pady=(2, 16))
        self.confirm_new_pass.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Update Password", width=320, height=38, font=("Segoe UI", 12, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack()

    def _submit(self):
        cur = self.current_pass.get()
        new = self.new_pass.get()
        confirm = self.confirm_new_pass.get()

        if not cur or not new or not confirm:
            CTkMessagebox(title="Input Error", message="All fields are required.", icon="cancel", master=self)
            return

        try:
            SecurityManager.change_password(self.username, cur, new, confirm)
            self._success = True
            parent = self.master
            self.destroy()
            if parent:
                CTkMessagebox(title="Success", message="Password updated successfully.", icon="check", master=parent)
        except PasswordValidationError as e:
            CTkMessagebox(title="Password Error", message=str(e), icon="warning", master=self)
        except AuthenticationError as e:
            CTkMessagebox(title="Authentication Error", message=str(e), icon="cancel", master=self)

    def is_successful(self):
        self.wait_window(self)
        return self._success


class SwitchAccountModal(BaseModal):

    def __init__(self, users_container, current_user=None, master=None):
        super().__init__(master, title="Switch Account", width=380, height=390)
        self.users = users_container
        self.current_user = normalize_username(current_user) if current_user else ""
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Select Account to Switch To:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))

        available = [u for u in self.users.show_users() if normalize_username(u) != self.current_user]
        self.has_targets = bool(available)
        menu_values = available if available else ["No Other Accounts Available"]

        self.user_menu = ctk.CTkOptionMenu(inner, values=menu_values, width=320, height=36)
        self.user_menu.pack(pady=(0, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(0, 16))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Switch Account", width=320, height=38, font=("Segoe UI", 12, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="#ffffff", command=self._submit,
        ).pack()

        ctk.CTkButton(
            inner, text="Forgot Password?", width=320, height=32, font=("Segoe UI", 11),
            fg_color="transparent", hover_color=CARD_BORDER, text_color=MUTED,
            command=self._open_recovery,
        ).pack(pady=(8, 0))

    def _open_recovery(self):
        self.withdraw()
        modal = PasswordRecoveryModal(self.users, master=self.master)
        result = modal.get_username()
        if result:
            self._username_result = result
            self.destroy()
        else:
            self.deiconify()

    def _submit(self):
        if not self.has_targets:
            CTkMessagebox(title="No Other Accounts", message="There are no other user accounts registered.", icon="info", master=self)
            return

        selected = self.user_menu.get()
        password = self.pass_entry.get()

        if not selected or selected == "No Other Accounts Available":
            CTkMessagebox(title="Error", message="Please select a valid user account.", icon="cancel", master=self)
            return
        if not password:
            CTkMessagebox(title="Error", message="Password is required to switch accounts.", icon="cancel", master=self)
            return

        username = normalize_username(selected)
        if username == self.current_user:
            CTkMessagebox(title="Error", message="You are already logged into this account.", icon="warning", master=self)
            return

        try:
            SecurityManager.authenticate(username, password)
            self._username_result = username
            self.destroy()
        except AccountLockedError as e:
            CTkMessagebox(
                title="Account Locked",
                message=f"Too many failed attempts. Account is locked for {e} more seconds.",
                icon="warning", master=self,
            )
        except AuthenticationError:
            CTkMessagebox(title="Access Denied", message="Invalid password for this account.", icon="cancel", master=self)

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class CTkInputModal(BaseModal):

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

        self.entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show=self.show or "")
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


class CTkMultiInputModal(BaseModal):

    def __init__(self, title, fields, master=None):
        height = 140 + len(fields) * 65
        super().__init__(master, title=title, width=400, height=height)
        self.fields = fields
        self.entries = []
        self._results = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=16)

        for f in self.fields:
            ctk.CTkLabel(inner, text=f["label"], font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w", pady=(4, 0))
            entry = ctk.CTkEntry(inner, width=350, height=34, font=("Segoe UI", 12), placeholder_text=f.get("placeholder", ""))
            entry.pack(pady=(2, 4))
            self.entries.append(entry)

        if self.entries:
            self.entries[0].focus_set()
            self.entries[-1].bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Confirm", width=350, height=36,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self._submit,
        ).pack(pady=(12, 0))

    def _submit(self):
        self._results = [e.get().strip() for e in self.entries]
        self.destroy()

    def get_values(self):
        self.wait_window(self)
        return self._results


class CTkDropdownDialog(BaseModal):

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
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
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
            CTkMessagebox(title="Input Error", message="Please enter an expense amount.", icon="cancel", master=self)
            return

        try:
            amount = float(raw_amount)
            if amount <= 0:
                CTkMessagebox(title="Invalid Amount", message="Amount must be greater than zero.", icon="cancel", master=self)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Amount", message="Please enter a valid numeric amount.", icon="cancel", master=self)
            return

        target_date = raw_date or datetime.now().strftime("%Y-%m-%d")
        try:
            parsed = datetime.strptime(target_date, "%Y-%m-%d").date()
            if parsed > date.today():
                CTkMessagebox(title="Invalid Date", message="Transaction date cannot be in the future.", icon="warning", master=self)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Date", message="Date must be in YYYY-MM-DD format (e.g. 2026-08-14).", icon="warning", master=self)
            return

        self._expense_data = {
            "category": category,
            "amount": amount,
            "note": note,
            "date": target_date,
        }
        self.destroy()

    def get_expense_data(self):
        self.wait_window(self)
        return self._expense_data


class AddIncomeModal(BaseModal):

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
            CTkMessagebox(title="Input Error", message="Please enter an income amount.", icon="cancel", master=self)
            return

        try:
            amount = float(raw_amount)
            if amount <= 0:
                CTkMessagebox(title="Invalid Amount", message="Amount must be greater than zero.", icon="cancel", master=self)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Amount", message="Please enter a valid numeric amount.", icon="cancel", master=self)
            return

        target_date = raw_date or datetime.now().strftime("%Y-%m-%d")
        try:
            parsed = datetime.strptime(target_date, "%Y-%m-%d").date()
            if parsed > date.today():
                CTkMessagebox(title="Invalid Date", message="Transaction date cannot be in the future.", icon="warning", master=self)
                return
        except ValueError:
            CTkMessagebox(title="Invalid Date", message="Date must be in YYYY-MM-DD format (e.g. 2026-08-14).", icon="warning", master=self)
            return

        self._income_data = {
            "source": source,
            "amount": amount,
            "note": note,
            "date": target_date,
        }
        self.destroy()

    def get_income_data(self):
        self.wait_window(self)
        return self._income_data


class RecurringTemplatesModal(ctk.CTkToplevel):

    def __init__(self, user, master=None):
        super().__init__(master)
        self.user = user
        self.master = master
        self.title("Recurring Transaction Templates")
        self.geometry("740x520")
        self.minsize(680, 460)
        self.configure(fg_color=APP_BG)
        self.transient(master)
        self.focus_set()
        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="🔁 Recurring Templates", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(side="left")

        self.type_toggle = ctk.CTkSegmentedButton(
            top_frame, values=["Expense Templates", "Income Templates"],
            command=lambda val: self._refresh_list(),
        )
        self.type_toggle.pack(side="right")
        self.type_toggle.set("Expense Templates")

        header = ctk.CTkFrame(self, height=36, fg_color=PRIMARY)
        header.pack(fill="x", padx=20, pady=(5, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Template Name", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=140).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Category / Source", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=120).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Amount", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Note", font=("Segoe UI", 11, "bold"), text_color="#ffffff").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(header, text="Actions", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=140).pack(side="right", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=CARD_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            bottom, text="➕ Create New Template", command=self._add_template_dialog,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, height=36, font=("Segoe UI", 12, "bold"),
        ).pack(fill="x")

        self._refresh_list()

    def _refresh_list(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        is_exp = self.type_toggle.get() == "Expense Templates"
        tpl_type = "expense" if is_exp else "income"
        tpls = self.user.get_templates(template_type=tpl_type)

        if not tpls:
            ctk.CTkLabel(
                self.scroll_frame, text=f"No recurring {tpl_type} templates created yet.",
                font=("Segoe UI", 12), text_color=MUTED,
            ).pack(pady=40)
            return

        for idx, tpl in enumerate(tpls):
            row_bg = CARD_BG if idx % 2 == 0 else ("#f8fafc", "#23163e")
            row = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            note_str = tpl.get("note") or "—"
            ctk.CTkLabel(row, text=tpl.get("name", ""), font=("Segoe UI", 11, "bold"), width=140, text_color=TITLE, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=tpl.get("target", "").capitalize(), font=("Segoe UI", 11), width=120, text_color=PRIMARY if is_exp else SUCCESS).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=format_amount(tpl.get("amount", 0.0), self.user.currency), font=("Segoe UI", 11, "bold"), width=110, text_color=BODY).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=note_str, font=("Segoe UI", 11), text_color=MUTED if note_str == "—" else BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=5)

            ctk.CTkButton(
                btn_box, text="Log Today", width=70, height=26, font=("Segoe UI", 10, "bold"),
                fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                command=lambda tid=tpl.get("id"): self._execute_template(tid),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box, text="Delete", width=55, height=26, font=("Segoe UI", 10, "bold"),
                fg_color=DANGER, hover_color=DANGER_HOVER,
                command=lambda tid=tpl.get("id"): self._delete_template(tid),
            ).pack(side="left", padx=2)

    def _execute_template(self, template_id):
        try:
            self.user.execute_template(template_id)
            CTkMessagebox(title="Logged", message="Transaction logged for today from template.", icon="check", master=self)
        except Exception as exc:
            CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=self)

    def _delete_template(self, template_id):
        msg = CTkMessagebox(
            title="Confirm Delete", message="Delete this recurring template?",
            icon="warning", option_1="Yes", option_2="No", master=self,
        )
        if msg.get() == "Yes":
            self.user.delete_template(template_id)
            self._refresh_list()

    def _add_template_dialog(self):
        is_exp = self.type_toggle.get() == "Expense Templates"
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"New {'Expense' if is_exp else 'Income'} Template")
        dialog.geometry("400x380")
        dialog.transient(self)
        dialog.grab_set()

        inner = ctk.CTkFrame(dialog, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Template Name (e.g. Monthly Rent):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        name_entry = ctk.CTkEntry(inner, width=360, height=32)
        name_entry.pack(pady=(2, 8))

        ctk.CTkLabel(inner, text="Category:" if is_exp else "Source:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        options = [c.capitalize() for c in self.user.categories] if is_exp else ["Salary", "Freelance", "Investment", "Business", "Gift", "Other"]
        target_menu = ctk.CTkOptionMenu(inner, values=options, width=360, height=32)
        target_menu.pack(pady=(2, 8))
        if options:
            target_menu.set(options[0])

        ctk.CTkLabel(inner, text=f"Amount ({self.user.currency}):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        amount_entry = ctk.CTkEntry(inner, width=360, height=32)
        amount_entry.pack(pady=(2, 8))

        ctk.CTkLabel(inner, text="Note (Optional):", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        note_entry = ctk.CTkEntry(inner, width=360, height=32)
        note_entry.pack(pady=(2, 14))

        def save():
            name = name_entry.get().strip()
            raw_amt = amount_entry.get().strip().replace(",", "")
            target = target_menu.get().strip()
            note = note_entry.get().strip()

            if not name or not raw_amt:
                CTkMessagebox(title="Error", message="Name and amount are required.", icon="cancel", master=dialog)
                return
            try:
                self.user.add_template("expense" if is_exp else "income", name, target, raw_amt, note)
                dialog.destroy()
                self._refresh_list()
            except Exception as exc:
                CTkMessagebox(title="Error", message=str(exc), icon="cancel", master=dialog)

        ctk.CTkButton(
            inner, text="Save Template", command=save,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, height=36, font=("Segoe UI", 12, "bold"),
        ).pack(fill="x")


class TransactionHistoryModal(ctk.CTkToplevel):

    def __init__(self, user, initial_category=None, month=None, master=None):
        super().__init__(master)
        self.user = user
        self.master = master
        self.initial_category = initial_category.capitalize() if initial_category else None
        self.month = month
        period_suffix = f" - {month}" if month else ""
        self.title(f"Transaction History Ledger{period_suffix}")
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
        if self.initial_category and self.initial_category in filter_cats:
            self.filter_menu.set(self.initial_category)

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
            for w in self.scroll_frame.winfo_children():
                w.destroy()

            selected_cat = self.filter_menu.get()
            query = self.search_entry.get().lower().strip()

            txs = self.user.get_transactions(month=self.month)
            if selected_cat != "All Categories":
                txs = [tx for tx in txs if tx.get("category", "").lower() == selected_cat.lower()]
            if query:
                txs = [
                    tx for tx in txs
                    if query in tx.get("note", "").lower() or query in tx.get("category", "").lower()
                ]

            if not txs:
                ctk.CTkLabel(
                    self.scroll_frame, text="No matching transactions found.",
                    font=("Segoe UI", 12), text_color=MUTED,
                ).pack(pady=40)
                return

            for idx, tx in enumerate(txs):
                row_bg = CARD_BG if idx % 2 == 0 else ("#f8fafc", "#23163e")
                row = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, height=38)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                note_str = tx.get("note") or "—"
                ctk.CTkLabel(row, text=tx.get("date", ""), font=("Segoe UI", 11), width=95, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=tx.get("category", "").capitalize(), font=("Segoe UI", 11, "bold"), width=110, text_color=PRIMARY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=format_amount(tx.get("amount", 0.0), self.user.currency), font=("Segoe UI", 11, "bold"), width=110, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note_str, font=("Segoe UI", 11), text_color=MUTED if note_str == "—" else BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                ctk.CTkButton(
                    row, text="Delete", width=60, height=24, font=("Segoe UI", 10, "bold"),
                    fg_color=DANGER, hover_color=DANGER_HOVER,
                    command=lambda tid=tx.get("id"): self._delete_tx(tid),
                ).pack(side="right", padx=5)
        except Exception:
            pass

    def _delete_tx(self, tx_id):
        msg = CTkMessagebox(
            title="Confirm Delete", message="Permanently delete this transaction?",
            icon="warning", option_1="Yes", option_2="No", master=self,
        )
        if msg.get() == "Yes":
            self.user.delete_transaction(tx_id)
            self._refresh_list()


class IncomeHistoryModal(ctk.CTkToplevel):

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
            for w in self.scroll_frame.winfo_children():
                w.destroy()

            query = self.search_entry.get().lower().strip()
            incomes = self.user.get_incomes()

            if query:
                incomes = [
                    inc for inc in incomes
                    if query in inc.get("note", "").lower() or query in inc.get("source", "").lower()
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

                note_str = inc.get("note") or "—"
                ctk.CTkLabel(row, text=inc.get("date", ""), font=("Segoe UI", 11), width=95, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=inc.get("source", "Income"), font=("Segoe UI", 11, "bold"), width=120, text_color=SUCCESS).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=format_amount(inc.get("amount", 0.0), self.user.currency), font=("Segoe UI", 11, "bold"), width=110, text_color=BODY).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note_str, font=("Segoe UI", 11), text_color=MUTED if note_str == "—" else BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                ctk.CTkButton(
                    row, text="Delete", width=60, height=24, font=("Segoe UI", 10, "bold"),
                    fg_color=DANGER, hover_color=DANGER_HOVER,
                    command=lambda iid=inc.get("id"): self._delete_inc(iid),
                ).pack(side="right", padx=5)
        except Exception:
            pass

    def _delete_inc(self, inc_id):
        msg = CTkMessagebox(
            title="Confirm Delete", message="Permanently delete this income record?",
            icon="warning", option_1="Yes", option_2="No", master=self,
        )
        if msg.get() == "Yes":
            self.user.delete_income(inc_id)
            self._refresh_list()


class ImportStatementModal(ctk.CTkToplevel):

    def __init__(self, user, master=None):
        super().__init__(master)
        self.user = user
        self.master = master
        self.title("Import Bank Statement (QIF / OFX)")
        self.geometry("780x540")
        self.minsize(680, 440)
        self.configure(fg_color=APP_BG)
        self.transient(master)
        self.focus_set()
        self.parsed_txs = []
        self.cat_pickers = []
        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="📥 Import Bank Statement", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(side="left")

        ctk.CTkButton(
            top_frame, text="📂 Choose QIF / OFX File", command=self._choose_file,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, height=32, font=("Segoe UI", 11, "bold"),
        ).pack(side="right")

        self.file_lbl = ctk.CTkLabel(self, text="No file selected yet.", font=("Segoe UI", 11), text_color=MUTED)
        self.file_lbl.pack(anchor="w", padx=20, pady=(0, 6))

        header = ctk.CTkFrame(self, height=36, fg_color=PRIMARY)
        header.pack(fill="x", padx=20, pady=(0, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Date", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=95).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Type", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Amount", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=100).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Payee / Description", font=("Segoe UI", 11, "bold"), text_color="#ffffff").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(header, text="Assigned Category", font=("Segoe UI", 11, "bold"), text_color="#ffffff", width=130).pack(side="right", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=CARD_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(4, 10))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 15))

        self.import_btn = ctk.CTkButton(
            bottom, text="Confirm & Import to Ledger", command=self._import_all,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, text_color="#ffffff",
            height=44, width=320, font=("Segoe UI", 13, "bold"), corner_radius=10,
        )
        self.import_btn.pack(anchor="center")

        self._refresh_list()

    def _choose_file(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Select Bank Statement",
            filetypes=[("Bank Statements (*.qif, *.ofx, *.qfx)", "*.qif *.ofx *.qfx"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        from .expense_tracker import StatementParser
        try:
            raw_txs = StatementParser.parse_file(filepath)
            if not raw_txs:
                CTkMessagebox(title="No Records", message="No valid transactions could be found in the selected file.", icon="info", master=self)
                return
            self.parsed_txs = raw_txs
            self.file_lbl.configure(text=f"Loaded {len(raw_txs)} transactions from: {os.path.basename(filepath)}", text_color=SUCCESS)
            self._refresh_list()
        except Exception as exc:
            CTkMessagebox(title="Parse Error", message=f"Failed to read statement: {exc}", icon="cancel", master=self)

    def _refresh_list(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not self.parsed_txs:
            ctk.CTkLabel(
                self.scroll_frame, text="Select a .qif or .ofx statement file to preview entries.",
                font=("Segoe UI", 12), text_color=MUTED,
            ).pack(pady=40)
            return

        cat_options = [c.capitalize() for c in self.user.categories]
        self.cat_pickers = []

        for idx, trn in enumerate(self.parsed_txs):
            row_bg = CARD_BG if idx % 2 == 0 else ("#f8fafc", "#23163e")
            row = ctk.CTkFrame(self.scroll_frame, fg_color=row_bg, height=38)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            amt = trn.get("amount", 0.0)
            is_income = amt > 0
            
            ctk.CTkLabel(row, text=trn.get("date", ""), font=("Segoe UI", 11), width=95, text_color=BODY).pack(side="left", padx=5)
            type_text = "💰 Income" if is_income else "💳 Expense"
            type_color = SUCCESS if is_income else WARNING
            ctk.CTkLabel(row, text=type_text, font=("Segoe UI", 10, "bold"), width=80, text_color=type_color).pack(side="left", padx=5)
            amt_color = SUCCESS if is_income else WARNING
            ctk.CTkLabel(row, text=format_amount(abs(trn.get("amount", 0.0)), self.user.currency), font=("Segoe UI", 11, "bold"), width=100, text_color=amt_color).pack(side="left", padx=5)
            payee_text = trn.get("payee") or trn.get("memo") or "—"
            ctk.CTkLabel(row, text=payee_text, font=("Segoe UI", 11), text_color=BODY, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

            if not is_income:
                payee_text_lower = (trn.get("payee") or "").strip().lower()
                remembered = self.user.get_payee_category(payee_text_lower) if payee_text_lower else None
                if remembered and remembered.capitalize() in cat_options:
                    matched_cat = remembered.capitalize()
                else:
                    memo_lower = (trn.get("memo") or "").lower()
                    matched_cat = "Miscellaneous"
                    for c in self.user.categories:
                        if c in memo_lower or c in payee_text_lower:
                            matched_cat = c.capitalize()
                            break
                menu = ctk.CTkOptionMenu(row, values=cat_options, width=130, height=28)
                menu.set(matched_cat if matched_cat in cat_options else cat_options[0])
                menu.pack(side="right", padx=10)
                self.cat_pickers.append((idx, menu, False))
            else:
                src_menu = ctk.CTkOptionMenu(row, values=["Salary", "Freelance", "Investment", "Business", "Gift", "Other"], width=130, height=28)
                src_menu.set("Salary")
                src_menu.pack(side="right", padx=10)
                self.cat_pickers.append((idx, src_menu, True))

    def _import_all(self):
        if not self.parsed_txs:
            CTkMessagebox(title="No File", message="Please choose a QIF or OFX bank statement file first.", icon="info", master=self)
            return
        imported_exp = 0
        imported_inc = 0
        for idx, widget, is_income in self.cat_pickers:
            trn = self.parsed_txs[idx]
            amt = abs(trn.get("amount", 0.0))
            date_str = trn.get("date") or date.today().strftime("%Y-%m-%d")
            note = (trn.get("payee") or trn.get("memo") or "")[:200]
            chosen = widget.get()

            if is_income:
                self.user.add_income(chosen, amt, note=note, date_val=date_str)
                imported_inc += 1
            else:
                chosen_lower = chosen.lower().strip()
                self.user.add_transaction(chosen_lower, amt, note=note, date_val=date_str)
                payee_key = (trn.get("payee") or "").strip().lower()
                if payee_key:
                    self.user.learn_payee_category(payee_key, chosen_lower)
                imported_exp += 1

        self.user.save()
        parent = self.master
        self.destroy()
        if parent:
            CTkMessagebox(
                title="Import Complete",
                message=f"Successfully imported {imported_exp} expenses and {imported_inc} incomes into your ledger.",
                icon="check", master=parent,
            )

            
class PasswordRecoveryModal(BaseModal):

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Password Recovery", width=460, height=540)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG, border_width=2, border_color=CARD_BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.94)

        ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=PRIMARY).pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=14)

        ctk.CTkLabel(inner, text="🔑 Reset Password", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(pady=(0, 2))
        ctk.CTkLabel(inner, text="Answer your security question to recover account access.", font=("Segoe UI", 10), text_color=MUTED).pack(pady=(0, 10))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        user_row = ctk.CTkFrame(inner, fg_color="transparent")
        user_row.pack(fill="x", pady=(2, 6))

        self.user_entry = ctk.CTkEntry(user_row, height=34, font=("Segoe UI", 12))
        self.user_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.user_entry.bind("<Return>", lambda e: self._lookup())
        self.user_entry.bind("<FocusOut>", lambda e: self._lookup(silent=True))

        ctk.CTkButton(
            user_row, text="Find Account", width=105, height=34, font=("Segoe UI", 11, "bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="#ffffff", command=self._lookup,
        ).pack(side="right")

        self.q_box = ctk.CTkFrame(inner, fg_color=APP_BG, corner_radius=8, border_width=1, border_color=CARD_BORDER)
        self.q_box.pack(fill="x", pady=(4, 8), ipady=4)
        self.question_lbl = ctk.CTkLabel(
            self.q_box, text="Enter username and click 'Find Account' to view your question.",
            font=("Segoe UI", 10, "italic"), text_color=MUTED, wraplength=350, justify="left",
        )
        self.question_lbl.pack(padx=10, pady=4, anchor="w")

        ctk.CTkLabel(inner, text="Security Answer:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.answer_entry = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), placeholder_text="Enter secret answer")
        self.answer_entry.pack(pady=(2, 6))

        ctk.CTkLabel(inner, text="New Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.new_pass = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), show="*")
        self.new_pass.pack(pady=(2, 6))

        ctk.CTkLabel(inner, text="Confirm New Password:", font=("Segoe UI", 11, "bold"), text_color=BODY).pack(anchor="w")
        self.confirm_pass = ctk.CTkEntry(inner, width=360, height=34, font=("Segoe UI", 12), show="*")
        self.confirm_pass.pack(pady=(2, 12))
        self.confirm_pass.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner, text="Reset Password & Sign In", width=360, height=38, font=("Segoe UI", 12, "bold"),
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER, text_color="#ffffff", command=self._submit,
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            inner, text="Back to Sign In", width=360, height=28, font=("Segoe UI", 11),
            fg_color="transparent", hover_color=APP_BG, text_color=MUTED, command=self.destroy,
        ).pack()

    def _lookup(self, silent=False):
        username = normalize_username(self.user_entry.get())
        if not username:
            if not silent:
                CTkMessagebox(title="Error", message="Please enter a username.", icon="cancel", master=self)
            return
        try:
            q = SecurityManager.get_security_question(username)
            self.question_lbl.configure(text=f"Question: {q}", text_color=TITLE, font=("Segoe UI", 10, "bold"))
            self.answer_entry.focus_set()
        except AuthenticationError as e:
            self.question_lbl.configure(text=f"Error: {e}", text_color=DANGER, font=("Segoe UI", 10))
            if not silent:
                CTkMessagebox(title="Error", message=str(e), icon="cancel", master=self)

    def _submit(self):
        username = normalize_username(self.user_entry.get())
        answer = self.answer_entry.get().strip()
        new_pass = self.new_pass.get()
        confirm = self.confirm_pass.get()

        if not username:
            CTkMessagebox(title="Error", message="Please enter your username.", icon="cancel", master=self)
            return
        if not answer or not new_pass or not confirm:
            CTkMessagebox(title="Error", message="All fields (answer, new password, confirmation) are required.", icon="cancel", master=self)
            return

        try:
            SecurityManager.recover_password(username, answer, new_pass, confirm)
            self._username_result = username
            parent = self.master
            self.destroy()
            if parent:
                CTkMessagebox(title="Success", message="Password reset successfully. You are now logged in.", icon="check", master=parent)
        except AccountLockedError as e:
            CTkMessagebox(title="Account Locked", message=f"Too many failed attempts. Account is locked for {e} more seconds.", icon="warning", master=self)
        except (AuthenticationError, PasswordValidationError) as e:
            CTkMessagebox(title="Recovery Error", message=str(e), icon="cancel", master=self)

    def get_username(self):
        self.wait_window(self)
        return self._username_result


class SavingsGoalsModal(ctk.CTkToplevel):

    def __init__(self, user, master=None):
        super().__init__(master)
        self.user = user
        self.title("🎯 Savings Goals")
        self.geometry("680x560")
        self.configure(fg_color=APP_BG)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 6))
        ctk.CTkLabel(header, text="🎯 Savings Goals", font=("Segoe UI", 18, "bold"), text_color=TITLE).pack(side="left")
        ctk.CTkButton(header, text="+ New Goal", height=32, font=("Segoe UI", 11, "bold"),
                      fg_color=SUCCESS, hover_color=SUCCESS_HOVER, text_color="#ffffff",
                      command=self._add_goal_dialog).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CARD_BG)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self._refresh()

    def _refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        goals = self.user.get_savings_goals()
        if not goals:
            ctk.CTkLabel(self.scroll, text="No savings goals yet. Add one to get started.",
                         font=("Segoe UI", 12), text_color=MUTED).pack(pady=40)
            return

        for goal in goals:
            self._render_goal_row(goal)

    def _render_goal_row(self, goal):
        card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=5, padx=4, ipady=6)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(6, 2))

        ctk.CTkLabel(top, text=goal["name"], font=("Segoe UI", 13, "bold"), text_color=TITLE).pack(side="left")
        pct = round(min((goal["current"] / goal["target"]) * 100, 100), 1) if goal["target"] > 0 else 0.0
        color = SUCCESS if pct >= 100 else (WARNING if pct >= 60 else BODY)
        ctk.CTkLabel(top, text=f"{pct:.1f}%  ({format_amount(goal['current'], self.user.currency)} / {format_amount(goal['target'], self.user.currency)})",
                     font=("Segoe UI", 11), text_color=color).pack(side="right")

        ctk.CTkProgressBar(card, progress_color=SUCCESS if pct >= 100 else PRIMARY,
                           height=10, corner_radius=5).pack(fill="x", padx=14, pady=(2, 6))
        # set progress after packing to avoid widget not existing error
        bar = card.winfo_children()[-1]
        bar.set(pct / 100)

        if goal.get("target_date"):
            ctk.CTkLabel(card, text=f"Target date: {goal['target_date']}", font=("Segoe UI", 10), text_color=MUTED).pack(anchor="w", padx=14)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(4, 0))
        gid = goal["id"]

        ctk.CTkButton(actions, text="Deposit", width=85, height=28, font=("Segoe UI", 10, "bold"),
                      fg_color=SUCCESS, hover_color=SUCCESS_HOVER, text_color="#ffffff",
                      command=lambda g=gid: self._deposit_dialog(g)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(actions, text="Withdraw", width=85, height=28, font=("Segoe UI", 10, "bold"),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      command=lambda g=gid: self._withdraw_dialog(g)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(actions, text="Edit", width=70, height=28, font=("Segoe UI", 10, "bold"),
                      fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="#ffffff",
                      command=lambda g=goal: self._edit_goal_dialog(g)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(actions, text="Delete", width=70, height=28, font=("Segoe UI", 10, "bold"),
                      fg_color=DANGER, hover_color=DANGER_HOVER, text_color="#ffffff",
                      command=lambda g=gid: self._delete_goal(g)).pack(side="right")

    def _add_goal_dialog(self):
        dlg = CTkMultiInputModal("New Savings Goal", fields=[
            {"label": "Goal Name", "placeholder": "e.g. Vacation Fund"},
            {"label": "Target Amount", "placeholder": "e.g. 2000"},
            {"label": "Initial Amount (optional)", "placeholder": "0"},
            {"label": "Target Date (YYYY-MM-DD, optional)", "placeholder": "Leave blank"},
        ], master=self)
        result = dlg.get_values()
        if not result:
            return
        name, target, current, tdate = result
        try:
            self.user.add_savings_goal(name, target, current_amount=current or 0, target_date=tdate or None)
            self._refresh()
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel", master=self)

    def _edit_goal_dialog(self, goal):
        dlg = CTkMultiInputModal(f"Edit Goal: {goal['name']}", fields=[
            {"label": "Goal Name", "placeholder": goal["name"]},
            {"label": "Target Amount", "placeholder": str(goal["target"])},
            {"label": "Target Date (YYYY-MM-DD, optional)", "placeholder": goal.get("target_date", "")},
        ], master=self)
        result = dlg.get_values()
        if not result:
            return
        name, target, tdate = result
        try:
            self.user.update_savings_goal(
                goal["id"],
                name=name or goal["name"],
                target_amount=target or goal["target"],
                target_date=tdate,
            )
            self._refresh()
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel", master=self)

    def _deposit_dialog(self, goal_id):
        dlg = CTkInputModal(title="Deposit to Goal", text="Enter amount to add to savings goal:", master=self)
        amt = dlg.get_input()
        if not amt:
            return
        try:
            goal = self.user.deposit_savings_goal(goal_id, amt)
            self._refresh()
            if goal["current"] >= goal["target"]:
                CTkMessagebox(title="Goal Reached!", message="Congratulations! You have reached your savings target for this goal! 🎉", icon="check", master=self)
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel", master=self)

    def _withdraw_dialog(self, goal_id):
        goal = next((g for g in self.user.savings_goals if g["id"] == goal_id), None)
        if goal and goal["current"] <= 0:
            CTkMessagebox(title="No Funds", message="This savings goal has 0.00 saved funds.", icon="info", master=self)
            return
        dlg = CTkInputModal(title="Withdraw from Goal", text="Enter amount to withdraw from savings goal:", master=self)
        amt = dlg.get_input()
        if not amt:
            return
        try:
            self.user.withdraw_savings_goal(goal_id, amt)
            self._refresh()
        except Exception as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel", master=self)

    def _delete_goal(self, goal_id):
        self.user.delete_savings_goal(goal_id)
        self._refresh()