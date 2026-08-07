import tkinter as tk
from tkinter import messagebox, simpledialog
from User import User_class, Users
from Expense_tracker import ExpenseTracker
from data_manager import cat_v

def start_app(data_file):
    root = tk.Tk()
    root.title("Expenses Tracker Dashboard")
    root.geometry("750x450")  # Slightly increased height to fit the new buttons cleanly
    root.resizable(True, True)
    root.configure(bg="#1855C5")  

    name = simpledialog.askstring("Input", "Please enter your name:", parent=root).capitalize()
    if not name:
        name = "Guest" 
    root.lift() # pulls the main window to the very front of the desktop
    root.focus_force()

    user = User_class(name) 
    userE = ExpenseTracker(user) 
    Us = Users(name)  # Create a Users instance to manage multiple users

    root.configure(pady=15, padx=20)

    # Welcome Label
    welcome_lbl = tk.Label(
        root, 
        text=f"Welcome, {user.name}!", 
        font=("Arial", 14, "bold"), 
        pady=5
    )
    welcome_lbl.pack()

    # instruction Label
    instruction_lbl = tk.Label(
        root, 
        text="Choose an action below:", 
        font=("Arial", 10), 
        fg="#391CCE", 
        pady=5
    )
    instruction_lbl.pack(pady=(0, 15))
    instruction_lbl.focus_set()  # Set focus to the instruction label for accessibility

    # --- Action functions ---
    def set_budget():
        category = simpledialog.askstring("Set Budget", "Category to set budget:", parent=root) 
        if cat_v(category) == True:
            limit = simpledialog.askfloat("Set Budget", "Budget limit amount:", parent=root) 
            if limit is not None:
                user.set_budget_limit(category, limit) 
                messagebox.showinfo("Budget Set", f"Budget for {category} set to ${limit:.2f}")
        else:
            messagebox.showerror("Invalid Category", f"'{category}' is not a valid category.") 

    def check_budget():
        category = simpledialog.askstring("Check Budget", "Category to check:", parent=root) 
        if cat_v(category) == True:
            messagebox.showinfo("Budget Check", user.check_budget(category)) 
        else:
            messagebox.showerror("Invalid Category", f"'{category}' is not a valid category.") 

    def add_expense():
        category = simpledialog.askstring("Add Expense", "Category to add expense:", parent=root) 
        if cat_v(category) == True:
            amount = simpledialog.askfloat("Add Expense", f"Amount for {category}:", parent=root) 
            if amount is not None:
                userE.add_expense(category, amount) 
                messagebox.showinfo("Expense Added", f"Recorded ${amount:.2f} under {category}.") 
        else:
            messagebox.showerror("Invalid Category", f"'{category}' is not a valid category.") 

    def show_status_window():
        status_win = tk.Toplevel(root)
        status_win.title("Financial Status")
        status_win.geometry("500x320")
        status_win.configure(bg="#0A0A0A") 
        text_widget = tk.Text(status_win, wrap="none", font=("Consolas", 11), padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        
        report_text = userE.get_status_report()
        text_widget.insert("1.0", report_text)
        text_widget.config(state="disabled") #read only
        
        close_btn = tk.Button(status_win, text="Close View", command=status_win.destroy, pady=5)
        close_btn.pack(fill="x")

        status_win.transient(root)   
        status_win.grab_set()        

    def search_expenses():
        category = simpledialog.askstring("Search Expense", "Category to search:", parent=root) 
        if cat_v(category) == True:
            result = userE.search_expenses(user.name, category) 
            if result is not None:
                messagebox.showinfo("Search Result", f"{user.name} spent ${result:.2f} on {category}") 
            else:
                messagebox.showinfo("Search Result", "No record found.") 
        else:
            messagebox.showerror("Invalid Category", f"'{category}' is not a valid category.") 

    def total_expenses():
        messagebox.showinfo("Total Expenses", f"Total expenses: ${userE.total_expenses_of_user():.2f}") 

    def purge_budget():
        category = simpledialog.askstring("Purge Budget", "Category to purge:", parent=root) 
        if cat_v(category) == True:
            user.purge_budget(category) 
            messagebox.showinfo("Purge Budget", f"Purged budget for {category}.")
        else:
            messagebox.showerror("Invalid Category", f"'{category}' is not a valid category.") 

    def show_users_gui():
        users_list = Us.show_users() 
        if users_list:
            messagebox.showinfo("Users List", "Current Users:\n" + "\n".join(users_list)) 
        else:
            messagebox.showinfo("Users List", "No users found.")

    def delete_user_gui():
        del_name = simpledialog.askstring("Delete User", "Enter username to delete:", parent=root).capitalize() 
        if del_name in Us.users:
            comfirmation = messagebox.askyesno("Comfirmation", "You sure you want to delete this user'data? ")
            if comfirmation:
                Us.delete_user(del_name) 
                messagebox.showinfo("Deleted User", del_name)
            else:
                root.withdraw()
        else:
            messagebox.showerror('Error', "User doesnt exist")

    def get_user_gui():
            search_name = simpledialog.askstring("Find User", "Enter username to find:", parent=root).capitalize()
            if not search_name:
                return  # User clicked cancel
            
            target_user = Us.get_user(search_name)
            if target_user:
                info_message = f"User Profile: {target_user.name}\n"
                info_message += "===================\n"
                info_message += "Budget Limits:\n"
                
                if target_user.budget_limit: #checks if there is a budget 
                    for category, limit in target_user.budget_limit.items():
                        info_message += f"  - {category.capitalize()}: ${limit:.2f}\n"
                else:
                    info_message += "  No budgets set.\n"
                    
                total_spent = sum(target_user.current_expenses.values()) # total spending
                info_message += f"\nTotal Spent: ${total_spent:.2f}"                                 
                messagebox.showinfo(f"User Found: {search_name}", info_message) # compiled information in a popup dialog
            else:
                messagebox.showerror('Error', f"User '{search_name}' does not exist.")

    def exit_app():
        messagebox.showinfo("Exit", "Goodbye! Thanks for tracking your expenses.") 
        root.destroy()

    # --- Buttons ---
    # Added matching background color so layout frame remains invisible
    grid_frame = tk.Frame(root, bg="#1855C5")
    grid_frame.pack(fill="both", expand=True)

    # Configure columns to split and stretch space evenly
    grid_frame.columnconfigure(0, weight=1)
    grid_frame.columnconfigure(1, weight=1)

    button_config = {
        "width": 26,              
        "font": ("Arial", 11, "bold"), 
        "pady": 6,                
        "relief": "groove"
    }

    # Left Column Buttons (anchored left with sticky="w")
    btn1 = tk.Button(grid_frame, text="1. Set a Budget", command=set_budget, **button_config)
    btn1.grid(row=0, column=0, padx=(20, 0), pady=8, sticky="w")

    btn2 = tk.Button(grid_frame, text="2. Check Budget", command=check_budget, **button_config)
    btn2.grid(row=1, column=0, padx=(20, 0), pady=8, sticky="w")

    btn3 = tk.Button(grid_frame, text="3. Add Expense", command=add_expense, **button_config)
    btn3.grid(row=2, column=0, padx=(20, 0), pady=8, sticky="w")

    btn4 = tk.Button(grid_frame, text="4. View Status Table", command=show_status_window, **button_config)
    btn4.grid(row=3, column=0, padx=(20, 0), pady=8, sticky="w")

    btn5 = tk.Button(grid_frame, text="5. Search Expense", command=search_expenses, **button_config)
    btn5.grid(row=4, column=0, padx=(20, 0), pady=8, sticky="w")

    # Right Column Buttons (anchored right with sticky="e")
    btn6 = tk.Button(grid_frame, text="6. Get Total Expenses", command=total_expenses, **button_config)
    btn6.grid(row=0, column=1, padx=(0, 20), pady=8, sticky="e")

    btn7 = tk.Button(grid_frame, text="7. Purge Budget", command=purge_budget, **button_config)
    btn7.grid(row=1, column=1, padx=(0, 20), pady=8, sticky="e")

    btn8 = tk.Button(grid_frame, text="8. Delete User", command=delete_user_gui, **button_config)
    btn8.grid(row=2, column=1, padx=(0, 20), pady=8, sticky="e")

    btn9 = tk.Button(grid_frame, text="9. Show Users List", command=show_users_gui, **button_config)
    btn9.grid(row=3, column=1, padx=(0, 20), pady=8, sticky="e")

    btn10 = tk.Button(
        grid_frame,
        text="10. Find A User",
        command=get_user_gui,
        **button_config
    )
    btn10.grid(row=4, column=1, padx=(0, 20), pady=8, sticky="e")
    
    # Exit Button 
    btn_exit = tk.Button(
        grid_frame,
        text="Exit App",
        command=exit_app,
        bg="#C01E13", 
        fg="white",
        activebackground="#D32F2F",
        activeforeground="white",
        **button_config
    )
    btn_exit.grid(row=5, column=0, columnspan=2, padx=20, pady=14)

    root.mainloop()