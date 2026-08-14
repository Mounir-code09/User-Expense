"""CustomTkinter modal dialogs for authentication and inputs."""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from .security import SecurityManager
from .data_manager import normalize_username
from .theme import (
    APP_BG, CARD_BG, CARD_BORDER, TITLE, BODY,
    PRIMARY, PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER,
)


class BaseModal(ctk.CTkToplevel):
    """Base modal dialog window with centering."""

    def __init__(self, master, title, width=400, height=320):
        super().__init__(master)
        self.master = master
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=APP_BG)
        self.resizable(False, False)

        # Center relative to master
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
        card = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color=CARD_BG,
            border_width=2,
            border_color=CARD_BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        accent = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=PRIMARY)
        accent.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            inner, text="Welcome Back", font=("Segoe UI", 20, "bold"), text_color=TITLE
        ).pack(pady=(0, 15))

        ctk.CTkLabel(inner, text="Username:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12))
        self.user_entry.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=BODY).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=38, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(4, 20))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner,
            text="Sign In",
            width=320,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._submit,
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
                    icon="warning",
                    master=self.master,
                )
            else:
                CTkMessagebox(title="Access Denied", message="Invalid username or password.", icon="cancel", master=self.master)
            return

        self._username_result = username
        self.destroy()

    def get_username(self):
        """Wait for window to close and return logged in username."""
        self.wait_window(self)
        return self._username_result


class SignUpModal(BaseModal):
    """User registration dialog with password strength enforcement."""

    def __init__(self, users_container, master=None):
        super().__init__(master, title="Create Account", width=420, height=460)
        self.users = users_container
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color=CARD_BG,
            border_width=2,
            border_color=CARD_BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        accent = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=SUCCESS)
        accent.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            inner, text="New Account", font=("Segoe UI", 20, "bold"), text_color=TITLE
        ).pack(pady=(0, 10))

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
            inner,
            text="Register & Sign In",
            width=320,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=SUCCESS,
            hover_color=SUCCESS_HOVER,
            command=self._submit,
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
        """Wait for window to close and return registered username."""
        self.wait_window(self)
        return self._username_result


class SwitchAccountModal(BaseModal):
    """Modal for switching accounts with password check."""

    def __init__(self, users_container, current_user=None, master=None):
        super().__init__(master, title="Switch Account", width=380, height=340)
        self.users = users_container
        self.current_user = normalize_username(current_user) if current_user else None
        self._username_result = None
        self._build_ui()

    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Select Account to Switch To:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))

        all_users = self.users.show_users()
        if self.current_user:
            users_list = [u for u in all_users if normalize_username(u) != self.current_user]
        else:
            users_list = all_users

        menu_values = users_list if users_list else ["No Other Users"]
        self.user_menu = ctk.CTkOptionMenu(inner, values=menu_values, width=320, height=36)
        self.user_menu.pack(pady=(0, 12))

        ctk.CTkLabel(inner, text="Password:", font=("Segoe UI", 12, "bold"), text_color=TITLE).pack(anchor="w", pady=(0, 4))
        self.pass_entry = ctk.CTkEntry(inner, width=320, height=36, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(0, 20))
        self.pass_entry.bind("<Return>", lambda e: self._submit())

        ctk.CTkButton(
            inner,
            text="Switch Account",
            width=320,
            height=38,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._submit,
        ).pack()

    def _submit(self):
        selected = self.user_menu.get()
        password = self.pass_entry.get()

        if not selected or selected in ("No Users", "No Other Users"):
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
                    icon="warning",
                    master=self.master,
                )
            else:
                CTkMessagebox(title="Access Denied", message="Invalid password for this account.", icon="cancel", master=self.master)
            return

        self._username_result = username
        self.destroy()

    def get_username(self):
        """Wait for window to close and return switched username."""
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
            inner,
            text="Confirm",
            width=320,
            height=36,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._submit,
        ).pack()

    def _submit(self):
        self._input_result = self.entry.get()
        self.destroy()

    def get_input(self):
        """Wait for window to close and return entered string."""
        self.wait_window(self)
        return self._input_result


class CTkDropdownDialog(BaseModal):
    """Dropdown selection modal."""

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
            inner,
            text="Select",
            width=320,
            height=36,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._submit,
        ).pack()

    def _submit(self):
        self._selection_result = self.dropdown.get()
        self.destroy()

    def get_input(self):
        """Wait for window to close and return selected option."""
        self.wait_window(self)
        return self._selection_result