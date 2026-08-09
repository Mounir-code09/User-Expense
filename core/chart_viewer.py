"""
Matplotlib Chart Embedder for CustomTkinter
Uses object-oriented Figure API to eliminate phantom Tk root windows.
"""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ChartViewer:
    @staticmethod
    def show_expense_pie_chart(parent_root, expense_data: dict, currency: str = "USD"):
        # Filter out categories with zero or negative expenses to keep the chart clean
        active_expenses = {cat.capitalize(): amt for cat, amt in expense_data.items() if amt > 0}
        
        # Display an info message box if there is no data available to plot
        if not active_expenses:
            CTkMessagebox(
                title="No Data", 
                message="No logged expenses available to visualize.", 
                icon="info"
            )
            return

        # Create an independent Toplevel window linked to the parent root
        chart_win = ctk.CTkToplevel(parent_root)
        chart_win.title("Expense Distribution Chart")
        chart_win.geometry("600x580")
        chart_win.transient(parent_root)
        chart_win.focus_set()

        # Match colors dynamically based on the current system theme (Dark/Light)
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
        text_color = "#ffffff" if is_dark else "#000000"

        # Instantiate the Matplotlib Figure directly to avoid global pyplot overhead
        fig = Figure(figsize=(6, 5), dpi=100)
        fig.patch.set_facecolor(bg_color)
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        labels = list(active_expenses.keys())
        amounts = list(active_expenses.values())
        colors = ["#4A90E2", "#50E3C2", "#F5A623", "#E65D65", "#9013FE", "#B8E986"]

        # Generate pie chart wedges with percentage labels
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors[:len(labels)],
            textprops=dict(color=text_color, fontsize=10)
        )

        # Style percentage text for better readability
        for autotext in autotexts:
            autotext.set_color("#ffffff")
            autotext.set_weight("bold")

        ax.set_title(
            f"Expense Breakdown ({currency})", 
            color=text_color, 
            fontsize=14, 
            pad=15, 
            weight="bold"
        )

        # Embed the Matplotlib figure into the CustomTkinter canvas widget
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg=bg_color, highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True, padx=15, pady=(15, 5))

        def close_chart():
            chart_win.destroy()

        chart_win.protocol("WM_DELETE_WINDOW", close_chart)

        close_btn = ctk.CTkButton(chart_win, text="Close Chart", command=close_chart)
        close_btn.pack(pady=(5, 15))