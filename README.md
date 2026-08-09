# 💰 Multi-Currency Expense Tracker

A modern desktop application for **personal expense tracking, category-based budgeting, multi-currency conversion, and financial data visualization**.

Built with **Python, CustomTkinter, Matplotlib, and JSON**, the application follows a layered architecture with separated GUI, business logic, persistence, security, and external-service responsibilities.

---

## ✨ Core Features

### 🎨 Modern Desktop GUI

* Built with **CustomTkinter**
* Centralized theme and color management
* Adaptive light/dark appearance
* Reusable modal dialogs
* Clean separation between interface and application logic

### 💱 Multi-Currency Support

* Supports **USD, EUR, GBP, JPY, and CAD**
* Fetches live exchange rates from `exchangerate-api.com`
* Performs currency conversion automatically
* Uses static fallback rates when the network is unavailable
* Background rate fetching prevents network requests from blocking the GUI

### 📊 Budget Management

* Set spending limits for individual categories
* Track spending against category budgets
* Detect and warn when budgets are exceeded
* Purge category data when required
* Validate categories and budget values at the business-logic level

### 📈 Data Visualization

* Generates expense breakdowns using **Matplotlib**
* Displays category spending through embedded pie charts
* Uses Matplotlib's object-oriented API
* Properly disposes figures when chart windows are closed

### 👥 Multi-User Profiles

* Independent financial profiles for each user
* Separate expenses, budgets, and preferred currencies
* Username normalization for consistent lookups
* Password-protected accounts
* User creation, deletion, switching, and authentication

### 🔒 Secure Local Persistence

* Passwords are never stored in plaintext
* Passwords are protected using **PBKDF2-HMAC-SHA256**
* Each account receives a unique cryptographic salt
* Database writes use temporary-file replacement to reduce corruption risk
* User deletion removes associated credentials and financial data

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
```

## 2. Install Dependencies

```bash
pip install customtkinter CTkMessagebox matplotlib requests pytest
```

## 3. Run the Application

```bash
python mainEXE.py
```

The application can also be launched programmatically:

```python
from core.gui_app import start_app

start_app("Database.json")
```

---

# 🏛️ Architecture

The project follows a **layered separation-of-concerns architecture**.

The application is divided into four primary responsibilities:

```text
┌─────────────────────────────┐
│          GUI Layer          │
│ gui_app.py / ui_actions.py │
│         modals.py           │
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

External services such as currency-rate retrieval operate independently from the main application flow.

---

# 📁 Project Structure

```text
expense-tracker/
│
├── mainEXE.py
├── Database.json
│
├── core/
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

# 🧩 Module Responsibilities

### `mainEXE.py`

Application entry point.

Its responsibility is limited to launching the application:

```python
start_app("Database.json")
```

No business logic is implemented here.

### `gui_app.py`

Contains `ExpenseApp`, the application's root window and lifecycle manager.

Responsible for:

* Application startup
* Login flow
* Dashboard initialization
* Welcome screen
* Dashboard transitions
* Network-status monitoring
* Application shutdown

### `ui_actions.py`

Contains `UIActions`, the bridge between the dashboard interface and the business layer.

Responsible for:

* Handling dashboard actions
* Collecting user input
* Performing initial input validation
* Calling the appropriate business-layer operations

UIActions does **not** implement reusable modal windows. Dialog presentation is handled by `modals.py`.

### `modals.py`

Contains reusable modal dialogs built around a shared `BaseModal`.

Includes:

* `SignInModal`
* `SignUpModal`
* `SwitchAccountModal`
* `CTkInputModal`
* `CTkDropdownDialog`

`SwitchAccountModal` supports an optional `current_user` parameter and can automatically detect the active user from the master window.

It also prevents the currently logged-in user from appearing as a switch-account option.

### `user.py`

Defines the user's financial profile and cross-profile management.

Main responsibilities:

* User profile representation
* Preferred currency
* Category budgets
* Expense ownership
* User lookup
* User deletion
* User listing
* Profile-level validation

The module provides:

* `User`
* `Users`

### `expense_tracker.py`

Contains `ExpenseTracker`, the primary business-layer interface for modifying and analyzing expenses.

Responsibilities:

* Add expenses
* Remove expenses
* Calculate totals
* Search expenses
* Generate spending status reports
* Validate expense data
* Prevent invalid financial mutations

### `data_manager.py`

Provides the persistence layer for the JSON database.

Responsibilities:

* Loading database records
* Saving records
* Creating and deleting users
* Category validation
* Username normalization
* Default-user templates
* Atomic database writes

`data_manager.py` defines the canonical set of valid expense categories used throughout the application.

### `security.py`

Contains `SecurityManager`, responsible for authentication and password security.

Responsibilities:

* Password hashing
* Password verification
* Registration validation
* Password-strength enforcement
* Failed-login tracking
* Temporary account lockout

### `currency_service.py`

Provides currency conversion and exchange-rate management.

Responsibilities:

* Fetch live exchange rates
* Perform currency conversion
* Maintain fallback exchange rates
* Detect offline/unavailable services
* Retrieve rates without blocking the GUI
* Protect shared rate data using thread synchronization

### `chart_viewer.py`

Contains `ChartViewer`, responsible for financial visualization.

Uses Matplotlib's object-oriented API to:

* Generate expense pie charts
* Embed charts inside the application
* Manage chart windows
* Dispose of Matplotlib figures correctly

### `theme.py`

Centralized visual configuration.

Defines:

* Application surfaces
* Text colors
* Button colors
* Chart colors
* Light/dark appearance mappings

This prevents individual modules from maintaining conflicting visual styles.

---

# 🔄 Application Data Flow

A typical expense operation follows this path:

```text
User interaction
       │
       ▼
   GUI Layer
       │
       ▼
   ui_actions.py
   Input validation
       │
       ▼
Business Layer
user.py / expense_tracker.py
       │
       ▼
data_manager.py
       │
       ▼
Atomic JSON write
       │
       ▼
Database.json
```

For currency conversion:

```text
User requests conversion
          │
          ▼
currency_service.py
          │
     ┌────┴────┐
     ▼         ▼
Live API    Fallback
     │         │
     └────┬────┘
          ▼
    Converted amount
```

---

# 🛡️ Validation & Defence in Depth

Input validation is intentionally performed at multiple layers.

The GUI performs the **first level of validation** to provide immediate feedback to the user.

The business layer independently validates the same data before modifying application state.

This prevents invalid data from entering the system if the business logic is called through another interface, such as:

* Unit tests
* Scripts
* Future APIs
* Other GUI components
* Direct programmatic calls

The principle is:

> **The GUI validates for usability; the business layer validates for correctness.**

---

# 🔐 Security Model

User passwords are never stored in plaintext.

Each password is processed using:

**PBKDF2-HMAC-SHA256**

with:

* **100,000 iterations**
* **16-byte unique salt**
* Derived password hash stored alongside the salt

The resulting credential representation is stored in the user's record within `Database.json`.

### Password Requirements

Passwords must contain:

* At least 8 characters
* At least one uppercase letter
* At least one lowercase letter
* At least one digit

### Brute-Force Protection

After **3 consecutive failed login attempts**, the account is temporarily locked for **30 seconds**.

### Local-First Security Model

The application is designed as a local-first desktop application, so credentials and financial data are maintained in the local JSON database.

Advantages include:

* Simple backup
* No mandatory server
* No remote database dependency
* Single-file data management

Deleting a user also removes their stored credentials and financial data.

---

# 💾 Persistence & Data Integrity

Financial data is stored in:

```text
Database.json
```

Database operations are centralized in `data_manager.py`.

Writes use a **temporary-file replacement strategy** rather than directly overwriting the existing database.

Conceptually:

```text
Database.json
     │
     ▼
Write temporary file
     │
     ▼
Complete write successfully
     │
     ▼
Replace original database
```

This reduces the likelihood of leaving the database partially written if the application crashes during a save operation.

---

# 🧪 Testing

The project includes a `pytest` test suite covering core functionality, security, persistence, currency conversion, and edge cases.

### `test_DataManager.py`

Tests:

* Database loading and saving
* Category validation
* Username normalization
* User deletion

### `test_User.py`

Tests:

* Profile initialization
* Budget management
* Budget limits
* Category purging
* User-container operations
* Invalid category handling
* Invalid currency handling

### `test_ExpenseTracker.py`

Tests:

* Expense accumulation
* Negative amount rejection
* Status reports
* Invalid category rejection
* Zero-total cleanup

### `test_currency_service.py`

Tests:

* Currency conversion mathematics
* Fallback exchange rates
* Offline detection
* Same-currency conversion
* Rounding behavior

### `test_security.py`

Tests:

* Password hashing
* Password verification
* Registration
* Login
* User deletion
* Account lockout

### Run the Test Suite

```bash
python -m pytest Tests/ -v
```

---

# 🏷️ Expense Categories

The application currently supports:

```text
food
transport
housing
entertainment
shopping
health
education
miscellaneous
```

Category identifiers are normalized to lowercase internally to ensure consistent lookups and validation.

---

# 💱 Supported Currencies

The application currently supports:

```text
USD
EUR
GBP
JPY
CAD
```

Exchange rates are retrieved from:

```text
exchangerate-api.com
```

When the external service is unavailable, the application automatically falls back to predefined static exchange rates.

---

# 🎯 Design Principles

The project is built around several core principles:

### Separation of Concerns

GUI, business logic, persistence, security, and external services remain independently organized.

### Defence in Depth

Critical validation is repeated at the business layer rather than trusting GUI input alone.

### Fail-Safe Persistence

Database writes use atomic replacement to reduce corruption risk.

### Offline Resilience

Currency conversion remains functional when live exchange-rate retrieval is unavailable.

### Reusability

Common UI components, dialogs, themes, and business operations are centralized rather than duplicated.

### Testability

Core application logic is separated from the GUI so it can be tested independently.

---

# 📌 Project Scope

The application provides a complete local desktop environment for managing personal expenses across multiple users and currencies.

Its current scope includes:

* Multi-user authentication
* Secure local password storage
* Expense tracking
* Category budgets
* Budget-limit monitoring
* Expense searching
* Financial summaries
* Expense visualization
* Currency conversion
* Offline exchange-rate fallback
* Atomic JSON persistence
* Automated unit testing
* Light/dark GUI theming

The architecture is intentionally modular so additional features—such as new currencies, database backends, reporting systems, or alternative interfaces—can be introduced without tightly coupling them to the existing GUI.
