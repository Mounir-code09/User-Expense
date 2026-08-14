"""Domain exception hierarchy tests."""
import pytest
from core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    CategoryAlreadyExistsError,
    ExpenseTrackerError,
    InvalidAmountError,
    InvalidCategoryError,
    PasswordValidationError,
)


def test_exception_inheritance():
    """Verify all domain exceptions inherit from ExpenseTrackerError."""
    assert issubclass(InvalidCategoryError, ExpenseTrackerError)
    assert issubclass(CategoryAlreadyExistsError, ExpenseTrackerError)
    assert issubclass(InvalidAmountError, ExpenseTrackerError)
    assert issubclass(AccountLockedError, ExpenseTrackerError)
    assert issubclass(AuthenticationError, ExpenseTrackerError)
    assert issubclass(PasswordValidationError, ExpenseTrackerError)


def test_exception_messages():
    """Verify exceptions format custom error messages cleanly."""
    err = InvalidCategoryError("Unrecognized category: travel")
    assert str(err) == "Unrecognized category: travel"

    amount_err = InvalidAmountError("Expense amount must be greater than zero.")
    assert str(amount_err) == "Expense amount must be greater than zero."
