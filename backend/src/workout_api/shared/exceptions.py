"""Custom exceptions for the workout API."""


class WorkoutAPIException(Exception):
    """Base exception for all workout API exceptions."""

    pass


class NotFoundError(WorkoutAPIException):
    """Raised when a requested resource is not found."""

    pass


class DuplicateError(WorkoutAPIException):
    """Raised when attempting to create a duplicate resource."""

    pass


class ValidationError(WorkoutAPIException):
    """Raised when data validation fails."""

    pass


class PermissionError(WorkoutAPIException):
    """Raised when user lacks permission for an operation."""

    pass


class AuthenticationError(WorkoutAPIException):
    """Raised when authentication fails."""

    pass


class BusinessRuleError(WorkoutAPIException):
    """Raised when a business rule is violated."""

    pass
