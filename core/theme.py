"""Shared colors, styling constants, and visual formatting helpers."""

APP_BG = ("#f1f5f9", "#0b0618")
CARD_BG = ("#ffffff", "#19102e")
CARD_BORDER = ("#cbd5e1", "#5b21b6")
ACCENT_BAR = ("#4f46e5", "#9333ea")

PRIMARY = ("#2563eb", "#3b82f6")
PRIMARY_HOVER = ("#1d4ed8", "#2563eb")
SUCCESS = ("#059669", "#10b981")
SUCCESS_HOVER = ("#047857", "#059669")
DANGER = ("#dc2626", "#ef4444")
DANGER_HOVER = ("#b91c1c", "#dc2626")
WARNING = ("#d97706", "#f59e0b")
NEUTRAL = ("#64748b", "#475569")
NEUTRAL_HOVER = ("#475569", "#334155")

TITLE = ("#1e293b", "#f8fafc")
SUBTITLE = ("#475569", "#cbd5e1")
BODY = ("#334155", "#e2e8f0")
MUTED = ("#64748b", "#94a3b8")
HIGHLIGHT = ("#0284c7", "#38bdf8")

ONLINE = ("#059669", "#34d399")
OFFLINE = ("#dc2626", "#f87171")

CHART_COLORS = [
    "#4f46e5", "#06b6d4", "#f97316", "#ec4899",
    "#10b981", "#8b5cf6", "#14b8a6", "#f43f5e",
    "#eab308", "#64748b",
]


def format_amount(amount, currency=None):
    """Format numeric value with thousands commas and 2 decimals."""
    try:
        val = float(amount)
        formatted = f"{val:,.2f}"
    except (ValueError, TypeError):
        formatted = "0.00"

    if currency:
        return f"{formatted} {currency}"
    return formatted