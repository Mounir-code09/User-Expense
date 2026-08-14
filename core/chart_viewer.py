"""Pie-chart viewer for expense summaries."""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .theme import CHART_COLORS


class ChartViewer:
    """Builds embedded expense charts for the app window."""

    @staticmethod
    def show_expense_pie_chart(parent_root, expense_data: dict, currency: str = "USD"):
        """Display pie chart of expense distribution. Filters zero/negative values."""
        active_expenses = {
            category.capitalize(): amount
            for category, amount in expense_data.items()
            if amount > 0
        }

        if not active_expenses:
            CTkMessagebox(
                title="No Data",
                message="No logged expenses available to visualize.",
                icon="info",
            )
            return

        chart_win = ctk.CTkToplevel(parent_root)
        chart_win.title("Expense Distribution Chart")
        chart_win.geometry("620x600")
        chart_win.transient(parent_root)
        chart_win.focus_set()

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg_color = "#1e1035" if is_dark else "#eef2ff"
        text_color = "#f1f5f9" if is_dark else "#1e1b4b"

        fig = Figure(figsize=(6, 5), dpi=100)
        fig.patch.set_facecolor(bg_color)

        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        labels = list(active_expenses.keys())
        amounts = list(active_expenses.values())

        _, _, autotexts = ax.pie(
            amounts,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=CHART_COLORS[: len(labels)],
            textprops={"color": text_color, "fontsize": 10},
        )

        for autotext in autotexts:
            autotext.set_color("#ffffff")
            autotext.set_weight("bold")

        ax.set_title(
            f"Expense Breakdown ({currency})",
            color=text_color,
            fontsize=14,
            pad=15,
            weight="bold",
        )

        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg=bg_color, highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True, padx=15, pady=(15, 5))

        def close_chart():
            fig.clear()
            canvas_widget.destroy()
            chart_win.destroy()

        chart_win.protocol("WM_DELETE_WINDOW", close_chart)

        close_btn = ctk.CTkButton(chart_win, text="Close Chart", command=close_chart)
        close_btn.pack(pady=(5, 15))
