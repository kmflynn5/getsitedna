"""Comprehensive error handling and retry logic utilities."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
import traceback

import requests
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pydantic import ValidationError


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    PARSING = "parsing"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    BROWSER = "browser"
    FILE_SYSTEM = "file_system"
    UNKNOWN = "unknown"


class AnalysisError(Exception):
    """Base exception for analysis errors."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[Dict] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.timestamp = time.time()
        super().__init__(message)


class NetworkError(AnalysisError):
    """Network-related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        context = {"status_code": status_code, "url": url}
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, context)


class ParsingError(AnalysisError):
    """HTML/CSS parsing errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, element: Optional[str] = None):
        context = {"url": url, "element": element}
        super().__init__(message, ErrorCategory.PARSING, ErrorSeverity.LOW, context)


class BrowserError(AnalysisError):
    """Browser automation errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, browser_type: Optional[str] = None):
        context = {"url": url, "browser_type": browser_type}
        super().__init__(message, ErrorCategory.BROWSER, ErrorSeverity.HIGH, context)


class ValidationError(AnalysisError):
    """Data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        context = {"field": field, "value": str(value) if value is not None else None}
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, context)


class RateLimitError(AnalysisError):
    """Rate limiting errors."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, url: Optional[str] = None):
        context = {"retry_after": retry_after, "url": url}
        super().__init__(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, context)


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, logger_name: str = "getsitedna"):
        self.logger = logging.getLogger(logger_name)
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "recent_errors": []
        }
        
        # Configure logging if not already configured
        if not self.logger.handlers:
            self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None) -> AnalysisError:
        """Handle and classify an error."""
        # Convert to AnalysisError if not already
        if isinstance(error, AnalysisError):
            analysis_error = error
        else:
            analysis_error = self._classify_error(error, context)
        
        # Log the error
        self._log_error(analysis_error)
        
        # Update statistics
        self._update_stats(analysis_error)
        
        return analysis_error
    
    def _classify_error(self, error: Exception, context: Optional[Dict] = None) -> AnalysisError:
        """Classify a generic exception into an AnalysisError."""
        error_type = type(error).__name__
        error_message = str(error)
        context = context or {}
        
        # Network errors
        if isinstance(error, (requests.RequestException, requests.ConnectionError)):
            return NetworkError(f"Network error: {error_message}", context=context)
        
        # Timeout errors
        if isinstance(error, (asyncio.TimeoutError, PlaywrightTimeoutError)):
            return AnalysisError(
                f"Timeout error: {error_message}",
                ErrorCategory.TIMEOUT,
                ErrorSeverity.MEDIUM,
                context
            )
        
        # Validation errors
        if isinstance(error, ValidationError):
            return ValidationError(f"Validation error: {error_message}", context=context)
        
        # File system errors
        if isinstance(error, (FileNotFoundError, PermissionError, OSError)):
            return AnalysisError(
                f"File system error: {error_message}",
                ErrorCategory.FILE_SYSTEM,
                ErrorSeverity.HIGH,
                context
            )
        
        # Default classification
        return AnalysisError(
            f"Unexpected error ({error_type}): {error_message}",
            ErrorCategory.UNKNOWN,
            ErrorSeverity.MEDIUM,
            context
        )
    
    def _log_error(self, error: AnalysisError):
        """Log an error with appropriate level."""
        log_message = f"[{error.category.value.upper()}] {error.message}"
        
        if error.context:
            context_str = ", ".join(f"{k}={v}" for k, v in error.context.items() if v is not None)
            if context_str:
                log_message += f" (Context: {context_str})"
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _update_stats(self, error: AnalysisError):
        """Update error statistics."""
        self.error_stats["total_errors"] += 1
        
        # Update by category
        category = error.category.value
        self.error_stats["by_category"][category] = self.error_stats["by_category"].get(category, 0) + 1
        
        # Update by severity
        severity = error.severity.value
        self.error_stats["by_severity"][severity] = self.error_stats["by_severity"].get(severity, 0) + 1
        
        # Add to recent errors (keep last 50)
        error_summary = {
            "timestamp": error.timestamp,
            "category": category,
            "severity": severity,
            "message": error.message[:100]  # Truncate long messages
        }
        self.error_stats["recent_errors"].append(error_summary)
        
        # Keep only last 50 errors
        if len(self.error_stats["recent_errors"]) > 50:
            self.error_stats["recent_errors"] = self.error_stats["recent_errors"][-50:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of error statistics."""
        return self.error_stats.copy()
    
    def should_continue(self, error: AnalysisError) -> bool:
        """Determine if analysis should continue after an error."""
        # Critical errors should stop analysis
        if error.severity == ErrorSeverity.CRITICAL:
            return False
        
        # Too many high severity errors
        high_errors = self.error_stats["by_severity"].get("high", 0)
        if high_errors > 10:
            return False
        
        # Too many total errors
        if self.error_stats["total_errors"] > 100:
            return False
        
        return True


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def retry_on_error(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
    error_handler: Optional[ErrorHandler] = None
):
    """Decorator for retrying functions on specific exceptions."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if error_handler:
                        analysis_error = error_handler.handle_error(e)
                        if not error_handler.should_continue(analysis_error):
                            break
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        await asyncio.sleep(delay)
                    
            # All retries exhausted
            if error_handler and last_exception:
                final_error = error_handler.handle_error(last_exception)
                raise final_error
            else:
                raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if error_handler:
                        analysis_error = error_handler.handle_error(e)
                        if not error_handler.should_continue(analysis_error):
                            break
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        time.sleep(delay)
                    
            # All retries exhausted
            if error_handler and last_exception:
                final_error = error_handler.handle_error(last_exception)
                raise final_error
            else:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry attempt."""
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        import random
        delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
    
    return delay


class SafeExecutor:
    """Safe execution wrapper with error handling."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
    
    async def safe_execute(self, 
                          func: Callable, 
                          *args, 
                          default_return: Any = None,
                          error_context: Optional[Dict] = None,
                          **kwargs) -> Any:
        """Safely execute a function with error handling."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            self.error_handler.handle_error(e, error_context)
            return default_return
    
    def safe_execute_sync(self, 
                         func: Callable, 
                         *args, 
                         default_return: Any = None,
                         error_context: Optional[Dict] = None,
                         **kwargs) -> Any:
        """Safely execute a function synchronously with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error_handler.handle_error(e, error_context)
            return default_return


class CircuitBreaker:
    """Circuit breaker pattern for failing operations."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise AnalysisError(
                        "Circuit breaker is OPEN",
                        ErrorCategory.NETWORK,
                        ErrorSeverity.HIGH
                    )
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


# Global error handler instance
default_error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[Dict] = None) -> AnalysisError:
    """Global error handling function."""
    return default_error_handler.handle_error(error, context)


def get_error_stats() -> Dict[str, Any]:
    """Get global error statistics."""
    return default_error_handler.get_error_summary()