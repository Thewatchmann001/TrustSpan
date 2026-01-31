"""
Timeout Utilities
Enforces 15-second timeout on AI calls and matching operations.
"""
import asyncio
import signal
import functools
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from app.utils.logger import logger


class TimeoutError(Exception):
    """Custom timeout error."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out after 15 seconds")


def with_timeout(timeout_seconds: int = 15):
    """
    Decorator to enforce timeout on synchronous functions.
    
    Usage:
        @with_timeout(15)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use ThreadPoolExecutor for timeout
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(func, *args, **kwargs)
            
            try:
                result = future.result(timeout=timeout_seconds)
                return result
            except FutureTimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                future.cancel()
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
            finally:
                executor.shutdown(wait=False)
        
        return wrapper
    return decorator


async def async_with_timeout(coro, timeout_seconds: int = 15):
    """
    Async timeout wrapper.
    
    Usage:
        result = await async_with_timeout(my_async_function(), 15)
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Async operation timed out after {timeout_seconds} seconds")
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")


def safe_execute_with_timeout(
    func: Callable,
    timeout_seconds: int = 15,
    fallback: Any = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with timeout and return fallback on timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds (default: 15)
        fallback: Value to return on timeout
        *args, **kwargs: Arguments to pass to function
    
    Returns:
        Function result or fallback on timeout
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, *args, **kwargs)
    
    try:
        result = future.result(timeout=timeout_seconds)
        return result
    except FutureTimeoutError:
        logger.warning(f"Function {func.__name__} timed out after {timeout_seconds} seconds - returning fallback")
        future.cancel()
        return fallback
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {str(e)}")
        return fallback
    finally:
        executor.shutdown(wait=False)
