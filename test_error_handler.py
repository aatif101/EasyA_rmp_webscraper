"""Test error handler functionality."""

import time
from src.utils.error_handler import ErrorHandler
from src.utils.logger import setup_logging


def test_retry_with_backoff():
    """Test retry with exponential backoff."""
    setup_logging("test_error_handler.log")
    error_handler = ErrorHandler(max_retries=3)
    
    # Test function that fails twice then succeeds
    attempt_count = [0]
    
    def failing_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ConnectionError(f"Attempt {attempt_count[0]} failed")
        return "Success"
    
    result = error_handler.retry_with_backoff(failing_function)
    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count[0]}")
    assert result == "Success"
    assert attempt_count[0] == 3


def test_handle_missing_element():
    """Test handling missing element with single retry."""
    setup_logging("test_error_handler.log")
    error_handler = ErrorHandler()
    
    # Test function that fails once then succeeds
    attempt_count = [0]
    
    def find_element():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            from selenium.common.exceptions import NoSuchElementException
            raise NoSuchElementException("Element not found")
        return "Element found"
    
    result = error_handler.handle_missing_element(find_element, "test-selector")
    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count[0]}")
    assert result == "Element found"
    assert attempt_count[0] == 2


def test_log_error():
    """Test error logging."""
    setup_logging("test_error_handler.log")
    error_handler = ErrorHandler()
    
    try:
        raise ValueError("Test error message")
    except ValueError as e:
        error_handler.log_error(e, "test context")
        print("Error logged successfully")


if __name__ == "__main__":
    print("Testing retry with backoff...")
    test_retry_with_backoff()
    print("\nTesting handle missing element...")
    test_handle_missing_element()
    print("\nTesting error logging...")
    test_log_error()
    print("\nAll tests passed!")
