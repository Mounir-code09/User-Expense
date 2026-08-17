import pytest
from core.user import User
from core.expense_tracker import ExpenseTracker
from core.data_manager import DEFAULT_CATEGORIES
from core.exceptions import InvalidAmountError, InvalidCategoryError


@pytest.fixture
def test_tracker(monkeypatch):
    db = {
        "users": {
            "Bob": {
                "currency": "USD",
                "categories": DEFAULT_CATEGORIES.copy(),
                "budget_limits": {"food": 100.0, "transport": 50.0},
                "transactions": [
                    {"id": "tx_1", "date": "2026-08-01", "category": "food", "amount": 30.0, "note": "Lunch"},
                    {"id": "tx_2", "date": "2026-08-02", "category": "transport", "amount": 65.0, "note": "Train"},
                ],
                "incomes": [
                    {"id": "inc_1", "date": "2026-08-01", "source": "Salary", "amount": 2500.0, "note": "Paycheck"},
                ],
                "password_hash": "ab:cd",
                "failed_attempts": 0,
                "lockout_until": 0,
            }
        }
    }
    monkeypatch.setattr("core.data_manager.load_database", lambda: db)
    monkeypatch.setattr("core.data_manager.save_database", lambda data: db.update(data))
    return ExpenseTracker(User("Bob"))


def test_add_expense_accumulates(test_tracker):
    test_tracker.add_expense("food", 20.50, note="Snacks")
    assert test_tracker.expense_report["food"] == 50.50
    assert test_tracker.total_expenses_of_user() == 115.50


def test_backward_compat_expenseReport(test_tracker):
    assert test_tracker.expenseReport["food"] == 30.0


def test_remove_expense_subtracts(test_tracker):
    test_tracker.remove_expense("food", 10.0)
    assert test_tracker.expense_report["food"] == 20.0


def test_remove_expense_float_precision(test_tracker):
    # Add exactly the same amount we'll remove (float representation edge case)
    test_tracker.user.transactions.append(
        {"id": "tx_edge", "date": "2026-08-03", "category": "food", "amount": 0.1, "note": ""}
    )
    current = test_tracker.expense_report["food"]
    # Should not raise — rounded comparison must accept exact amounts
    test_tracker.remove_expense("food", current)


def test_remove_expense_rejects_invalid(test_tracker):
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        test_tracker.remove_expense("food", 0)
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        test_tracker.remove_expense("food", -5)
    with pytest.raises(InvalidAmountError, match="only"):
        test_tracker.remove_expense("food", 50.0)


def test_status_report_contains_expected_fields(test_tracker):
    report = test_tracker.get_status_report()
    assert "Food" in report
    assert "✅ OK" in report
    assert "Transport" in report
    assert "❌ OVER" in report
    assert "Total Spent:" in report
    assert "Total Income:" in report
    assert "Net Savings:" in report


def test_add_expense_rejects_invalid_inputs(test_tracker):
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        test_tracker.add_expense("food", 0)
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        test_tracker.add_expense("food", -10)
    with pytest.raises(InvalidCategoryError, match="not a recognized category"):
        test_tracker.add_expense("unregistered_category", 50.0)
