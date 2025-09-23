"""
Retry strategies for handling transient failures.

This module provides various retry strategies with exponential backoff,
jitter, and configurable retry conditions.
"""

import asyncio
import random
import logging
from typing import Any, Callable, Optional, Type, Union, List
from datetime import datetime, timedelta

from ..core.interfaces import IRetryStrategy
from ..core.exceptions import RetryableError, RateLimitError, TemporaryServiceError
from ..models.domain import RetryConfig

logger = logging.getLogger(__name__)


class ExponentialBackoffRetry(IRetryStrategy):
    """
    Exponential backoff retry strategy with jitter.
    
    Features:
    - Exponential backoff with configurable base and multiplier
    - Optional jitter to prevent thundering herd
    - Configurable retry conditions
    - Detailed logging of retry attempts
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.retryable_exceptions = (
            RetryableError,
            RateLimitError,
            TemporaryServiceError,
            ConnectionError,
            TimeoutError,
        )
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute operation with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt + 1} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception is retryable
                if not self._is_retryable(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise
                
                # Check if we have more attempts
                if attempt >= self.config.max_attempts - 1:
                    logger.error(
                        f"Operation failed after {self.config.max_attempts} attempts: {e}"
                    )
                    raise
                
                # Calculate delay
                delay = self._calculate_delay(attempt, e)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if an exception is retryable."""
        return isinstance(exception, self.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int, exception: Exception) -> float:
        """Calculate delay for the next retry attempt."""
        # Check if the exception specifies a retry delay
        if isinstance(exception, RetryableError) and exception.retry_after:
            base_delay = exception.retry_after
        else:
            # Calculate exponential backoff
            base_delay = self.config.base_delay * (
                self.config.exponential_base ** attempt
            )
        
        # Apply maximum delay limit
        delay = min(base_delay, self.config.max_delay)
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class LinearBackoffRetry(IRetryStrategy):
    """Linear backoff retry strategy."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        increment: float = 1.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.increment = increment
        self.retryable_exceptions = (
            RetryableError,
            RateLimitError,
            TemporaryServiceError,
            ConnectionError,
            TimeoutError,
        )
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute operation with linear backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not isinstance(e, self.retryable_exceptions):
                    raise
                
                if attempt >= self.max_attempts - 1:
                    raise
                
                delay = self.base_delay + (attempt * self.increment)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise last_exception


class NoRetry(IRetryStrategy):
    """No retry strategy - executes operation once."""
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute operation without retry."""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            return operation(*args, **kwargs)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by temporarily stopping calls to a failing service.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, operation: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute operation through circuit breaker."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (
            datetime.utcnow() - self.last_failure_time
        ).total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
