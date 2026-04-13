"""
Custom exceptions for TrustSpan backend
"""


class TrustSpanException(Exception):
    """Base exception for TrustSpan application."""
    pass


class BlockchainError(TrustSpanException):
    """Exception raised for blockchain-related errors."""
    pass


class AIServiceError(TrustSpanException):
    """Exception raised for AI service errors."""
    pass


class ValidationError(TrustSpanException):
    """Exception raised for validation errors."""
    pass


class AuthenticationError(TrustSpanException):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(TrustSpanException):
    """Exception raised for authorization errors."""
    pass


class InvalidCredentials(AuthenticationError):
    """Exception raised for invalid credentials."""
    pass


class UserNotFound(TrustSpanException):
    """Exception raised when user is not found."""
    pass