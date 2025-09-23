"""
Exception classes for the Hybrid Surveyor application.

This module defines a hierarchy of exceptions that provide clear error handling
and debugging information throughout the application.
"""

from typing import Any, Dict, Optional


class HybridSurveyorException(Exception):
    """Base exception for all Hybrid Surveyor errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        result = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            result += f" (Details: {details_str})"
        if self.cause:
            result += f" (Caused by: {self.cause})"
        return result


class ConfigurationError(HybridSurveyorException):
    """Raised when there's an error in application configuration."""
    pass


class AuthenticationError(HybridSurveyorException):
    """Raised when authentication with external services fails."""
    pass


class DataExtractionError(HybridSurveyorException):
    """Raised when data extraction from Google Sheets fails."""
    pass


class DataTransformationError(HybridSurveyorException):
    """Raised when data transformation or normalization fails."""
    pass


class DatabaseError(HybridSurveyorException):
    """Raised when database operations fail."""
    pass


class ValidationError(HybridSurveyorException):
    """Raised when data validation fails."""
    pass


class ProcessingError(HybridSurveyorException):
    """Raised when data processing pipeline fails."""
    pass


class RetryableError(HybridSurveyorException):
    """Base class for errors that can be retried."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        max_retries: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.max_retries = max_retries


class RateLimitError(RetryableError):
    """Raised when API rate limits are exceeded."""
    pass


class TemporaryServiceError(RetryableError):
    """Raised when external services are temporarily unavailable."""
    pass
