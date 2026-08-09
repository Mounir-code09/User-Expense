"""
CustomTkinter GUI View
Class-based layout module managing single-root lifecycle, vibrant welcome screen, and dashboard UI delegation.
"""
import customtkinter as ctk
from .user import User_class, Users
from .expense_tracker import ExpenseTracker
from .data_manager import set_database_file
from .currency_service import currency_service
from .ui_actions import UIActions

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ExpenseApp(ctk.CTk):
    """
    Main application window managing the single-root lifecycle,
    vibrant startup authentication frame, and dashboard UI.
    """
    def __init__(self, data_file):
        super().__init__()
        set_database_file(data_file)
        
        self.title("Expenses Tracker Dashboard")
        self.geometry("820x600")
        self.resizable(True, True)
        
        self.data_file = data_file
        self.user = None
        self.tracker = None
        self.users = Users()
        self.actions = None
        self.network_job = None
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Render the colorful startup prompt frame inside the single root window
        self._build_startup_ui()

    def _build_startup_ui(self):
        """Renders an attractive, colorful, and professional username prompt card inside the main window."""
        self.startup_frame = ctk.CTkFrame(self, fg_color=("gray92", "gray14"))
        self.startup_frame.pack(fill="both", expand=True)

        card_frame = ctk.CTkFrame(
            self.startup_frame, 
            width=420, 
            height=325, 
            corner_radius=16,
            fg_color=("white", "gray20"),
            border_width=2,
            border_color=("#1f6aa5", "#1f538d")
        )
        card_frame.place(relx=0.5, rely=0.5, anchor="center")
        card_frame.pack_propagate(False)

        # Decorative top accent banner for a professional splash of color
        accent_banner = ctk.CTkFrame(
            card_frame, 
            height=8, 
            corner_radius=0, 
            fg_color=("#1f6aa5", "#3b82f6")
        )
        accent_banner.pack(fill="x", side="top")

        inner_container = ctk.CTkFrame(card_frame, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=30, pady=25)

        title_lbl = ctk.CTkLabel(
            inner_container, 
            text="Welcome to Expense Tracker", 
            font=("Arial", 20, "bold"),
            text_color=("#1f6aa5", "#60a5fa")
        )
        title_lbl.pack(pady=(0, 8))

        instruction_lbl = ctk.CTkLabel(
            inner_container, 
            text="Enter your profile username to access your portfolio:", 
            font=("Arial", 12),
            text_color=("gray40", "gray70"),
            wraplength=340
        )
        instruction_lbl.pack(pady=(0, 20))

        self.entry_username = ctk.CTkEntry(
            inner_container, 
            width=300, 
            height=40, 
            font=("Arial", 13),
            corner_radius=8
        )
        self.entry_username.pack(pady=(0, 20))
        self.entry_username.focus()
        self.entry_username.bind("<Return>", lambda event: self._confirm_username())

        btn_confirm = ctk.CTkButton(
            inner_container, 
            text="Start Workspace", 
            width=300, 
            height=40, 
            font=("Arial", 13, "bold"),
            fg_color=("#1f6aa5", "#1f538d"),
            hover_color=("#14406e", "#163c68"),
            corner_radius=8,
            command=self._confirm_username
        )
        btn_confirm.pack()

    def _confirm_username(self):
        """Captures the username input, cleans up the startup frame, and loads the dashboard."""
        raw_name = self.entry_username.get()
        
        if raw_name and raw_name.strip():
            username = raw_name.strip().capitalize()
        else:
            username = "Guest"

        self.startup_frame.destroy()

        self.user = User_class(username)
        self.tracker = ExpenseTracker(self.user)
        self.actions = UIActions(self.user, self.tracker, self.users, self)

        currency_service.fetch_rates_async()
        self._build_dashboard_ui()
        self._start_network_monitoring()

    def _build_dashboard_ui(self):
        # --- TOP CONTROL HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(20, 10), fill="x", padx=30)

        welcome_lbl = ctk.CTkLabel(header_frame, text=f"Welcome, {self.user.name}!", font=("Arial", 20, "bold"))
        welcome_lbl.pack(side="left")

        self.network_lbl = ctk.CTkLabel(header_frame, text="Checking Network...", font=("Arial", 11, "bold"))
        self.network_lbl.pack(side="left", padx=(15, 0))

        currency_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        currency_frame.pack(side="right")
        
        currency_lbl = ctk.CTkLabel(currency_frame, text="Account Currency:", font=("Arial", 11, "bold"))
        currency_lbl.pack(side="left", padx=(0, 10))

        usd_btn = ctk.CTkButton(
            currency_frame, 
            text="Revert to USD", 
            command=lambda: self.actions.change_account_currency("USD", self.currency_selector), 
            width=100, 
            height=28, 
            fg_color="#36662e", 
            hover_color="#2b5224"
        )
        usd_btn.pack(side="right", padx=(10, 0))

        self.currency_selector = ctk.CTkOptionMenu(
            currency_frame, 
            values=["USD", "EUR", "GBP", "JPY", "CAD"],
            width=85,
            height=28,
            command=lambda val: self.actions.change_account_currency(val, self.currency_selector)
        )
        self.currency_selector.pack(side="right")
        self.currency_selector.set(self.user.currency)

        instruction_lbl = ctk.CTkLabel(
            self, 
            text="Select actions below. Financials are logged physically in your native Account Currency.", 
            font=("Arial", 11), 
            text_color=("#1855C5", "#5694f7")
        )
        instruction_lbl.pack(pady=(0, 15))

        # --- GRID FRAME ARRANGEMENT ---
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        button_config = {"width": 240, "font": ("Arial", 12, "bold"), "height": 40, "corner_radius": 8}

        buttons_left = [
            ("1. Set a Budget", self.actions.set_budget),
            ("2. Check Budget", self.actions.check_budget), 
            ("3. Add Expense", self.actions.add_expense),
            ("4. Remove Expense", self.actions.remove_expense),
            ("5. View Status Table", self.actions.show_status), 
            ("6. Search Expense", self.actions.search_expenses)
        ]
        buttons_right = [
            ("7. Visual Breakdown Of Expenses", self.actions.show_chart),
            ("8. Total Expenses", self.actions.total_expenses),
            ("9. Purge Category", self.actions.purge), 
            ("10. Show Users", self.actions.show_users),
            ("11. Delete User", self.actions.delete_user), 
            ("12. Find User", self.actions.get_user)
        ]

        for idx, (txt, cmd) in enumerate(buttons_left):
            ctk.CTkButton(grid_frame, text=txt, command=cmd, **button_config).grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
        for idx, (txt, cmd) in enumerate(buttons_right):
            ctk.CTkButton(grid_frame, text=txt, command=cmd, **button_config).grid(row=idx, column=1, padx=10, pady=8, sticky="ew")

        exit_btn = ctk.CTkButton(
            self, 
            text="Exit Application Workspace", 
            command=self.actions.exit_app, 
            fg_color="#A30000", 
            hover_color="#7A0000", 
            font=("Arial", 12, "bold"), 
            height=42
        )
        exit_btn.pack(fill="x", padx=30, pady=(10, 20))

    def _start_network_monitoring(self):
        """Polls network connectivity periodically using the Tkinter after scheduler."""
        if not self.winfo_exists():
            return

        if currency_service.is_offline:
            self.network_lbl.configure(
                text="🔴 Offline (Local Rates)",
                text_color="#A30000"
            )
        else:
            self.network_lbl.configure(
                text="🟢 Online (Live Rates)",
                text_color="#00A300"
            )

        currency_service.fetch_rates_async()

        self.network_job = self.after(
            10000,
            self._start_network_monitoring
        )

    def on_close(self):
        """Saves user data and safely cancels pending background jobs before exit."""
        if self.user:
            self.user.save()

        try:
            if self.network_job is not None:
                self.after_cancel(self.network_job)
        except Exception:
            pass

        self.destroy()


def start_app(data_file):
    """Initializes and runs the main application instance."""
    app = ExpenseApp(data_file)
    app.mainloop()