# -*- coding: utf-8 -*-
"""
Retry Utilities with Exponential Backoff for MeTruyenCV Downloader
Tiện ích thử lại với exponential backoff cho MeTruyenCV Downloader
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, Union, Type, Tuple
from functools import wraps
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import httpx
from logger import logger

class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        backoff_factor: float = 1.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.backoff_factor = backoff_factor
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if attempt <= 0:
            return 0
        
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** (attempt - 1)) * self.backoff_factor
        
        # Apply maximum delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

# Predefined retry configurations for different operation types
RETRY_CONFIGS = {
    'page_load': RetryConfig(max_attempts=3, base_delay=2.0, max_delay=10.0),
    'element_find': RetryConfig(max_attempts=2, base_delay=1.0, max_delay=5.0),
    'image_download': RetryConfig(max_attempts=3, base_delay=1.0, max_delay=15.0),
    'chapter_content': RetryConfig(max_attempts=2, base_delay=2.0, max_delay=8.0),
    'network_request': RetryConfig(max_attempts=3, base_delay=1.0, max_delay=10.0),
    'default': RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0)
}

def should_retry_exception(exception: Exception, operation_type: str = 'default') -> bool:
    """Determine if an exception should trigger a retry"""
    
    # Network-related exceptions that should be retried
    network_exceptions = (
        httpx.TimeoutException,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError
    )
    
    # Selenium exceptions that should be retried
    selenium_exceptions = (
        TimeoutException,
        WebDriverException
    )
    
    # Exceptions that should NOT be retried
    no_retry_exceptions = (
        KeyboardInterrupt,
        SystemExit,
        MemoryError,
        NoSuchElementException  # Usually indicates page structure change
    )
    
    if isinstance(exception, no_retry_exceptions):
        return False
    
    if operation_type in ['page_load', 'network_request', 'image_download']:
        return isinstance(exception, network_exceptions + selenium_exceptions)
    
    if operation_type in ['element_find', 'chapter_content']:
        return isinstance(exception, selenium_exceptions)
    
    # Default: retry most exceptions except the no-retry list
    return not isinstance(exception, no_retry_exceptions)

async def async_retry(
    func: Callable,
    *args,
    operation_type: str = 'default',
    config: Optional[RetryConfig] = None,
    context: str = None,
    **kwargs
) -> Any:
    """
    Async retry wrapper with exponential backoff
    
    Args:
        func: Async function to retry
        *args: Arguments for the function
        operation_type: Type of operation for retry configuration
        config: Custom retry configuration
        context: Context for logging
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = RETRY_CONFIGS.get(operation_type, RETRY_CONFIGS['default'])
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            if attempt > 1:
                delay = config.calculate_delay(attempt - 1)
                if delay > 0:
                    logger.log_retry(
                        func.__name__, 
                        attempt, 
                        config.max_attempts, 
                        delay, 
                        context
                    )
                    await asyncio.sleep(delay)
            
            # Call the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success
            if attempt > 1:
                logger.info(f"Thành công {func.__name__} sau {attempt} lần thử", context)
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Check if we should retry this exception
            if not should_retry_exception(e, operation_type):
                logger.error(f"Lỗi không thể retry: {str(e)[:100]}", context)
                raise e
            
            # Log the attempt failure
            if attempt < config.max_attempts:
                logger.warning(f"Lần thử {attempt} thất bại: {str(e)[:100]}", context)
            else:
                logger.error(f"Tất cả {config.max_attempts} lần thử đều thất bại: {str(e)[:100]}", context)
    
    # All retries failed
    raise last_exception

def sync_retry(
    func: Callable,
    *args,
    operation_type: str = 'default',
    config: Optional[RetryConfig] = None,
    context: str = None,
    **kwargs
) -> Any:
    """
    Synchronous retry wrapper with exponential backoff
    
    Args:
        func: Function to retry
        *args: Arguments for the function
        operation_type: Type of operation for retry configuration
        config: Custom retry configuration
        context: Context for logging
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = RETRY_CONFIGS.get(operation_type, RETRY_CONFIGS['default'])
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            if attempt > 1:
                delay = config.calculate_delay(attempt - 1)
                if delay > 0:
                    logger.log_retry(
                        func.__name__, 
                        attempt, 
                        config.max_attempts, 
                        delay, 
                        context
                    )
                    time.sleep(delay)
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Success
            if attempt > 1:
                logger.info(f"Thành công {func.__name__} sau {attempt} lần thử", context)
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Check if we should retry this exception
            if not should_retry_exception(e, operation_type):
                logger.error(f"Lỗi không thể retry: {str(e)[:100]}", context)
                raise e
            
            # Log the attempt failure
            if attempt < config.max_attempts:
                logger.warning(f"Lần thử {attempt} thất bại: {str(e)[:100]}", context)
            else:
                logger.error(f"Tất cả {config.max_attempts} lần thử đều thất bại: {str(e)[:100]}", context)
    
    # All retries failed
    raise last_exception

def retry_on_failure(
    operation_type: str = 'default',
    config: Optional[RetryConfig] = None
):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        operation_type: Type of operation for retry configuration
        config: Custom retry configuration
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = kwargs.pop('_retry_context', None)
            return await async_retry(
                func, *args, 
                operation_type=operation_type, 
                config=config, 
                context=context,
                **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = kwargs.pop('_retry_context', None)
            return sync_retry(
                func, *args, 
                operation_type=operation_type, 
                config=config, 
                context=context,
                **kwargs
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Convenience decorators for common operations
retry_page_load = retry_on_failure('page_load')
retry_element_find = retry_on_failure('element_find')
retry_image_download = retry_on_failure('image_download')
retry_chapter_content = retry_on_failure('chapter_content')
retry_network_request = retry_on_failure('network_request')
