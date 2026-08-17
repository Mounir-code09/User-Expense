from datetime import date
import customtkinter as ctk

from .currency_service import currency_service
from .data_manager import create_timestamped_backup, set_database_file
from .expense_tracker import ExpenseTracker
from .modals import SignInModal, SignUpModal
from .theme import (
    ACCENT_BAR, APP_BG, BODY, CARD_BG, CARD_BORDER, DANGER, DANGER_HOVER,
    HIGHLIGHT, MUTED, NEUTRAL, NEUTRAL_HOVER, OFFLINE, ONLINE, PRIMARY,
    PRIMARY_HOVER, SUCCESS, SUCCESS_HOVER, TITLE, WARNING, format_amount,
    get_system_appearance_mode,
)
from .ui_actions import UIActions
from .user import User, Users

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ExpenseApp(ctk.CTk):

    def __init__(self, data_file):
        super().__init__()
        set_database_file(data_file)

        self.title("Expenses & Income Financial Dashboard")
        self.geometry("960x780")
        self.minsize(880, 700)
        self.configure(fg_color=APP_BG)
        self.resizable(True, True)

        self.data_file = data_file
        self.user = None
        self.tracker = None
        self.users = Users()
        self.actions = None
        self.network_job = None
        self._theme_job = None
        self._last_known_theme = get_system_appearance_mode()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_startup_ui()

    def on_close(self):
        if self.user:
            try:
                self.user.save()
            except Exception:
                pass
            try:
                create_timestamped_backup()
            except Exception:
                pass
        try:
            if self.network_job is not None:
                self.after_cancel(self.network_job)
        except Exception:
            pass
        try:
            if self._theme_job is not None:
                self.after_cancel(self._theme_job)
        except Exception:
            pass
        self.destroy()

    def _build_startup_ui(self):
        self.startup_frame = ctk.CTkFrame(self, fg_color=APP_BG, corner_radius=0)
        self.startup_frame.pack(fill="both", expand=True)

        card_frame = ctk.CTkFrame(
            self.startup_frame, width=440, height=380,
            corner_radius=20, fg_color=CARD_BG,
            border_width=2, border_color=CARD_BORDER,
        )
        card_frame.place(relx=0.5, rely=0.5, anchor="center")
        card_frame.pack_propagate(False)

        ctk.CTkFrame(card_frame, height=8, corner_radius=0, fg_color=ACCENT_BAR).pack(fill="x", side="top")

        inner = ctk.CTkFrame(card_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=28)

        ctk.CTkLabel(
            inner, text="💰 Financial Tracker",
            font=("Segoe UI", 26, "bold"), text_color=TITLE,
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            inner, text="Track expenses, manage category budgets, log income, and analyze cashflow.",
            font=("Segoe UI", 12), text_color=MUTED, wraplength=360,
        ).pack(pady=(0, 22))

        ctk.CTkLabel(
            inner, text="Select an option to continue:",
            font=("Segoe UI", 13, "bold"), text_color=BODY,
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            inner, text="Sign In", width=320, height=48,
            font=("Segoe UI", 14, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            corner_radius=10, command=self._open_signin_modal,
        ).pack(pady=(0, 14))

        ctk.CTkButton(
            inner, text="Create Account", width=320, height=48,
            font=("Segoe UI", 14, "bold"), fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            corner_radius=10, command=self._open_signup_modal,
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
        if hasattr(self, "startup_frame") and self.startup_frame.winfo_exists():
            self.startup_frame.destroy()

        self.user = User(username)
        self.tracker = ExpenseTracker(self.user)
        self.actions = UIActions(self.user, self.tracker, self.users, self)

        currency_service.fetch_rates_async()
        self._build_dashboard_ui()
        self._start_network_monitoring()
        self._sync_system_theme()

    def switch_user_workflow(self, username=None):
        if self.user:
            try:
                self.user.save()
            except Exception:
                pass

        if self.network_job is not None:
            try:
                self.after_cancel(self.network_job)
            except Exception:
                pass

        if self._theme_job is not None:
            try:
                self.after_cancel(self._theme_job)
            except Exception:
                pass

        for widget in self.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        if username:
            self._load_user_workspace(username)
        else:
            self.configure(fg_color=APP_BG)
            self._build_startup_ui()

    def get_selected_month(self):
        if not hasattr(self, "period_selector") or not self.period_selector.winfo_exists():
            return None
        val = self.period_selector.get()
        if not val or val == "All Time":
            return None
        if "(" in val and ")" in val:
            return val.split("(")[1].split(")")[0].strip()
        return None

    def _generate_period_options(self):
        today = date.today()
        options = ["All Time", f"This Month ({today.strftime('%Y-%m')})"]
        curr = today.replace(day=1)
        for i in range(1, 4):
            prev = (curr - date.resolution).replace(day=1)
            label = "Last Month" if i == 1 else f"{i} Months Ago"
            options.append(f"{label} ({prev.strftime('%Y-%m')})")
            curr = prev
        options.append(f"This Year ({today.year})")
        options.append(f"Last Year ({today.year - 1})")
        return options

    def _build_dashboard_ui(self):
        period_options = self._generate_period_options()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(12, 4), fill="x", padx=26)

        ctk.CTkLabel(
            header, text=f"Welcome, {self.user.name}!",
            font=("Segoe UI", 22, "bold"), text_color=TITLE,
        ).pack(side="left")

        self.network_lbl = ctk.CTkLabel(
            header, text="Checking network…", font=("Segoe UI", 11, "bold"), text_color=MUTED
        )
        self.network_lbl.pack(side="left", padx=(14, 0))

        controls_frame = ctk.CTkFrame(header, fg_color="transparent")
        controls_frame.pack(side="right")

        ctk.CTkLabel(
            controls_frame, text="Period:",
            font=("Segoe UI", 11, "bold"), text_color=BODY,
        ).pack(side="left", padx=(0, 6))

        self.period_selector = ctk.CTkOptionMenu(
            controls_frame,
            values=period_options,
            width=195, height=30, fg_color=PRIMARY, button_color=PRIMARY_HOVER,
            command=lambda val: self.refresh_summary_cards(),
        )
        self.period_selector.pack(side="left", padx=(0, 14))
        self.period_selector.set("All Time")

        ctk.CTkLabel(
            controls_frame, text="Currency:",
            font=("Segoe UI", 11, "bold"), text_color=BODY,
        ).pack(side="left", padx=(0, 6))

        self.currency_selector = ctk.CTkOptionMenu(
            controls_frame,
            values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"],
            width=85, height=30, fg_color=PRIMARY, button_color=PRIMARY_HOVER,
            command=lambda val: self.actions.change_account_currency(val, self.currency_selector),
        )
        self.currency_selector.pack(side="right")
        self.currency_selector.set(self.user.currency)

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=26, pady=(4, 6))
        self.cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        card_kw = {"fg_color": CARD_BG, "corner_radius": 12, "border_width": 1, "border_color": CARD_BORDER}

        c1 = ctk.CTkFrame(self.cards_frame, **card_kw)
        c1.grid(row=0, column=0, padx=4, sticky="nsew", ipady=4)
        ctk.CTkLabel(c1, text="💳 Total Expenses", font=("Segoe UI", 10, "bold"), text_color=MUTED).pack(pady=(4, 2))
        self.spent_lbl = ctk.CTkLabel(c1, text="0.00", font=("Segoe UI", 15, "bold"), text_color=DANGER)
        self.spent_lbl.pack(pady=(0, 4))

        c2 = ctk.CTkFrame(self.cards_frame, **card_kw)
        c2.grid(row=0, column=1, padx=4, sticky="nsew", ipady=4)
        ctk.CTkLabel(c2, text="💰 Total Income", font=("Segoe UI", 10, "bold"), text_color=MUTED).pack(pady=(4, 2))
        self.income_lbl = ctk.CTkLabel(c2, text="0.00", font=("Segoe UI", 15, "bold"), text_color=SUCCESS)
        self.income_lbl.pack(pady=(0, 4))

        c3 = ctk.CTkFrame(self.cards_frame, **card_kw)
        c3.grid(row=0, column=2, padx=4, sticky="nsew", ipady=4)
        ctk.CTkLabel(c3, text="📈 Net Savings", font=("Segoe UI", 10, "bold"), text_color=MUTED).pack(pady=(4, 2))
        self.savings_lbl = ctk.CTkLabel(c3, text="0.00", font=("Segoe UI", 15, "bold"), text_color=HIGHLIGHT)
        self.savings_lbl.pack(pady=(0, 4))

        c4 = ctk.CTkFrame(self.cards_frame, **card_kw)
        c4.grid(row=0, column=3, padx=4, sticky="nsew", ipady=4)
        ctk.CTkLabel(c4, text="🎯 Remaining Budget", font=("Segoe UI", 10, "bold"), text_color=MUTED).pack(pady=(4, 2))
        self.rem_lbl = ctk.CTkLabel(c4, text="0.00", font=("Segoe UI", 15, "bold"), text_color=TITLE)
        self.rem_lbl.pack(pady=(0, 4))

        self.progress_container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        self.progress_container.pack(fill="x", padx=26, pady=(4, 6), ipady=2)

        ctk.CTkLabel(
            self.progress_container, text="📊 Category Budget Progress",
            font=("Segoe UI", 12, "bold"), text_color=TITLE,
        ).pack(anchor="w", padx=16, pady=(4, 2))

        self.progress_scroll = ctk.CTkScrollableFrame(self.progress_container, height=85, fg_color="transparent")
        self.progress_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self.refresh_summary_cards()

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=26, pady=2)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        btn_style = {
            "height": 36, "font": ("Segoe UI", 11, "bold"),
            "corner_radius": 9, "fg_color": PRIMARY, "hover_color": PRIMARY_HOVER,
        }

        left_buttons = [
            ("➕ Add Expense", self.actions.add_expense),
            ("💰 Record Income", self.actions.add_income),
            ("🎯 Set Category Budget", self.actions.set_budget),
            ("🎯 Savings Goals", self.actions.manage_savings_goals),
            ("🔁 Recurring Templates", self.actions.manage_recurring_templates),
            ("📜 Expense History", self.actions.show_transactions),
            ("💵 Income History", self.actions.show_incomes),
        ]
        right_buttons = [
            ("📊 Visual Analytics", self.actions.show_chart),
            ("📁 Add Custom Category", self.actions.add_custom_category),
            ("📋 Financial Status Table", self.actions.show_status),
            ("🔄 Reset Category", self.actions.reset_category),
            ("📥 Export to CSV", self.actions.export_to_csv),
            ("🏦 Import Bank Statement", self.actions.import_bank_statement),
            ("⚙️ Change Password", self.actions.change_password),
        ]

        for idx, (label, cmd) in enumerate(left_buttons):
            ctk.CTkButton(grid, text=label, command=cmd, **btn_style).grid(
                row=idx, column=0, padx=5, pady=3, sticky="ew"
            )
        for idx, (label, cmd) in enumerate(right_buttons):
            ctk.CTkButton(grid, text=label, command=cmd, **btn_style).grid(
                row=idx, column=1, padx=5, pady=3, sticky="ew"
            )

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=26, pady=(8, 14))

        ctk.CTkButton(
            bottom, text="Switch Account", command=self.actions.switch_user_profile,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            font=("Segoe UI", 11, "bold"), height=36, corner_radius=9,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            bottom, text="Log Out", command=self.switch_user_workflow,
            fg_color=DANGER, hover_color=DANGER_HOVER,
            font=("Segoe UI", 11, "bold"), height=36, corner_radius=9,
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))

        ctk.CTkButton(
            bottom, text="Exit Application", command=self.actions.exit_app,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            font=("Segoe UI", 11, "bold"), height=36, corner_radius=9,
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def refresh_summary_cards(self):
        try:
            if not self.user or not self.winfo_exists():
                return
            if not hasattr(self, "spent_lbl") or not hasattr(self, "income_lbl"):
                return
            if not self.spent_lbl.winfo_exists() or not self.income_lbl.winfo_exists():
                return

            month = self.get_selected_month()
            total_spent = self.user.total_expenses(month=month)
            total_income = self.user.total_income(month=month)
            net_savings = self.user.get_net_savings(month=month)
            rem_budget = self.user.get_remaining_budget(month=month)

            self.spent_lbl.configure(text=format_amount(total_spent, self.user.currency))
            self.income_lbl.configure(text=format_amount(total_income, self.user.currency))

            if net_savings >= 0:
                self.savings_lbl.configure(text=f"+{format_amount(net_savings, self.user.currency)}", text_color=SUCCESS)
            else:
                self.savings_lbl.configure(text=f"-{format_amount(abs(net_savings), self.user.currency)}", text_color=DANGER)

            if sum(self.user.budget_limits.values()) == 0:
                self.rem_lbl.configure(text="No limits", text_color=MUTED)
            elif rem_budget >= 0:
                self.rem_lbl.configure(text=f"+{format_amount(rem_budget, self.user.currency)}", text_color=SUCCESS)
            else:
                self.rem_lbl.configure(text=f"-{format_amount(abs(rem_budget), self.user.currency)}", text_color=DANGER)

            if hasattr(self, "progress_scroll") and self.progress_scroll.winfo_exists():
                for widget in self.progress_scroll.winfo_children():
                    widget.destroy()

                progress_data = self.user.get_category_budget_progress(month=month)
                goals_data = self.user.get_savings_goals()

                if not progress_data and not goals_data:
                    ctk.CTkLabel(
                        self.progress_scroll,
                        text="No active budgets or savings goals. Click 'Set Category Budget' or 'Savings Goals' to start.",
                        font=("Segoe UI", 11), text_color=MUTED,
                    ).pack(pady=10)
                else:
                    for item in progress_data:
                        row = ctk.CTkFrame(self.progress_scroll, fg_color="transparent")
                        row.pack(fill="x", pady=2)
                        color = DANGER if item["status"] == "danger" else (WARNING if item["status"] == "warning" else SUCCESS)
                        cat_title = f"🏷️ {item['category']}: {format_amount(item['spent'], self.user.currency)} / {format_amount(item['limit'], self.user.currency)} ({item['percentage']}%)"
                        ctk.CTkLabel(row, text=cat_title, font=("Segoe UI", 10, "bold"), text_color=BODY).pack(anchor="w")
                        bar = ctk.CTkProgressBar(row, height=8, progress_color=color)
                        bar.pack(fill="x", pady=(1, 3))
                        bar.set(item["ratio"])

                    for goal in goals_data:
                        row = ctk.CTkFrame(self.progress_scroll, fg_color="transparent")
                        row.pack(fill="x", pady=2)
                        pct = round(min((goal["current"] / goal["target"]) * 100, 100), 1) if goal["target"] > 0 else 0.0
                        goal_title = f"🎯 {goal['name']}: {format_amount(goal['current'], self.user.currency)} / {format_amount(goal['target'], self.user.currency)} ({pct}%)"
                        ctk.CTkLabel(row, text=goal_title, font=("Segoe UI", 10, "bold"), text_color=HIGHLIGHT).pack(anchor="w")
                        bar = ctk.CTkProgressBar(row, height=8, progress_color=HIGHLIGHT)
                        bar.pack(fill="x", pady=(1, 3))
                        bar.set(pct / 100.0)
        except Exception:
            pass

    def _start_network_monitoring(self):
        try:
            if not self.winfo_exists() or not hasattr(self, "network_lbl") or not self.network_lbl.winfo_exists():
                return

            if currency_service.is_offline:
                err = f" ({currency_service.last_error})" if currency_service.last_error else ""
                self.network_lbl.configure(text=f"🔴 Offline (fallback rates){err}", text_color=OFFLINE)
            else:
                self.network_lbl.configure(text="🟢 Online (live rates)", text_color=ONLINE)

            currency_service.fetch_rates_async()
            self.network_job = self.after(10_000, self._start_network_monitoring)
        except Exception:
            pass

    def _sync_system_theme(self):
        try:
            if not self.winfo_exists():
                return
            current_os_theme = get_system_appearance_mode()
            if current_os_theme != self._last_known_theme:
                self._last_known_theme = current_os_theme
                ctk.set_appearance_mode(current_os_theme)
        except Exception:
            pass
        self._theme_job = self.after(2_000, self._sync_system_theme)


def start_app(data_file):
    app = ExpenseApp(data_file)
    app.mainloop()