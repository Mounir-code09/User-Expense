# 💰 Multi-Currency Expense & Financial Tracker

A modern desktop application for **personal expense tracking, category budgeting with visual progress bars, income & net savings tracking, multi-currency conversion, transaction ledgers, and visual analytics**.

Built with **Python, CustomTkinter, Matplotlib, and JSON**, the application features a layered architecture with clean separation between the GUI, business layer, persistence, security, domain exceptions, and live currency exchange services.

---

## ✨ Core Features

### 🎨 Modern Desktop Dashboard
* Built with **CustomTkinter** with light and dark mode adaptation.
* **4 Live Metric Cards**: Real-time summary of Total Expenses, Total Income, Net Savings, and Remaining Budget directly on the main window.
* **Category Budget Progress Bars**: Real-time progress bars for each configured budget category color-coded for safety (Green $< 75\%$, Warning Orange $75\% - 100\%$, Red $> 100\%$).

### 💰 Income & Net Savings Tracking
* Record income sources (Salary, Freelance, Investments, Business, Gifts, Other) with amounts, notes, and dates.
* Automatic real-time calculation of **Net Savings** (`Income − Expenses`) and **Savings Rate %**.
* Dedicated **Income History** ledger with search and deletion.

### 📜 Expense Transaction Ledger with Notes & Dates
* Record individual transactions with **Category, Amount, Date (`YYYY-MM-DD`), and Note/Description**.
* **Interactive Transaction History**: Scrollable ledger with real-time search across notes and categories.
* **Transaction Deletion**: Delete individual entries directly from the history ledger.

### 📊 3-Way Interactive Visual Analytics
* Embedded **Matplotlib** analytics window with an interactive segmented toggle:
  * 🍩 **Spending Distribution (Pie Chart)**: Percentage and amount distribution of actual spending.
  * 🎯 **Budget Allocation (Pie Chart)**: Percentage and amount distribution of planned budgets.
  * 📊 **Budget vs. Actual (Bar Chart)**: Side-by-side comparison bars showing planned limits vs. actual spending.

### 🏷️ Custom Category Management
* Preloaded with canonical categories (`food`, `transport`, `housing`, `entertainment`, `shopping`, `health`, `education`, `miscellaneous`).
* Add unlimited custom categories tailored to your personal finances.

### 📥 CSV Spreadsheet Export
* Export full financial records (Expenses and Incomes with Type, ID, Date, Category/Source, Amount, Currency, Note) to a `.csv` file with a single click.

### 💱 Multi-Currency Support & Live Exchange Rates
* Supports **USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, and more**.
* Non-blocking background rate fetching from `exchangerate-api.com`.
* Persistent local cache and static fallbacks keep the application fully operational offline.

### 🔒 Secure Authentication & Local Persistence
* Accounts protected with **PBKDF2-HMAC-SHA256** (600,000 iterations) password hashing and unique cryptographic salts (`secrets.token_hex`).
* Constant-time hash verification (`hmac.compare_digest`) to prevent timing attacks.
* Automatic 30-second lockout after 3 consecutive failed login attempts.
* Atomic temporary-file replacement for JSON persistence with automatic `.corrupt.bak` recovery.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone git@github.com:Mounir-code09/User-Expense.git
cd User-Expense
```

### 2. Install Dependencies

```bash
pip install customtkinter CTkMessagebox matplotlib requests pytest pytest-cov
```

### 3. Launch the Application

```bash
python main.py
```

---

## 🏛️ Architecture

```text
┌──────────────────────────────────────────────┐
│                  GUI Layer                   │
│   gui_app.py / ui_actions.py / modals.py     │
│               chart_viewer.py                │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                Business Layer                │
│ user.py / expense_tracker.py / security.py   │
│                exceptions.py                 │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              Persistence Layer               │
│               data_manager.py                │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
                 Database.json
```

---

## 📁 Project Structure

```text
User_Expenses/
│
├── main.py                     # Canonical application entry point
├── mainEXE.py                  # Launcher alias
├── Database.json               # Local JSON database
├── README.md
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI workflow
│
├── core/
│   ├── __init__.py
│   ├── gui_app.py              # Main window, metric cards, progress bars
│   ├── ui_actions.py           # Dashboard actions and event handlers
│   ├── modals.py               # Sign In, Sign Up, Expense/Income entry, Ledgers
│   ├── user.py                 # User profile, transactions, incomes, savings
│   ├── expense_tracker.py      # Business logic and status table reports
│   ├── exceptions.py           # Custom domain exceptions
│   ├── data_manager.py         # JSON storage, atomic saves, corrupt recovery
│   ├── security.py             # PBKDF2 hashing, timing-safe checks, lockouts
│   ├── currency_service.py     # Threaded live rate updates, offline fallbacks
│   ├── chart_viewer.py         # 3-in-1 interactive visual analytics
│   └── theme.py                # Centralized color palettes & formatting
│
└── Tests/
    ├── test_exceptions.py      # Domain exception hierarchy tests
    ├── test_data_manager.py    # Database & migration tests
    ├── test_user.py            # User, transactions, incomes, savings, CSV tests
    ├── test_expense_tracker.py # Expense calculations & status reports
    ├── test_currency_service.py# Live rates, caching, and conversion math
    └── test_security.py        # Hashing, strength rules, and lockouts
```

---

## 🧪 Testing

Run all unit tests with pytest:

```bash
python -m pytest Tests/ -v
```

Run test suite with coverage report:

```bash
python -m pytest Tests/ -v --cov=core --cov-report=term-missing
```

---

## 🔐 Security & Lockout Policy

* **Hashing Algorithm**: PBKDF2-HMAC-SHA256 with 600,000 iterations and a 16-byte random salt.
* **Verification**: Constant-time comparison (`hmac.compare_digest`).
* **Password Complexity**: Minimum 8 characters, requiring at least one uppercase letter, one lowercase letter, and one digit.
* **Brute-Force Lockout**: 3 failed login attempts lock the account for 30 seconds.
