"""
CustomTkinter Dashboard Interface Module
Handles UI event bindings and layout grids.
Delegates exchange rate updates and network checks to currency_service without freezing.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from User import User_class, Users
from Expense_tracker import ExpenseTracker
from data_manager import cat_v, set_database_file
from currency_service import currency_service

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def start_app(data_file):
    set_database_file(data_file)

    root = ctk.CTk()
    root.title("Expenses Tracker Dashboard")
    root.geometry("820x560")
    root.resizable(True, True)
    
    dialog = ctk.CTkInputDialog(text="Please enter your name:", title="Input")
    raw_name = dialog.get_input()
    name = raw_name.capitalize() if raw_name else "Guest"
    
    root.deiconify()
    root.lift()
    root.focus_force()

    user = User_class(name) 
    userE = ExpenseTracker(user) 
    Us = Users()

    # Initial async fetch to populate rates in the background
    currency_service.fetch_rates_async()

    # --- TOP CONTROL HEADER ---
    header_frame = ctk.CTkFrame(root, fg_color="transparent")
    header_frame.pack(pady=(20, 10), fill="x", padx=30)

    welcome_lbl = ctk.CTkLabel(header_frame, text=f"Welcome, {user.name}!", font=("Arial", 20, "bold"))
    welcome_lbl.pack(side="left")

    network_lbl = ctk.CTkLabel(header_frame, text="Checking Network...", font=("Arial", 11, "bold"))
    network_lbl.pack(side="left", padx=(15, 0))

    currency_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    currency_frame.pack(side="right")
    
    currency_lbl = ctk.CTkLabel(currency_frame, text="Account Currency:", font=("Arial", 11, "bold"))
    currency_lbl.pack(side="left", padx=(0, 10))
    
    def change_account_currency(new_currency):
        if user.currency == new_currency:
            return
            
        msg = CTkMessagebox(
            title="Convert Portfolio", 
            message=f"Convert all your stored budgets and expenses from {user.currency} to {new_currency}?",
            icon="question", option_1="Yes", option_2="No"
        )
        if msg.get() == "Yes":
            user.convert_account_currency(new_currency)
            currency_selector.set(new_currency)
            CTkMessagebox(title="Converted", message=f"Portfolio is now natively recorded in {new_currency}.", icon="check")
        else:
            currency_selector.set(user.currency)

    usd_btn = ctk.CTkButton(
        currency_frame, 
        text="Revert to USD", 
        command=lambda: change_account_currency("USD"), 
        width=100, 
        height=28, 
        fg_color="#36662e", 
        hover_color="#2b5224"
    )
    usd_btn.pack(side="right", padx=(10, 0))

    currency_selector = ctk.CTkOptionMenu(
        currency_frame, 
        values=["USD", "EUR", "GBP", "JPY", "CAD"],
        width=85,
        height=28,
        command=change_account_currency
    )
    currency_selector.pack(side="right")
    currency_selector.set(user.currency)

    instruction_lbl = ctk.CTkLabel(
        root, 
        text="Select actions below. Financials are logged physically in your native Account Currency.", 
        font=("Arial", 11), 
        text_color=("#1855C5", "#5694f7")
    )
    instruction_lbl.pack(pady=(0, 15))

    # --- NON-BLOCKING NETWORK MONITORING ---
    def update_network_status():
        # Reads the thread-safe flag from currency_service instantly
        if currency_service.is_offline:
            network_lbl.configure(text="🔴 Offline (Local Rates)", text_color="#A30000")
            if not getattr(root, 'offline_warned', False):
                CTkMessagebox(
                    title="Offline Mode", 
                    message="No internet connection detected. Using static local exchange rates.", 
                    icon="warning"
                )
                root.offline_warned = True
        else:
            network_lbl.configure(text="🟢 Online (Live Rates)", text_color="#00A300")
            root.offline_warned = False
            
        # Triggers an asynchronous refresh attempt every 30 seconds
        currency_service.fetch_rates_async()
        root.after(30000, update_network_status)

    update_network_status()

    # --- BUTTON EVENT OPERATIONS ---
    def set_budget():
        d1 = ctk.CTkInputDialog(text="Category to set budget:", title="Set Budget")
        category = d1.get_input()
        if not category: return
            
        category_clean = category.lower().strip()
        if not cat_v(category_clean):
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel")
            return

        d2 = ctk.CTkInputDialog(text=f"Budget limit amount ({user.currency}):", title="Set Budget")
        raw_limit = d2.get_input()
        if not raw_limit: return

        try:
            user.set_budget_limit(category_clean, raw_limit)
            CTkMessagebox(title="Budget Set", message=f"Budget set to {float(raw_limit):.2f} {user.currency}", icon="check")
        except ValueError as e:
            CTkMessagebox(title="Invalid Input", message=str(e), icon="cancel")

    def check_budget():
        d = ctk.CTkInputDialog(text="Category to check:", title="Check Budget")
        category = d.get_input()
        if not category: return
        
        category_clean = category.lower().strip()
        if cat_v(category_clean):
            budget = user.check_budget(category_clean)
            CTkMessagebox(title="Budget Check", message=f"Current limit for {category_clean}: {budget:.2f} {user.currency}", icon="info") 
        else:
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel") 

    def purge():
        d = ctk.CTkInputDialog(text="Category to purge:", title="Purge Budget")
        category = d.get_input()
        if not category: return
        
        category_clean = category.lower().strip()
        if cat_v(category_clean):
            user.purge(category_clean)
            CTkMessagebox(title="Purge Budget", message=f"Purged budget and history metrics for {category_clean}.", icon="check")
        else:
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel") 

    def add_expense():
        d1 = ctk.CTkInputDialog(text="Category to add expense:", title="Add Expense")
        category = d1.get_input()
        if not category: return
            
        category_clean = category.lower().strip()
        if not cat_v(category_clean):
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel")
            return

        d2 = ctk.CTkInputDialog(text=f"Amount for {category_clean} ({user.currency}):", title="Add Expense")
        raw_amount = d2.get_input()
        if not raw_amount: return

        try:
            amount = float(raw_amount)
            if amount <= 0.0:
                CTkMessagebox(title="Invalid Input", message="Please enter a positive amount.", icon="cancel")
                return
            
            budget_limit = user.budget_limit.get(category_clean)
            current_spending = userE.expenseReport.get(category_clean, 0.0)
            
            if budget_limit and (current_spending + amount) > budget_limit:            
                msg = CTkMessagebox(
                    title="Over Budget Warning", 
                    message=f"Adding {amount:.2f} {user.currency} will exceed limits for {category_clean}.\nSave transaction regardless?",
                    icon="warning", option_1="No", option_2="Yes"
                )
                if msg.get() != "Yes":
                    return

            userE.add_expense(category_clean, amount)
            CTkMessagebox(title="Expense Added", message=f"Recorded {amount:.2f} {user.currency} under {category_clean}.", icon="check")
        except ValueError:
            CTkMessagebox(title="Invalid Input", message="Please enter a valid numeric value.", icon="cancel")

    def show_status_window():
        status_win = ctk.CTkToplevel(root)
        status_win.title("Financial Status Dashboard")
        status_win.geometry("540x400")
        
        text_widget = ctk.CTkTextbox(status_win, font=("Consolas", 12), activate_scrollbars=True)
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", userE.get_status_report())
        text_widget.configure(state="disabled")
        
        close_btn = ctk.CTkButton(status_win, text="Close View", command=status_win.destroy)
        close_btn.pack(fill="x", padx=15, pady=(0, 15))
        status_win.transient(root)   
        status_win.focus_set()        

    def search_expenses():
        d = ctk.CTkInputDialog(text="Category to search:", title="Search Expense")
        category = d.get_input()
        if not category: return
        
        category_clean = category.lower().strip()
        if cat_v(category_clean):
            result = userE.search_expenses(category_clean) 
            if result is not None:
                CTkMessagebox(title="Search Result", message=f"{user.name} spent {result:.2f} {user.currency} on {category_clean}", icon="info") 
            else:
                CTkMessagebox(title="Search Result", message="No transaction records found for this category.", icon="info") 
        else:
            CTkMessagebox(title="Invalid Category", message=f"'{category}' is not a valid category.", icon="cancel") 

    def total_expenses():
        total = userE.total_expenses_of_user()
        CTkMessagebox(title="Total Aggregate Expenses", message=f"Total user footprint portfolio costs: {total:.2f} {user.currency}", icon="info") 

    def show_users_gui():
        users_list = Us.show_users() 
        if users_list:
            CTkMessagebox(title="Users List", message="Current Users:\n\n" + "\n".join(users_list), icon="info") 
        else:
            CTkMessagebox(title="Users List", message="No active logs mapped.", icon="info")

    def delete_user_gui():
        d = ctk.CTkInputDialog(text="Enter username to delete:", title="Delete User")
        raw_del_name = d.get_input()
        if not raw_del_name: return
        
        del_name = raw_del_name.strip().capitalize()
        if del_name == user.name:
            CTkMessagebox(title="Error", message="You cannot delete the currently active configuration profile.", icon="cancel")
            return

        if del_name in Us.show_users():
            msg = CTkMessagebox(title="Confirmation", message=f"Permanently wipe {del_name}'s database file records?", icon="question", option_1="Yes", option_2="No")
            if msg.get() == "Yes":
                Us.delete_user(del_name) 
                CTkMessagebox(title="Deleted User", message=f"Successfully scrubbed {del_name}.", icon="check")
        else:
            CTkMessagebox(title="Error", message="Profile record does not exist.", icon="cancel")

    def get_user_gui():
        d = ctk.CTkInputDialog(text="Enter username to find:", title="Find User")
        raw_search_name = d.get_input()
        if not raw_search_name: return
        
        search_name = raw_search_name.capitalize()
        target_user = Us.get_user(search_name)
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

    def exit_app():
        CTkMessagebox(title="Exit", message="State saved completely. Goodbye!", icon="info") 
        root.after(800, lambda: root.quit())  

    # --- GRID FRAME ARRANGEMENT ---
    grid_frame = ctk.CTkFrame(root, fg_color="transparent")
    grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
    grid_frame.columnconfigure(0, weight=1)
    grid_frame.columnconfigure(1, weight=1)

    button_config = {"width": 240, "font": ("Arial", 12, "bold"), "height": 40, "corner_radius": 8}

    buttons_left = [("1. Set a Budget", set_budget), ("2. Check Budget", check_budget), 
                    ("3. Add Expense", add_expense), ("4. View Status Table", show_status_window), 
                    ("5. Search Expense", search_expenses)]
    buttons_right = [("6. Total Expenses", total_expenses), ("7. Purge Category", purge), 
                     ("8. Show Users", show_users_gui), ("9. Delete User", delete_user_gui), 
                     ("10. Find User", get_user_gui)]

    for idx, (txt, cmd) in enumerate(buttons_left):
        ctk.CTkButton(grid_frame, text=txt, command=cmd, **button_config).grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
    for idx, (txt, cmd) in enumerate(buttons_right):
        ctk.CTkButton(grid_frame, text=txt, command=cmd, **button_config).grid(row=idx, column=1, padx=10, pady=8, sticky="ew")

    exit_btn = ctk.CTkButton(root, text="Exit Application Workspace", command=exit_app, fg_color="#A30000", hover_color="#7A0000", font=("Arial", 12, "bold"), height=42)
    exit_btn.pack(fill="x", padx=30, pady=(10, 20))
    
    root.mainloop()