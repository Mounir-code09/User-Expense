"""
ExpenseTracker Logic Testing Architecture
"""
import pytest
from unittest.mock import Mock
from User import User_class
from Expense_tracker import ExpenseTracker

@pytest.fixture
def mock_tracker_env():
    user = Mock(spec=User_class)
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

def test_total_expenses_of_user(mock_tracker_env):
    assert mock_tracker_env.total_expenses_of_user() == 95.0

def test_status_report_formatting(mock_tracker_env):
    report = mock_tracker_env.get_status_report()
    assert "Food" in report
    assert "✅ OK" in report
    assert "Transport" in report
    assert "❌ OVER" in report