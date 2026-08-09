"""
Application Theme
Centralized color palette for a vibrant, consistent visual identity across all windows.
Supports automatic light/dark adaptation via CustomTkinter appearance mode tuples.
"""

# ---------------------------------------------------------------------------
# Brand palette — vivid, high-contrast tones designed for readability
# ---------------------------------------------------------------------------

# Surfaces & backgrounds
APP_BG = ("#eef2ff", "#0f0720")              # Soft lavender / deep cosmic purple
CARD_BG = ("#ffffff", "#1e1035")             # Crisp white / rich plum card
CARD_BORDER = ("#6366f1", "#a855f7")         # Indigo / bright violet outline
ACCENT_BAR = ("#4f46e5", "#c026d3")          # Indigo-to-magenta accent stripe

# Primary actions
PRIMARY = ("#2563eb", "#3b82f6")             # Bold blue
PRIMARY_HOVER = ("#1d4ed8", "#2563eb")
SUCCESS = ("#059669", "#10b981")             # Emerald green
SUCCESS_HOVER = ("#047857", "#059669")
DANGER = ("#dc2626", "#ef4444")              # Vivid red
DANGER_HOVER = ("#b91c1c", "#dc2626")
WARNING = ("#d97706", "#f59e0b")             # Amber
NEUTRAL = ("#64748b", "#475569")             # Slate gray
NEUTRAL_HOVER = ("#475569", "#334155")

# Text
TITLE = ("#4338ca", "#c084fc")               # Deep indigo / soft violet
SUBTITLE = ("#6366f1", "#a78bfa")            # Muted indigo / lilac
BODY = ("#334155", "#e2e8f0")               # Dark slate / light gray
MUTED = ("#64748b", "#94a3b8")             # Secondary descriptive text
HIGHLIGHT = ("#0891b2", "#22d3ee")           # Cyan highlight for tips

# Network status indicators
ONLINE = ("#059669", "#34d399")
OFFLINE = ("#dc2626", "#f87171")

# Modal-specific accents
SIGNIN_ACCENT = ("#2563eb", "#60a5fa")
SIGNUP_ACCENT = ("#059669", "#34d399")

# Chart colors — bold, distinguishable wedges
CHART_COLORS = [
    "#6366f1", "#06b6d4", "#f97316", "#ec4899",
    "#84cc16", "#8b5cf6", "#14b8a6", "#f43f5e",
]