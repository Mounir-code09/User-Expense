"""Main application window, startup flow, and live dashboard metrics."""
import customtkinter as ctk

from .currency_service import currency_service
from .data_manager import set_database_file
from .expense_tracker import ExpenseTracker
from .modals import SignInModal, SignUpModal
from .theme import (
    ACCENT_BAR, APP_BG, BODY, CARD_BG, CARD_BORDER, DANGER, DANGER_HOVER,
    HIGHLIGHT, MUTED, NEUTRAL, NEUTRAL_HOVER, OFFLINE, ONLINE, PRIMARY,
    PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER, TITLE,
)
from .ui_actions import UIActions
from .user import User, Users

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ExpenseApp(ctk.CTk):
    """Root window controlling authentication flow, user sessions, and dashboard."""

    def __init__(self, data_file):
        super().__init__()
        set_database_file(data_file)

        self.title("Expenses Tracker Dashboard")
        self.geometry("900x680")
        self.minsize(820, 620)
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

    def on_close(self):
        """Save active session and cancel background timers before exit."""
        if self.user:
            self.user.save()
        try:
            if self.network_job is not None:
                self.after_cancel(self.network_job)
        except Exception:
            pass
        self.destroy()

    def _build_startup_ui(self):
        """Render welcome screen with Sign In and Sign Up options."""
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
            text="Track spending, manage category budgets, and analyze finances.",
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

    def _load_user_workspace(self, username):
        """Transition from welcome screen to the main dashboard."""
        if hasattr(self, "startup_frame") and self.startup_frame.winfo_exists():
            self.startup_frame.destroy()

        self.user = User(username)
        self.tracker = ExpenseTracker(self.user)
        self.actions = UIActions(self.user, self.tracker, self.users, self)

        currency_service.fetch_rates_async()
        self._build_dashboard_ui()
        self._start_network_monitoring()

    def switch_user_workflow(self, username=None):
        """Log out or switch to another user profile."""
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

    def _build_dashboard_ui(self):
        """Construct the dashboard with live summary cards and action buttons."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(16, 6), fill="x", padx=30)

        ctk.CTkLabel(
            header,
            text=f"Welcome, {self.user.name}!",
            font=("Segoe UI", 22, "bold"),
            text_color=TITLE,
        ).pack(side="left")

        self.network_lbl = ctk.CTkLabel(
            header, text="Checking network…", font=("Segoe UI", 11, "bold"), text_color=MUTED
        )
        self.network_lbl.pack(side="left", padx=(14, 0))

        currency_frame = ctk.CTkFrame(header, fg_color="transparent")
        currency_frame.pack(side="right")

        ctk.CTkLabel(
            currency_frame,
            text="Currency:",
            font=("Segoe UI", 11, "bold"),
            text_color=BODY,
        ).pack(side="left", padx=(0, 8))

        self.currency_selector = ctk.CTkOptionMenu(
            currency_frame,
            values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"],
            width=90,
            height=30,
            fg_color=PRIMARY,
            button_color=PRIMARY_HOVER,
            command=lambda val: self.actions.change_account_currency(val, self.currency_selector),
        )
        self.currency_selector.pack(side="right")
        self.currency_selector.set(self.user.currency)

        # 3 Live Summary Metric Cards
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=30, pady=(6, 12))
        self.cards_frame.columnconfigure((0, 1, 2), weight=1)

        # Card 1: Total Spent
        c1 = ctk.CTkFrame(self.cards_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        c1.grid(row=0, column=0, padx=6, sticky="nsew", ipady=8)
        ctk.CTkLabel(c1, text="💳 Total Spending", font=("Segoe UI", 11, "bold"), text_color=MUTED).pack(pady=(6, 2))
        self.spent_lbl = ctk.CTkLabel(c1, text="0.00", font=("Segoe UI", 18, "bold"), text_color=TITLE)
        self.spent_lbl.pack(pady=(0, 6))

        # Card 2: Remaining Budget
        c2 = ctk.CTkFrame(self.cards_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        c2.grid(row=0, column=1, padx=6, sticky="nsew", ipady=8)
        ctk.CTkLabel(c2, text="🎯 Remaining Budget", font=("Segoe UI", 11, "bold"), text_color=MUTED).pack(pady=(6, 2))
        self.rem_lbl = ctk.CTkLabel(c2, text="0.00", font=("Segoe UI", 18, "bold"), text_color=SUCCESS)
        self.rem_lbl.pack(pady=(0, 6))

        # Card 3: Top Category
        c3 = ctk.CTkFrame(self.cards_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        c3.grid(row=0, column=2, padx=6, sticky="nsew", ipady=8)
        ctk.CTkLabel(c3, text="🏆 Top Spending Category", font=("Segoe UI", 11, "bold"), text_color=MUTED).pack(pady=(6, 2))
        self.top_lbl = ctk.CTkLabel(c3, text="None", font=("Segoe UI", 18, "bold"), text_color=HIGHLIGHT)
        self.top_lbl.pack(pady=(0, 6))

        self.refresh_summary_cards()

        # Action Grid
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=30, pady=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        btn_style = {
            "width": 260,
            "height": 40,
            "font": ("Segoe UI", 12, "bold"),
            "corner_radius": 10,
            "fg_color": PRIMARY,
            "hover_color": PRIMARY_HOVER,
        }

        buttons_left = [
            ("➕ 1. Add Expense", self.actions.add_expense),
            ("🎯 2. Set Category Budget", self.actions.set_budget),
            ("📜 3. Transaction History", self.actions.show_transactions),
            ("🔄 4. Reset Category", self.actions.reset_category),
        ]
        buttons_right = [
            ("📊 5. Visual Analytics (3-in-1)", self.actions.show_chart),
            ("📋 6. Financial Status Table", self.actions.show_status),
            ("🏷️ 7. Add Custom Category", self.actions.add_custom_category),
            ("📥 8. Export to CSV", self.actions.export_to_csv),
        ]

        for idx, (label, command) in enumerate(buttons_left):
            ctk.CTkButton(grid, text=label, command=command, **btn_style).grid(
                row=idx, column=0, padx=10, pady=6, sticky="ew"
            )
        for idx, (label, command) in enumerate(buttons_right):
            ctk.CTkButton(grid, text=label, command=command, **btn_style).grid(
                row=idx, column=1, padx=10, pady=6, sticky="ew"
            )

        # Bottom navigation
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=30, pady=(12, 20))

        ctk.CTkButton(
            bottom,
            text="Switch Account",
            command=self.actions.switch_user_profile,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            font=("Segoe UI", 12, "bold"),
            height=38,
            corner_radius=10,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            bottom,
            text="Log Out",
            command=self.switch_user_workflow,
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
            font=("Segoe UI", 12, "bold"),
            height=38,
            corner_radius=10,
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))

        ctk.CTkButton(
            bottom,
            text="Exit Application",
            command=self.actions.exit_app,
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            font=("Segoe UI", 12, "bold"),
            height=38,
            corner_radius=10,
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def refresh_summary_cards(self):
        """Update live values and colors on the top metric summary cards."""
        if not self.user or not hasattr(self, "spent_lbl"):
            return

        total_spent = self.user.total_expenses_of_user()
        rem_budget = self.user.get_remaining_budget()
        top_cat, top_amt = self.user.get_top_category()

        self.spent_lbl.configure(text=f"{total_spent:.2f} {self.user.currency}")

        if sum(self.user.budget_limits.values()) == 0:
            self.rem_lbl.configure(text="No limits set", text_color=MUTED)
        elif rem_budget >= 0:
            self.rem_lbl.configure(text=f"+{rem_budget:.2f} {self.user.currency}", text_color=SUCCESS)
        else:
            self.rem_lbl.configure(text=f"{rem_budget:.2f} {self.user.currency}", text_color=DANGER)

        if top_cat != "None":
            self.top_lbl.configure(text=f"{top_cat} ({top_amt:.2f})")
        else:
            self.top_lbl.configure(text="None")

    def _start_network_monitoring(self):
        """Refresh exchange rates and update connectivity status periodically."""
        if not self.winfo_exists():
            return

        if currency_service.is_offline:
            self.network_lbl.configure(text="🔴 Offline (fallback rates)", text_color=OFFLINE)
        else:
            self.network_lbl.configure(text="🟢 Online (live rates)", text_color=ONLINE)

        currency_service.fetch_rates_async()
        self.network_job = self.after(10_000, self._start_network_monitoring)


def start_app(data_file):
    """Launch the Expense Tracker desktop application."""
    app = ExpenseApp(data_file)
    app.mainloop()