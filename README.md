# 📊 Multi-Currency Expense Tracker & Financial Dashboard

A robust, modern desktop application built with **Python**, **CustomTkinter**, and **Matplotlib** designed to track personal expenses, manage category-specific budget limits, and handle real-time multi-currency conversions with offline fallback support.

---

## 🚀 Key Features

1. **Modern Graphical User Interface**: Built with CustomTkinter using a responsive single-root architecture and a vibrant, theme-aware startup card interface.
2. **Real-Time Multi-Currency Support**: Integrates live exchange rates via background asynchronous polling, complete with socket-based connectivity checks and static fallback rates for offline use.
3. **Smart Budget Management**: Set, check, and purge budget limits per category with built-in over-budget warning prompts.
4. **Data Visualization**: Clean, embedded Matplotlib pie charts displaying expense breakdowns dynamically adjusted for light and dark system themes.
5. **Multi-User Profile System**: Securely manage multiple user profiles with isolated data structures and persistent records.
6. **Atomic Data Persistence**: JSON-based database storage utilizing atomic file replacement (`.tmp` file renaming) to prevent data corruption.

---

## 📂 Project Architecture

The core logic is modularly organized into the `core/` package:

| Module | Description |
| --- | --- |
| `gui_app.py` | Manages the single-root application lifecycle, the vibrant startup authentication frame, and the main dashboard grid. |
| `ui_actions.py` | Handles event controllers, modal popups, custom dropdown inputs, and UI message notifications. |
| `user.py` | Manages user profile entities, budget thresholds, and native portfolio currency transformations. |
| `expense_tracker.py` | Handles transaction updates, budget limit comparisons, and plain-text financial status report generation. |
| `data_manager.py` | Manages JSON database persistence, file loading/saving, and category string validation. |
| `currency_service.py` | Manages live exchange rate requests, background threads, socket-based network drop detection, and cross-rate calculations. |
| `chart_viewer.py` | Object-oriented Matplotlib pie chart embedder using the Figure API to avoid global pyplot overhead. |

---

## 🧪 Testing Suite

The project includes a comprehensive test suite powered by **pytest**, covering core components, edge cases, and failure handling logic.

1. **`test_currency_service.py`**: Validates live conversion math, fallback dictionary triggers, and offline failure threshold logic.
2. **`test_data_manager.py`**: Tests database loading behavior, category string validation rules, user saving/loading, and cleanup operations.
3. **`test_expense_tracker.py`**: Tests expense accumulation totals, aggregate spending calculations, and status table report formatting.
4. **`test_user.py`**: Validates `User_class` initialization, negative budget boundary constraints, and container management.

To run the test suite locally: python -m pytest



## 🛠️ Installation & Getting Started

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker

```


2. **Install dependencies:**
```bash
pip install customtkinter CTkMessagebox matplotlib requests pytest

```


3. **Run the application:**
```python
from core.gui_app import start_app

if __name__ == "__main__":
    start_app("Database.json")

```