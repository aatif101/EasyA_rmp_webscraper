"""WebDriver Manager for RateMyProfessor Scraper"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logger = logging.getLogger(__name__)


class WebDriverManager:
    """Manages Chrome WebDriver lifecycle and provides helper methods for element interaction"""
    
    def __init__(self, headless: bool = True, timeout: int = 10):
        """
        Initialize WebDriver Manager
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for explicit waits in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def get_driver(self) -> webdriver.Chrome:
        """
        Initialize and return Chrome WebDriver with configured options
        
        Returns:
            Configured Chrome WebDriver instance
        """
        if self.driver is not None:
            return self.driver
            
        # Configure Chrome options
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        
        # Add user-agent to avoid detection
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Configure timeouts
        self.driver.implicitly_wait(5)  # 5 second implicit wait
        self.driver.set_page_load_timeout(30)  # 30 second page load timeout
        
        logger.info(f"WebDriver initialized (headless={self.headless}, timeout={self.timeout}s)")
        
        return self.driver
    
    def quit_driver(self):
        """Close and quit the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = None):
        """
        Wait for an element to be present and visible with explicit wait
        
        Args:
            selector: Element selector string
            by: Selenium By locator strategy (default: CSS_SELECTOR)
            timeout: Custom timeout in seconds (uses default if None)
            
        Returns:
            WebElement if found
            
        Raises:
            TimeoutException if element not found within timeout
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            logger.debug(f"Element found: {selector}")
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {selector}")
            raise
    
    def click_with_retry(self, element, retries: int = 3) -> bool:
        """
        Click an element with retry logic for handling stale elements and click interceptions
        
        Args:
            element: WebElement to click or selector string
            retries: Number of retry attempts
            
        Returns:
            True if click succeeded, False otherwise
        """
        for attempt in range(retries):
            try:
                # If element is a string, find it first
                if isinstance(element, str):
                    element = self.wait_for_element(element)
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)  # Brief pause after scroll
                
                # Try to click
                element.click()
                logger.debug(f"Click successful on attempt {attempt + 1}")
                return True
                
            except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                logger.warning(f"Click attempt {attempt + 1} failed: {type(e).__name__}")
                
                if attempt < retries - 1:
                    time.sleep(0.5)  # Wait before retry
                    # If element is stale, try to re-locate it
                    if isinstance(e, StaleElementReferenceException) and isinstance(element, str):
                        try:
                            element = self.wait_for_element(element)
                        except TimeoutException:
                            logger.error(f"Could not re-locate element after stale reference")
                            return False
                else:
                    logger.error(f"Click failed after {retries} attempts")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error during click: {e}")
                return False
        
        return False
    
    def scroll_to_element(self, element):
        """
        Scroll to bring an element into view
        
        Args:
            element: WebElement or selector string to scroll to
        """
        try:
            # If element is a string, find it first
            if isinstance(element, str):
                element = self.wait_for_element(element)
            
            # Scroll element into center of viewport
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)  # Wait for smooth scroll to complete
            logger.debug("Scrolled to element")
            
        except Exception as e:
            logger.warning(f"Error scrolling to element: {e}")
