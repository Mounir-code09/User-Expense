"""Visual analytics with interactive 3-way toggle (Expenses, Budgets, Comparison)."""
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .theme import CARD_BG, CHART_COLORS, PRIMARY, PRIMARY_HOVER, SUCCESS, DANGER


class ChartViewer:
    """Embedded interactive financial visualization dialog."""

    @staticmethod
    def show_expense_pie_chart(parent_root, user):
        """Display interactive charts window with spending, budget, and comparison views."""
        expenses = user.get_category_expenses()
        budgets = user.budget_limits
        currency = user.currency

        has_expenses = any(v > 0 for v in expenses.values())
        has_budgets = any(v > 0 for v in budgets.values())

        if not has_expenses and not has_budgets:
            CTkMessagebox(
                title="No Data",
                message="No expenses or budgets available to visualize yet.",
                icon="info",
            )
            return

        chart_win = ctk.CTkToplevel(parent_root)
        chart_win.title("Financial Visual Analytics")
        chart_win.geometry("680x640")
        chart_win.minsize(620, 580)
        chart_win.transient(parent_root)
        chart_win.focus_set()

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg_color = "#1e1035" if is_dark else "#eef2ff"
        card_color = "#281845" if is_dark else "#ffffff"
        text_color = "#f1f5f9" if is_dark else "#1e1b4b"

        # Top view selector
        top_bar = ctk.CTkFrame(chart_win, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        view_toggle = ctk.CTkSegmentedButton(
            top_bar,
            values=["Spending Distribution", "Budget Allocation", "Spent vs. Budget"],
            font=("Segoe UI", 12, "bold"),
            selected_color=PRIMARY[1] if is_dark else PRIMARY[0],
            selected_hover_color=PRIMARY_HOVER[1] if is_dark else PRIMARY_HOVER[0],
        )
        view_toggle.pack(fill="x")
        view_toggle.set("Spending Distribution" if has_expenses else "Budget Allocation")

        fig = Figure(figsize=(6.5, 4.8), dpi=100)
        fig.patch.set_facecolor(bg_color)
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg=bg_color, highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True, padx=15, pady=5)

        def draw_view(selected_view):
            fig.clear()
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg_color)

            if selected_view == "Spending Distribution":
                active = {k.capitalize(): v for k, v in expenses.items() if v > 0}
                if not active:
                    ax.text(0.5, 0.5, "No spending recorded yet", ha="center", va="center", color=text_color, fontsize=13)
                    ax.axis("off")
                else:
                    labels = list(active.keys())
                    amounts = list(active.values())
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
                    ax.set_title(f"Spending Breakdown ({currency})", color=text_color, fontsize=14, pad=15, weight="bold")

            elif selected_view == "Budget Allocation":
                active = {k.capitalize(): v for k, v in budgets.items() if v > 0}
                if not active:
                    ax.text(0.5, 0.5, "No category budgets configured", ha="center", va="center", color=text_color, fontsize=13)
                    ax.axis("off")
                else:
                    labels = list(active.keys())
                    amounts = list(active.values())
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
                    ax.set_title(f"Budget Allocation ({currency})", color=text_color, fontsize=14, pad=15, weight="bold")

            elif selected_view == "Spent vs. Budget":
                cats = [c for c in user.categories if expenses.get(c, 0) > 0 or budgets.get(c, 0) > 0]
                if not cats:
                    cats = user.categories[:5]

                cat_names = [c.capitalize() for c in cats]
                spent_vals = [expenses.get(c, 0.0) for c in cats]
                budget_vals = [budgets.get(c, 0.0) for c in cats]

                import numpy as np
                y = np.arange(len(cat_names))
                height = 0.35

                ax.barh(y - height / 2, budget_vals, height, label="Budget Limit", color="#6366f1", alpha=0.85)
                
                # Color spent bars based on whether limit exceeded
                spent_colors = [
                    DANGER[0] if (budgets.get(c, 0) > 0 and expenses.get(c, 0) > budgets.get(c, 0)) else SUCCESS[0]
                    for c in cats
                ]
                ax.barh(y + height / 2, spent_vals, height, label="Actual Spent", color=spent_colors, alpha=0.9)

                ax.set_yticks(y)
                ax.set_yticklabels(cat_names, color=text_color, fontsize=10)
                ax.tick_params(colors=text_color)
                ax.set_xlabel(f"Amount ({currency})", color=text_color, fontsize=11)
                ax.set_title("Budget vs. Actual Spending", color=text_color, fontsize=14, pad=15, weight="bold")
                ax.legend(facecolor=card_color, edgecolor=text_color, labelcolor=text_color, loc="lower right")
                ax.grid(axis="x", linestyle="--", alpha=0.3)

            fig.tight_layout()
            canvas.draw()

        view_toggle.configure(command=draw_view)
        draw_view(view_toggle.get())

        def close_chart():
            fig.clear()
            canvas_widget.destroy()
            chart_win.destroy()

        chart_win.protocol("WM_DELETE_WINDOW", close_chart)

        bottom = ctk.CTkFrame(chart_win, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(5, 15))
        close_btn = ctk.CTkButton(
            bottom,
            text="Close",
            command=close_chart,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            height=36,
        )
        close_btn.pack(fill="x")
