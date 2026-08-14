"""Expense tracking calculations, status reporting, and adjustment tests."""
import pytest
from core.user import User
from core.expense_tracker import ExpenseTracker
from core.data_manager import DEFAULT_CATEGORIES


@pytest.fixture
def test_tracker(monkeypatch):
    db_store = {
        "users": {
            "Bob": {
                "currency": "USD",
                "categories": DEFAULT_CATEGORIES.copy(),
                "budget_limits": {"food": 100.0, "transport": 50.0},
                "transactions": [
                    {"id": "tx_1", "date": "2026-08-01", "category": "food", "amount": 30.0, "note": "Lunch"},
                    {"id": "tx_2", "date": "2026-08-02", "category": "transport", "amount": 65.0, "note": "Train"},
                ],
                "password_hash": "ab:cd",
                "failed_attempts": 0,
                "lockout_until": 0,
            }
        }
    }
    monkeypatch.setattr("core.data_manager.load_database", lambda: db_store)
    monkeypatch.setattr("core.data_manager.save_database", lambda data: db_store.update(data))
    user = User("Bob")
    return ExpenseTracker(user)


def test_add_expense_accumulates_total(test_tracker):
    tracker = test_tracker
    tracker.add_expense("food", 20.50, note="Snacks")
    assert tracker.expenseReport["food"] == 50.50
    assert tracker.total_expenses_of_user() == 115.50


def test_remove_expense_subtracts_from_total(test_tracker):
    tracker = test_tracker
    tracker.remove_expense("food", 10.0)
    assert tracker.expenseReport["food"] == 20.0


def test_remove_expense_rejects_exceeding_or_negative(test_tracker):
    tracker = test_tracker
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.remove_expense("food", 0)
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.remove_expense("food", -5)
    with pytest.raises(ValueError, match="only"):
        tracker.remove_expense("food", 50.0)


def test_status_report_formatting(test_tracker):
    report = test_tracker.get_status_report()
    assert "Food" in report
    assert "✅ OK" in report
    assert "Transport" in report
    assert "❌ OVER" in report
    assert "Total Spent:" in report


def test_add_expense_rejects_invalid_inputs(test_tracker):
    tracker = test_tracker
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.add_expense("food", 0)
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.add_expense("food", -10)
    with pytest.raises(ValueError, match="not a recognized category"):
        tracker.add_expense("unregistered_category", 50.0)
