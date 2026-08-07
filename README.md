# Multi-User Personal Finance & Expense Tracker

A modern, desktop-based personal finance management system engineered in Python. The application provides dynamic multi-user profile separation, real-time budget thresholding across dynamic categories, automatic precision multi-currency conversions, and an interactive graphical user interface built with CustomTkinter. 

This repository leverages an automated validation pipeline via `pytest` to ensure structural mathematical accuracy and file-system transaction integrity.

---

## ✨ Features

*   **Dynamic Multi-User Accounts:** Instantly swap between separate profiles managed on a proxy-based lookup architecture without data overhead.
*   **Atomic JSON Data Engine:** Multi-stage file transactions that safeguard database records against truncation or sudden power loss corruptions.
*   **Robust Category Whitelisting:** Input validation protecting budget boundaries against arbitrary naming inputs.
*   **Precision Currency Conversion Engine:** Seamlessly converts inputs across `USD`, `EUR`, `GBP`, `JPY`, and `CAD` using isolated arithmetic verification down to two decimal places.
*   **Visual Status Alert Matrix:** Instant visual text dashboards flagging category-specific parameters (`✅ OK` vs `❌ OVER`) upon expense recording.
*   **Comprehensive Test Coverage:** Driven completely by automated mocks keeping physical disc structures clean during unit test runtime pipelines.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8 or higher
*   Git installed on your system

### Installation & Execution

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/yourusername/User_Expenses.git](https://github.com/yourusername/User_Expenses.git)
   cd User_Expenses