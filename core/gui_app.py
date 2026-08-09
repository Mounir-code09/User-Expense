"""
GUI App Module
--------------
Main application window: startup authentication, dashboard layout, and background tasks.
"""
import customtkinter as ctk

from .user import User_class, Users
from .expense_tracker import ExpenseTracker
from .data_manager import set_database_file
from .currency_service import currency_service
from .modals import SignInModal, SignUpModal
from .ui_actions import UIActions
from .theme import (
    APP_BG, CARD_BG, CARD_BORDER, ACCENT_BAR, TITLE, BODY, MUTED, HIGHLIGHT,
    PRIMARY, PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, ONLINE, OFFLINE,
)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ExpenseApp(ctk.CTk):
    """Root window controlling authentication flow, user sessions, and the dashboard."""

    def __init__(self, data_file: str):
        super().__init__()
        set_database_file(data_file)

        self.title("Expenses Tracker Dashboard")
        self.geometry("860x680")
        self.minsize(780, 620)
        self.configure(fg_color=APP_BG)
        self.resizable(True, True)

        self.data_file = data_file
        self.user = None
        self.tracker = None
        self.users = Users()
        self.actions = None
        self.network_job = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_startup_ui()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_close(self):
        """Persist the active session and cancel background timers before exit."""
        if self.user:
            self.user.save()
        try:
            if self.network_job is not None:
                self.after_cancel(self.network_job)
        except Exception:
            pass
        self.destroy()

    # ------------------------------------------------------------------
    # Startup & authentication
    # ------------------------------------------------------------------

    def _build_startup_ui(self):
        """Render the welcome screen with Sign In and Sign Up options."""
        self.startup_frame = ctk.CTkFrame(self, fg_color=APP_BG, corner_radius=0)
        self.startup_frame.pack(fill="both", expand=True)

        card_frame = ctk.CTkFrame(
            self.startup_frame,
            width=440,
            height=380,
            corner_radius=20,
            fg_color=CARD_BG,
            border_width=2,
            border_color=CARD_BORDER,
        )
        card_frame.place(relx=0.5, rely=0.5, anchor="center")
        card_frame.pack_propagate(False)

        accent_banner = ctk.CTkFrame(card_frame, height=8, corner_radius=0, fg_color=ACCENT_BAR)
        accent_banner.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=28)

        ctk.CTkLabel(
            inner,
            text="💰 Expense Tracker",
            font=("Segoe UI", 26, "bold"),
            text_color=TITLE,
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            inner,
            text="Manage budgets, track spending, and convert currencies — all in one place.",
            font=("Segoe UI", 12),
            text_color=MUTED,
            wraplength=360,
        ).pack(pady=(0, 22))

        ctk.CTkLabel(
            inner,
            text="Select an option to continue:",
            font=("Segoe UI", 13, "bold"),
            text_color=BODY,
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            inner,
            text="Sign In",
            width=320,
            height=48,
            font=("Segoe UI", 14, "bold"),
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=10,
            command=self._open_signin_modal,
        ).pack(pady=(0, 14))

        ctk.CTkButton(
            inner,
            text="Create Account",
            width=320,
            height=48,
            font=("Segoe UI", 14, "bold"),
            fg_color=SUCCESS,
            hover_color=SUCCESS_HOVER,
            corner_radius=10,
            command=self._open_signup_modal,
        ).pack()

    def _open_signin_modal(self):
        modal = SignInModal(self.users, master=self)
        username = modal.get_username()
        if username:
            self._load_user_workspace(username)

    def _open_signup_modal(self):
        modal = SignUpModal(self.users, master=self)
        username = modal.get_username()
        if username:
            self._load_user_workspace(username)

    def _load_user_workspace(self, username: str):
        """Transition from the welcome screen to the main dashboard."""
        if hasattr(self, "startup_frame") and self.startup_frame.winfo_exists():
            self.startup_frame.destroy()
            
        self.user = User_class(username)
        self.tracker = ExpenseTracker(self.user)
        self.actions = UIActions(self.user, self.tracker, self.users, self)

        currency_service.fetch_rates_async()
        self._build_dashboard_ui()
        self._start_network_monitoring()

    def switch_user_workflow(self, username=None):
        """Log out or switch directly to another authenticated profile."""
        if self.user:
            self.user.save()

        if self.network_job is not None:
            try:
                self.after_cancel(self.network_job)
            except Exception:
                pass

        for widget in self.winfo_children():
            widget.destroy()

        if username:
            self._load_user_workspace(username)
        else:
            self.configure(fg_color=APP_BG)
            self._build_startup_ui()

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def _build_dashboard_ui(self):
        """Construct the main expense-management dashboard."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(18, 6), fill="x", padx=30)

        ctk.CTkLabel(
            header,
            text=f"Welcome, {self.user.name}!",
            font=("Segoe UI", 22, "bold"),
            text_color=TITLE,
        ).pack(side="left")

        self.network_lbl = ctk.CTkLabel(
            header, text="Checking network…", font=("Segoe UI", 11, "bold"), text_color=MUTED
        )
        self.network_lbl.pack(side="left", padx=(16, 0))

        currency_frame = ctk.CTkFrame(header, fg_color="transparent")
        currency_frame.pack(side="right")

        ctk.CTkLabel(
            currency_frame,
            text="Account Currency:",
            font=("Segoe UI", 11, "bold"),
            text_color=BODY,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            currency_frame,
            text="Revert to USD",
            command=lambda: self.actions.change_account_currency("USD", self.currency_selector),
            width=110,
            height=30,
            fg_color=SUCCESS,
            hover_color=SUCCESS_HOVER,
            font=("Segoe UI", 11, "bold"),
        ).pack(side="right", padx=(10, 0))

        self.currency_selector = ctk.CTkOptionMenu(
            currency_frame,
            values=["USD", "EUR", "GBP", "JPY", "CAD"],
            width=90,
            height=30,
            fg_color=PRIMARY,
            button_color=PRIMARY_HOVER,
            command=lambda val: self.actions.change_account_currency(val, self.currency_selector),
        )
        self.currency_selector.pack(side="right")
        self.currency_selector.set(self.user.currency)

        ctk.CTkLabel(
            self,
            text="Select an action below. All amounts are recorded in your account currency.",
            font=("Segoe UI", 11),
            text_color=HIGHLIGHT,
        ).pack(pady=(0, 12))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=22, pady=6)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        btn_style = {
            "width": 250,
            "height": 38,
            "font": ("Segoe UI", 12, "bold"),
            "corner_radius": 10,
            "fg_color": PRIMARY,
            "hover_color": PRIMARY_HOVER,
        }

        buttons_left = [
            ("1. Set a Budget", self.actions.set_budget),
            ("2. Check Budget", self.actions.check_budget),
            ("3. Add Expense", self.actions.add_expense),
            ("4. Remove Expense", self.actions.remove_expense),
            ("5. View Status Table", self.actions.show_status),
            ("6. Visual Breakdown", self.actions.show_chart),
        ]
        buttons_right = [
            ("7. Total Expenses", self.actions.total_expenses),
            ("8. Purge Category", self.actions.purge),
            ("9. Show Users", self.actions.show_users),
            ("10. Find User", self.actions.get_user),
            ("11. Switch Account", self.actions.switch_user_profile),
            ("12. Delete User", self.actions.delete_user),
        ]

        for idx, (label, command) in enumerate(buttons_left):
            ctk.CTkButton(grid, text=label, command=command, **btn_style).grid(
                row=idx, column=0, padx=10, pady=5, sticky="ew"
            )
        for idx, (label, command) in enumerate(buttons_right):
            ctk.CTkButton(grid, text=label, command=command, **btn_style).grid(
                row=idx, column=1, padx=10, pady=5, sticky="ew"
            )

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=30, pady=(12, 22))

        ctk.CTkButton(
            bottom,
            text="Log Out",
            command=self.switch_user_workflow,
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
            font=("Segoe UI", 12, "bold"),
            height=42,
            corner_radius=10,
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            bottom,
            text="Exit Application",
            command=self.actions.exit_app,
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            font=("Segoe UI", 12, "bold"),
            height=42,
            corner_radius=10,
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    # ------------------------------------------------------------------
    # Background network polling
    # ------------------------------------------------------------------

    def _start_network_monitoring(self):
        """Refresh exchange rates and update the connectivity indicator every 10 seconds."""
        if not self.winfo_exists():
            return

        if currency_service.is_offline:
            self.network_lbl.configure(text="🔴 Offline (fallback rates)", text_color=OFFLINE)
        else:
            self.network_lbl.configure(text="🟢 Online (live rates)", text_color=ONLINE)

        currency_service.fetch_rates_async()
        self.network_job = self.after(10_000, self._start_network_monitoring)


def start_app(data_file: str):
    """Launch the Expense Tracker desktop application."""
    app = ExpenseApp(data_file)
    app.mainloop()