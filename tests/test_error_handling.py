"""Tests for error handling and retry logic."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from src.getsitedna.utils.error_handling import (
    ErrorHandler, AnalysisError, NetworkError, ParsingError, BrowserError,
    ValidationError, RateLimitError, ErrorSeverity, ErrorCategory,
    RetryConfig, retry_on_error, calculate_delay, SafeExecutor, CircuitBreaker
)


class TestErrorClasses:
    """Test custom error classes."""
    
    def test_analysis_error_creation(self):
        """Test AnalysisError creation."""
        error = AnalysisError(
            "Test error",
            ErrorCategory.NETWORK,
            ErrorSeverity.HIGH,
            {"url": "https://example.com"}
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.HIGH
        assert error.context["url"] == "https://example.com"
        assert error.timestamp > 0
    
    def test_network_error_creation(self):
        """Test NetworkError creation."""
        error = NetworkError("Connection failed", 404, "https://example.com")
        
        assert error.message == "Connection failed"
        assert error.category == ErrorCategory.NETWORK
        assert error.context["status_code"] == 404
        assert error.context["url"] == "https://example.com"
    
    def test_parsing_error_creation(self):
        """Test ParsingError creation."""
        error = ParsingError("Invalid HTML", "https://example.com", "div")
        
        assert error.message == "Invalid HTML"
        assert error.category == ErrorCategory.PARSING
        assert error.severity == ErrorSeverity.LOW
        assert error.context["url"] == "https://example.com"
        assert error.context["element"] == "div"
    
    def test_browser_error_creation(self):
        """Test BrowserError creation."""
        error = BrowserError("Browser crashed", "https://example.com", "chromium")
        
        assert error.message == "Browser crashed"
        assert error.category == ErrorCategory.BROWSER
        assert error.severity == ErrorSeverity.HIGH
        assert error.context["browser_type"] == "chromium"
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid field", "name", "invalid_value")
        
        assert error.message == "Invalid field"
        assert error.category == ErrorCategory.VALIDATION
        assert error.context["field"] == "name"
        assert error.context["value"] == "invalid_value"
    
    def test_rate_limit_error_creation(self):
        """Test RateLimitError creation."""
        error = RateLimitError("Rate limited", 60, "https://example.com")
        
        assert error.message == "Rate limited"
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.context["retry_after"] == 60


class TestErrorHandler:
    """Test ErrorHandler functionality."""
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler("test_logger")
        
        assert handler.logger.name == "test_logger"
        assert handler.error_stats["total_errors"] == 0
        assert isinstance(handler.error_stats["by_category"], dict)
        assert isinstance(handler.error_stats["by_severity"], dict)
        assert isinstance(handler.error_stats["recent_errors"], list)
    
    def test_handle_analysis_error(self):
        """Test handling AnalysisError."""
        handler = ErrorHandler()
        
        error = AnalysisError("Test error", ErrorCategory.NETWORK, ErrorSeverity.HIGH)
        result = handler.handle_error(error)
        
        assert result == error
        assert handler.error_stats["total_errors"] == 1
        assert handler.error_stats["by_category"]["network"] == 1
        assert handler.error_stats["by_severity"]["high"] == 1
    
    def test_handle_generic_exception(self):
        """Test handling generic Python exceptions."""
        handler = ErrorHandler()
        
        generic_error = ValueError("Invalid value")
        result = handler.handle_error(generic_error)
        
        assert isinstance(result, AnalysisError)
        assert "ValueError" in result.message
        assert result.category == ErrorCategory.UNKNOWN
        assert handler.error_stats["total_errors"] == 1
    
    def test_error_classification(self):
        """Test automatic error classification."""
        handler = ErrorHandler()
        
        # Test timeout error
        timeout_error = asyncio.TimeoutError("Request timed out")
        result = handler.handle_error(timeout_error)
        
        assert result.category == ErrorCategory.TIMEOUT
        assert result.severity == ErrorSeverity.MEDIUM
        
        # Test file error
        file_error = FileNotFoundError("File not found")
        result = handler.handle_error(file_error)
        
        assert result.category == ErrorCategory.FILE_SYSTEM
        assert result.severity == ErrorSeverity.HIGH
    
    def test_error_statistics_tracking(self):
        """Test error statistics tracking."""
        handler = ErrorHandler()
        
        # Add multiple errors
        handler.handle_error(AnalysisError("Error 1", ErrorCategory.NETWORK, ErrorSeverity.HIGH))
        handler.handle_error(AnalysisError("Error 2", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM))
        handler.handle_error(AnalysisError("Error 3", ErrorCategory.PARSING, ErrorSeverity.LOW))
        
        stats = handler.get_error_summary()
        
        assert stats["total_errors"] == 3
        assert stats["by_category"]["network"] == 2
        assert stats["by_category"]["parsing"] == 1
        assert stats["by_severity"]["high"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_severity"]["low"] == 1
        assert len(stats["recent_errors"]) == 3
    
    def test_recent_errors_limit(self):
        """Test recent errors list limit."""
        handler = ErrorHandler()
        
        # Add more than 50 errors
        for i in range(60):
            handler.handle_error(AnalysisError(f"Error {i}", ErrorCategory.UNKNOWN, ErrorSeverity.LOW))
        
        stats = handler.get_error_summary()
        
        # Should keep only last 50
        assert len(stats["recent_errors"]) == 50
        assert stats["total_errors"] == 60
    
    def test_should_continue_logic(self):
        """Test should_continue decision logic."""
        handler = ErrorHandler()
        
        # Low/medium errors should allow continuation
        low_error = AnalysisError("Low error", ErrorCategory.PARSING, ErrorSeverity.LOW)
        assert handler.should_continue(handler.handle_error(low_error))
        
        medium_error = AnalysisError("Medium error", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM)
        assert handler.should_continue(handler.handle_error(medium_error))
        
        # Critical errors should stop
        critical_error = AnalysisError("Critical error", ErrorCategory.UNKNOWN, ErrorSeverity.CRITICAL)
        assert not handler.should_continue(handler.handle_error(critical_error))
        
        # Too many high errors should stop
        handler.error_stats["by_severity"]["high"] = 15
        high_error = AnalysisError("High error", ErrorCategory.UNKNOWN, ErrorSeverity.HIGH)
        assert not handler.should_continue(handler.handle_error(high_error))


class TestRetryLogic:
    """Test retry functionality."""
    
    def test_retry_config(self):
        """Test RetryConfig creation."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
    
    def test_calculate_delay(self):
        """Test delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        
        # Test max delay limit
        config_with_max = RetryConfig(base_delay=1.0, max_delay=3.0, jitter=False)
        assert calculate_delay(10, config_with_max) == 3.0
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(base_delay=2.0, jitter=True)
        
        delay = calculate_delay(0, config)
        
        # Should be between 50-100% of base delay
        assert 1.0 <= delay <= 2.0
    
    @pytest.mark.asyncio
    async def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""
        call_count = 0
        
        @retry_on_error()
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_decorator_eventual_success(self):
        """Test retry decorator with eventual success."""
        call_count = 0
        
        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_decorator_permanent_failure(self):
        """Test retry decorator with permanent failure."""
        call_count = 0
        
        @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.01))
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError):
            await test_function()
        
        assert call_count == 3
    
    def test_retry_decorator_sync_function(self):
        """Test retry decorator with synchronous function."""
        call_count = 0
        
        @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.01))
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_with_specific_exceptions(self):
        """Test retry with specific exception types."""
        call_count = 0
        
        @retry_on_error(
            RetryConfig(max_attempts=3, base_delay=0.01),
            exceptions=(ValueError,)
        )
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            elif call_count == 2:
                raise TypeError("Non-retryable error")
            return "success"
        
        # Should not retry TypeError
        with pytest.raises(TypeError):
            await test_function()
        
        assert call_count == 2


class TestSafeExecutor:
    """Test SafeExecutor functionality."""
    
    def test_safe_executor_initialization(self):
        """Test SafeExecutor initialization."""
        executor = SafeExecutor()
        
        assert executor.error_handler is not None
    
    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test safe execution with successful function."""
        executor = SafeExecutor()
        
        async def test_function(x, y):
            return x + y
        
        result = await executor.safe_execute(test_function, 2, 3)
        
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_safe_execute_with_error(self):
        """Test safe execution with error."""
        executor = SafeExecutor()
        
        async def test_function():
            raise ValueError("Test error")
        
        result = await executor.safe_execute(test_function, default_return="default")
        
        assert result == "default"
        assert executor.error_handler.error_stats["total_errors"] == 1
    
    def test_safe_execute_sync(self):
        """Test synchronous safe execution."""
        executor = SafeExecutor()
        
        def test_function():
            raise ValueError("Test error")
        
        result = executor.safe_execute_sync(test_function, default_return="default")
        
        assert result == "default"
        assert executor.error_handler.error_stats["total_errors"] == 1
    
    @pytest.mark.asyncio
    async def test_safe_execute_with_context(self):
        """Test safe execution with error context."""
        executor = SafeExecutor()
        
        async def test_function():
            raise ValueError("Test error")
        
        await executor.safe_execute(
            test_function,
            error_context={"operation": "test", "url": "https://example.com"}
        )
        
        # Check that context was recorded
        recent_errors = executor.error_handler.error_stats["recent_errors"]
        assert len(recent_errors) == 1


class TestCircuitBreaker:
    """Test CircuitBreaker pattern."""
    
    def test_circuit_breaker_initialization(self):
        """Test CircuitBreaker initialization."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        @breaker
        async def test_function():
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening after threshold."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        call_count = 0
        
        @breaker
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test failure")
        
        # First failure
        with pytest.raises(ValueError):
            await test_function()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(ValueError):
            await test_function()
        assert breaker.state == "OPEN"
        assert breaker.failure_count == 2
        
        # Third call should fail immediately without calling function
        with pytest.raises(AnalysisError):
            await test_function()
        assert call_count == 2  # Function not called the third time
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        
        @breaker
        async def test_function():
            return "success"
        
        # Trigger failure to open circuit
        test_function.failure_count = 1
        breaker.state = "OPEN"
        breaker.last_failure_time = time.time() - 0.02  # Past recovery timeout
        
        # Should attempt reset and succeed
        result = await test_function()
        
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0