class ExpenseTrackerError(Exception):
    pass


class InvalidCategoryError(ExpenseTrackerError):
    pass


class CategoryAlreadyExistsError(ExpenseTrackerError):
    pass


class InvalidAmountError(ExpenseTrackerError):
    pass


class InvalidDateError(ExpenseTrackerError):
    pass


class AccountLockedError(ExpenseTrackerError):
    # Raised with remaining lockout seconds as the message
    pass


class AuthenticationError(ExpenseTrackerError):
    pass


class PasswordValidationError(ExpenseTrackerError):
    pass
