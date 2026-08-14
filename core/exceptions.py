"""Custom domain exceptions for the Expense Tracker application."""


class ExpenseTrackerError(Exception):
    """Base exception for all application errors."""
    pass


class InvalidCategoryError(ExpenseTrackerError):
    """Raised when an unrecognized or invalid category is specified."""
    pass


class CategoryAlreadyExistsError(ExpenseTrackerError):
    """Raised when attempting to add a category that already exists."""
    pass


class InvalidAmountError(ExpenseTrackerError):
    """Raised when an invalid, negative, or zero financial amount is provided."""
    pass


class AccountLockedError(ExpenseTrackerError):
    """Raised when an account is temporarily locked due to failed login attempts."""
    pass


class AuthenticationError(ExpenseTrackerError):
    """Raised when invalid login credentials are provided."""
    pass


class PasswordValidationError(ExpenseTrackerError):
    """Raised when a password fails complexity or match validation."""
    pass
