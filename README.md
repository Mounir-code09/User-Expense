# Multi-Currency Expense & Financial Tracker

A desktop application for personal finance management — expense tracking, category budgets, income logging, recurring transaction templates, multi-currency conversion, and visual analytics.

Built with **Python · CustomTkinter · Matplotlib · JSON**. No database server required.

---

## Features

**Dashboard & Period Filtering**
- Live metric cards: Total Expenses, Total Income, Net Savings, Remaining Budget
- Period selector: Filter dashboard metrics and progress bars by All Time, recent months (This Month, Last Month, 2/3 Months Ago), or calendar years (This Year, Last Year)
- Color-coded category budget progress bars (green / orange / red thresholds)
- Real-time OS dark/light mode sync — no restart required
- Light and dark mode via CustomTkinter system detection

**Expenses, Income & Strict Validation**
- Log transactions with category, amount, date, and optional note
- Strict date validation: Prevents recording transactions or income dated in the future
- Log income by source (Salary, Freelance, Investment, Business, Gift, Other)
- Searchable, filterable ledgers for both expenses and income
- Delete individual entries from either ledger

**Recurring Transaction Templates**
- Save reusable templates for frequent expenses (e.g. rent, utilities) and income (e.g. paycheck)
- 1-click "Log Today" execution from the recurring templates manager
- Automatic currency recalculation when switching account base currency

**Bank Statement Import (QIF / OFX) & Payee Memory**
- Import standard `.qif`, `.ofx`, and `.qfx` bank statement files
- Transaction preview with per-row category assignment and high-contrast centered controls
- **Payee Categorization Memory**: Remembers how you categorize payees (e.g. Netflix -> Entertainment) and auto-suggests categories on future imports
- Future-dated records automatically excluded by strict date guards

**Savings Goals Tracker**
- Create dedicated savings goals (e.g., Vacation Fund, Emergency Savings) with target amounts and dates
- Track progress with dedicated dashboard visual progress indicators
- Deposit and withdraw funds with instant validation and balance tracking
- Automatic multi-currency conversion alongside ledger records

**Budget Management**
- Set per-category spending limits
- Over-budget warning before committing a transaction
- Proactive alerts when spending reaches 90% (warning) or 100% (critical) of any budget limit
- One-click category reset (clears transactions and limit together)
- Add unlimited custom categories beyond the 8 built-in defaults

**Analytics**
- 3-mode interactive chart window with optional period filtering:
  - Spending Distribution — pie chart of actual spend (click a slice to drill down into its transactions)
  - Budget Allocation — pie chart of planned limits (click a slice to view category transactions)
  - Budget vs. Actual — horizontal bar chart comparing both

**Currency**
- Supports USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR
- Multi-provider live currency rate engine: Primary (`ExchangeRate-API`) + Secondary live fallback (`Frankfurter API` / `api.frankfurter.dev`)
- Falls back to local JSON cache or static rates when offline with descriptive UI network indicators
- One-click account currency conversion (recalculates all stored amounts, templates, and savings goals)

**Security & Account Management**
- PBKDF2-HMAC-SHA256 (600,000 iterations) with a random 16-byte salt per account
- Constant-time hash comparison (`hmac.compare_digest`) against timing attacks
- 3 failed login attempts → 30-second lockout
- Password policy: min 8 chars, at least one uppercase, lowercase, and digit
- **Mandatory Password Recovery**: Hashed security question & answer required on registration to reset forgotten passwords
- In-app password change requiring current password verification, new password distinct from current, and re-hashing
- Multi-account support with per-account switch authentication

**Data, Backups & Export**
- Atomic JSON writes (temp file + `os.replace`) — no partial writes on crash
- Corrupt database auto-backed up to `.corrupt.bak` before recovery
- Automated timestamped backup (`backups/Database_backup_YYYY-MM-DD_HHMMSS.json`) created on every graceful exit with auto-rotation (keeps last 10 backups)
- One-click CSV export with optional monthly period filtering

---

## Getting Started

```bash
git clone git@github.com:Mounir-code09/User-Expense.git
cd User-Expense
pip install customtkinter CTkMessagebox matplotlib requests pytest pytest-cov
python mainEXE.py
```

---

## Project Structure

```
User-Expense/
├── mainEXE.py                  # Entry point
├── Database.json               # Local JSON store (auto-created)
├── last_known_rates.json       # Exchange rate cache (auto-created)
├── backups/                    # Auto-rotating timestamped backups (git-ignored)
│
├── core/
│   ├── gui_app.py              # Main window, metric cards, period selector, theme sync
│   ├── ui_actions.py           # Button handlers, modal orchestration, budget alerts
│   ├── modals.py               # Auth, entries, templates, password change, bank import dialogs
│   ├── chart_viewer.py         # 3-in-1 Matplotlib analytics window with slice drill-downs
│   ├── user.py                 # User profile, transactions, templates, budgets, budget alerts
│   ├── expense_tracker.py      # Report generation, remove-expense logic, QIF/OFX parser
│   ├── security.py             # Hashing, lockout, auth, password changes
│   ├── data_manager.py         # JSON I/O, atomic saves, schema migration, timestamped backups
│   ├── currency_service.py     # Live rate fetching, caching, conversion, error tracking
│   ├── exceptions.py           # Domain exception hierarchy
│   ├── theme.py                # Color palette constants, format_amount(), OS theme detection
│   └── __init__.py
│
└── Tests/
    ├── __init__.py
    ├── test_exceptions.py
    ├── test_data_manager.py
    ├── test_user.py
    ├── test_expense_tracker.py
    ├── test_currency_service.py
    ├── test_security.py
    └── test_statement_parser.py
```

---

## Architecture

```
┌──────────────────────────────────────────┐
│              GUI Layer                   │
│  gui_app · ui_actions · modals · chart   │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│           Business Layer                 │
│  user · expense_tracker · security       │
│  exceptions · currency_service           │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│          Persistence Layer               │
│            data_manager                  │
└───────────────────┬──────────────────────┘
                    │
                    ▼
              Database.json
```

---

## Testing

```bash
# All tests
python -m pytest Tests/ -v

# With coverage
python -m pytest Tests/ -v --cov=core --cov-report=term-missing
```

81+ unit tests across 8 test modules verifying domain logic, period calculations, future date guards, pre-1970 date bounds, recurring templates, auth security, password recovery, savings goals, QIF/OFX parsing, timestamped backups, budget alert thresholds, and edge cases.

---

## Security Notes

| Property | Detail |
|---|---|
| Hash algorithm | PBKDF2-HMAC-SHA256 |
| Iterations | 600,000 |
| Salt | 16-byte random (`secrets.token_hex`) |
| Comparison | `hmac.compare_digest` (constant-time) |
| Lockout | 3 attempts → 30s block |
| Password policy | ≥8 chars, upper + lower + digit |
| Password change | Requires current password verification + distinct new password + re-hashing |
| Account recovery | Hashed security question + answer verified via constant-time comparison |
