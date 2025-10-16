"""Error handling utilities with retry logic and logging."""

import logging
import time
from typing import Callable, Any, Optional
from functools import wraps
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)


class ErrorHandler:
    """Handles errors with retry logic and exponential backoff."""
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize ErrorHandler.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    def retry_with_backoff(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Retry a function with exponential backoff.
        
        Implements exponential backoff: 1s, 2s, 4s for up to 3 retries.
        
        Args:
            func: Function to retry
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of successful function call
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (
                TimeoutException,
                WebDriverException,
                ConnectionError,
                Exception
            ) as e:
                last_exception = e
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"All {self.max_retries} attempts failed for {func.__name__}"
                    )
        
        raise last_exception
    
    def handle_missing_element(
        self, 
        func: Callable, 
        selector: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Handle missing element with single retry.
        
        Args:
            func: Function that locates element
            selector: CSS selector or XPath for the element
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Element if found, None otherwise
        """
        try:
            return func(*args, **kwargs)
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.warning(
                f"Element not found on first attempt: {selector}. Retrying..."
            )
            
            # Wait 2 seconds before retry
            time.sleep(2)
            
            try:
                return func(*args, **kwargs)
            except (NoSuchElementException, TimeoutException) as retry_error:
                self.logger.error(
                    f"Element not found after retry: {selector}. "
                    f"Error: {str(retry_error)}"
                )
                return None
    
    def log_error(self, error: Exception, context: str) -> None:
        """
        Log error with context information.
        
        Args:
            error: Exception that occurred
            context: Context description (e.g., "scraping professor X")
        """
        self.logger.error(
            f"Error in {context}: {type(error).__name__} - {str(error)}",
            exc_info=True
        )
