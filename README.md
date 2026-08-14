# 💰 Multi-Currency Expense Tracker

A modern desktop application for **personal expense tracking, category-based budgeting, multi-currency conversion, and financial data visualization**.

Built with **Python, CustomTkinter, Matplotlib, and JSON**, the application follows a clean layered architecture with separated GUI, business logic, persistence, security, and external-service responsibilities.

---

## ✨ Core Features

### 🎨 Modern Desktop GUI
* Built with **CustomTkinter**
* Centralized theme and color management
* Adaptive light/dark appearance
* Reusable modal dialogs
* Clean separation between interface and application logic

### 💱 Multi-Currency Support
* Supports **USD, EUR, GBP, JPY, CAD, and more**
* Live exchange rates fetched in background threads from `exchangerate-api.com`
* Automatic local disk caching for offline resilience
* Static fallback rates ensure the app remains functional without internet connectivity

### 📊 Budget Management
* Set spending limits for individual categories
* Track spending against category budgets
* Detect and warn when transactions exceed budgets
* Reset category data (budgets and spending) on demand
* Multi-layer validation at both GUI and business-logic levels

### 📈 Data Visualization
* Generates expense breakdowns using **Matplotlib**
* Displays category spending through embedded charts
* Uses Matplotlib's object-oriented API with automatic figure disposal

### 👥 Multi-User Profiles
* Independent financial profiles for each user
* Separate expenses, budgets, and preferred currencies
* Username normalization for consistent lookups
* Password-protected accounts with PBKDF2-HMAC-SHA256 hashing
* Brute-force protection with temporary lockouts

### 🔒 Safe Local Persistence
* Data stored in JSON with atomic temporary-file replacement
* Automatic backup creation on corrupted database detection
* No plain-text passwords or exposed sensitive tokens

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Mounir-code09/User-Expense.git
cd User-Expense
```

### 2. Install Dependencies

```bash
pip install customtkinter CTkMessagebox matplotlib requests pytest pytest-cov
```

### 3. Run the Application

```bash
python mainEXE.py
```

Or run programmatically:

```python
from core.gui_app import start_app

start_app("Database.json")
```

---

## 🏛️ Architecture

The project follows a **layered separation-of-concerns architecture**:

```text
┌─────────────────────────────┐
│          GUI Layer          │
│ gui_app.py / ui_actions.py  │
│ modals.py / chart_viewer.py │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Business Layer        │
│ user.py / expense_tracker.py│
│         security.py         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Persistence Layer      │
│       data_manager.py       │
└──────────────┬──────────────┘
               │
               ▼
          Database.json
```

---

## 📁 Project Structure

```text
User_Expenses/
│
├── mainEXE.py
├── Database.json
├── README.md
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── core/
│   ├── __init__.py
│   ├── gui_app.py
│   ├── ui_actions.py
│   ├── modals.py
│   ├── user.py
│   ├── expense_tracker.py
│   ├── data_manager.py
│   ├── security.py
│   ├── currency_service.py
│   ├── chart_viewer.py
│   └── theme.py
│
└── Tests/
    ├── test_DataManager.py
    ├── test_User.py
    ├── test_ExpenseTracker.py
    ├── test_currency_service.py
    └── test_security.py
```

---

## 🧩 Module Responsibilities

| Module | Primary Responsibility |
| :--- | :--- |
| `mainEXE.py` | Application entry point that boots `ExpenseApp`. |
| `core/gui_app.py` | Root window lifecycle, startup screens, session switching, and dashboard UI. |
| `core/ui_actions.py` | Maps dashboard buttons to business logic with input dialogs and validations. |
| `core/modals.py` | Reusable centered modal dialogs for sign-in, registration, and user inputs. |
| `core/user.py` | User financial profile representation, currency changes, and category resets. |
| `core/expense_tracker.py` | Business logic for adding/removing expenses and formatting financial reports. |
| `core/data_manager.py` | Persistence helpers, atomic JSON replacement, category validation, and corrupt DB backups. |
| `core/security.py` | PBKDF2 password hashing, constant-time verification, password rules, and lockout tracking. |
| `core/currency_service.py` | Threaded live rate fetching, persistent disk cache, and multi-currency conversions. |
| `core/chart_viewer.py` | Matplotlib pie chart visualization with appearance theme integration. |
| `core/theme.py` | Palette constants for light and dark modes. |

---

## 🔐 Security & Lockout Policy

* **Hashing Algorithm**: PBKDF2-HMAC-SHA256 with 100,000 iterations and a unique 16-byte cryptographic salt per user.
* **Timing Protection**: Password verification uses constant-time comparison (`hmac.compare_digest`).
* **Password Policy**: Minimum 8 characters with at least one uppercase letter, one lowercase letter, and one digit.
* **Brute-Force Lockout**: 3 consecutive failed login attempts trigger a 30-second lockout period for the account.

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
python -m pytest Tests/ -v
```

To run with coverage:

```bash
python -m pytest Tests/ -v --cov=core --cov-report=term-missing
```

---

## 🏷️ Supported Categories & Currencies

* **Categories**: `food`, `transport`, `housing`, `entertainment`, `shopping`, `health`, `education`, `miscellaneous`.
* **Currencies**: `USD`, `EUR`, `GBP`, `JPY`, `CAD`, `AUD`, `CHF`, `CNY`, `INR`.
