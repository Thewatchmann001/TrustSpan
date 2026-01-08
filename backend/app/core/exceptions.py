"""
Custom exceptions for TrustBridge backend
"""


class TrustBridgeException(Exception):
    """Base exception for TrustBridge application."""
    pass


class BlockchainError(TrustBridgeException):
    """Exception raised for blockchain-related errors."""
    pass


class AIServiceError(TrustBridgeException):
    """Exception raised for AI service errors."""
    pass


class ValidationError(TrustBridgeException):
    """Exception raised for validation errors."""
    pass


class AuthenticationError(TrustBridgeException):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(TrustBridgeException):
    """Exception raised for authorization errors."""
    pass


class InvalidCredentials(AuthenticationError):
    """Exception raised for invalid credentials."""
    pass


class UserNotFound(TrustBridgeException):
    """Exception raised when user is not found."""
    pass