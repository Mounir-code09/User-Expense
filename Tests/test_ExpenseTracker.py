"""
ExpenseTracker Logic Tests
==========================

Validates :class:`core.expense_tracker.ExpenseTracker`.
"""
import pytest
from unittest.mock import Mock
from core.expense_tracker import ExpenseTracker


@pytest.fixture
def mock_tracker_env():
    user = Mock()
    user.name = "Bob"
    user.currency = "USD"
    user.budget_limit = {"food": 100.0, "transport": 50.0}
    user.current_expenses = {"food": 30.0, "transport": 65.0}
    user.save = Mock()
    return ExpenseTracker(user)


def test_add_expense_accumulates_total(mock_tracker_env):
    tracker = mock_tracker_env
    new_total = tracker.add_expense("food", 20.50)

    assert new_total == 50.50
    assert tracker.expenseReport["food"] == 50.50
    tracker.user.save.assert_called_once()


def test_remove_expense_rejects_non_positive_amount(mock_tracker_env):
    tracker = mock_tracker_env
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.remove_expense("food", 0)
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.remove_expense("food", -10)


def test_status_report_formatting(mock_tracker_env):
    report = mock_tracker_env.get_status_report()
    assert "Food" in report
    assert "✅ OK" in report
    assert "Transport" in report
    assert "❌ OVER" in report


def test_add_expense_rejects_non_positive_amount(mock_tracker_env):
    tracker = mock_tracker_env
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.add_expense("food", 0)
    with pytest.raises(ValueError, match="greater than zero"):
        tracker.add_expense("food", -5)


def test_add_expense_rejects_invalid_category(mock_tracker_env):
    tracker = mock_tracker_env
    with pytest.raises(ValueError, match="not a recognized expense category"):
        tracker.add_expense("rent", 50.0)


def test_remove_expense_rejects_invalid_category(mock_tracker_env):
    tracker = mock_tracker_env
    with pytest.raises(ValueError, match="not a recognized expense category"):
        tracker.remove_expense("rent", 10.0)


def test_remove_expense_cleans_up_zero_totals(mock_tracker_env):
    tracker = mock_tracker_env
    tracker.remove_expense("food", 30.0)
    assert "food" not in tracker.expenseReport