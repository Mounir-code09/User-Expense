from core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    CategoryAlreadyExistsError,
    ExpenseTrackerError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    PasswordValidationError,
)


def test_all_inherit_from_base():
    for exc_class in (
        InvalidCategoryError, CategoryAlreadyExistsError, InvalidAmountError,
        InvalidDateError, AccountLockedError, AuthenticationError, PasswordValidationError,
    ):
        assert issubclass(exc_class, ExpenseTrackerError)


def test_exception_messages():
    assert str(InvalidCategoryError("Unrecognized category: travel")) == "Unrecognized category: travel"
    assert str(InvalidAmountError("Expense amount must be greater than zero.")) == "Expense amount must be greater than zero."
    assert str(InvalidDateError("Transaction date cannot be in the future.")) == "Transaction date cannot be in the future."
    assert str(AccountLockedError("25")) == "25"
    assert str(AuthenticationError("Invalid username or password.")) == "Invalid username or password."
    assert str(PasswordValidationError("Passwords do not match.")) == "Passwords do not match."
