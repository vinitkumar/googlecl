"""Custom exceptions for GoogleCL."""


class GoogleCLException(Exception):
    """Base exception for GoogleCL."""

    pass


class ExecutionError(GoogleCLException):
    """Raised when there's an error during command execution."""

    pass


class EarlyQuit(GoogleCLException):
    """Raised when the application needs to quit early."""

    pass


class AuthenticationError(GoogleCLException):
    """Raised when authentication fails."""

    pass


class ServiceError(GoogleCLException):
    """Raised when a Google service operation fails."""

    pass


class ConfigurationError(GoogleCLException):
    """Raised when there's a configuration issue."""

    pass
