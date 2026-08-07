"""
CustomTkinter GUI View
Class-based layout module cleanly delegating actions to UIActions.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from User import User_class, Users
from Expense_tracker import ExpenseTracker
from data_manager import set_database_file
from currency_service import currency_service
from ui_actions import UIActions

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ExpenseApp(ctk.CTk):
    def __init__(self, username, data_file):
        super().__init__()
        set_database_file(data_file)
        
        self.title("Expenses Tracker Dashboard")
        self.geometry("820x560")
        self.resizable(True, True)

        self.user = User_class(username)
        self.tracker = ExpenseTracker(self.user)
        self.users = Users()
        self.actions = UIActions(self.user, self.tracker, self.users, self)

        currency_service.fetch_rates_async()
        self._build_ui()
        self._start_network_monitoring()

    def _build_ui(self):
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

        # --- GRID FRAME ARRANGEMENT (ALL 10 BUTTONS) ---
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        button_config = {"width": 240, "font": ("Arial", 12, "bold"), "height": 40, "corner_radius": 8}

        buttons_left = [
            ("1. Set a Budget", self.actions.set_budget),
            ("2. Check Budget", self.actions.check_budget), 
            ("3. Add Expense", self.actions.add_expense),
            ("4. View Status Table", self.actions.show_status), 
            ("5. Search Expense", self.actions.search_expenses)
        ]
        buttons_right = [
            ("6. Total Expenses", self.actions.total_expenses),
            ("7. Purge Category", self.actions.purge), 
            ("8. Show Users", self.actions.show_users),
            ("9. Delete User", self.actions.delete_user), 
            ("10. Find User", self.actions.get_user)
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
        if currency_service.is_offline:
            self.network_lbl.configure(text="🔴 Offline (Local Rates)", text_color="#A30000")
            if not getattr(self, 'offline_warned', False):
                CTkMessagebox(
                    title="Offline Mode", 
                    message="No internet connection detected. Using static local exchange rates.", 
                    icon="warning"
                )
                self.offline_warned = True
        else:
            self.network_lbl.configure(text="🟢 Online (Live Rates)", text_color="#00A300")
            self.offline_warned = False
            
        currency_service.fetch_rates_async()
        self.after(30000, self._start_network_monitoring)

def start_app(data_file):
    dialog = ctk.CTkInputDialog(text="Please enter your name:", title="Input")
    raw_name = dialog.get_input()
    name = raw_name.capitalize() if raw_name else "Guest"
    
    app = ExpenseApp(name, data_file)
    app.mainloop()