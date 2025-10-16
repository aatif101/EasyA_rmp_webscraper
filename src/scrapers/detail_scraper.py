"""Professor detail page scraper for RateMyProfessor."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Dict, List, Optional
import logging
import time

from ..models.professor import Professor
from ..utils.cleaner import DataCleaner
from ..utils.error_handler import ErrorHandler
from .review_scraper import ReviewScraper

logger = logging.getLogger(__name__)


class ProfessorDetailScraper:
    """Scraper for extracting detailed professor information from individual professor pages."""
    
    def __init__(self, driver: webdriver.Chrome):
        """
        Initialize the ProfessorDetailScraper.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.cleaner = DataCleaner()
        self.error_handler = ErrorHandler(max_retries=3)
        self.review_scraper = ReviewScraper(driver)
    
    def scrape_professor(self, url: str) -> Optional[Professor]:
        """
        Orchestrate the scraping of a professor's complete data with error recovery.
        
        Args:
            url: URL of the professor's detail page
            
        Returns:
            Professor object with metadata and reviews, or None if scraping fails
        """
        try:
            logger.info(f"Scraping professor page: {url}")
            
            # Navigate to professor page with retry logic
            def _navigate():
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load
            
            self.error_handler.retry_with_backoff(_navigate)
            
            # Extract metadata with error handling
            professor_name = self._extract_professor_name()
            department = self._extract_department()
            overall_quality = self._extract_overall_quality()
            difficulty_level = self._extract_difficulty_level()
            would_take_again = self._extract_would_take_again()
            
            # Extract rating distribution
            rating_distribution = self.extract_rating_distribution()
            
            # Extract tags
            tags = self.extract_tags()
            
            # Load all reviews and extract them
            logger.info("Loading and extracting reviews...")
            self.review_scraper.load_all_reviews()
            reviews = self.review_scraper.extract_reviews()
            
            # Create Professor object with metadata and reviews
            professor = Professor(
                professor_name=professor_name,
                department=department,
                overall_quality=overall_quality,
                difficulty_level=difficulty_level,
                would_take_again=would_take_again,
                rating_distribution=rating_distribution,
                tags=tags,
                reviews=reviews
            )
            
            logger.info(f"Successfully scraped professor: {professor_name} with {len(reviews)} reviews")
            return professor
            
        except Exception as e:
            self.error_handler.log_error(e, f"scraping professor page {url}")
            logger.warning(f"Skipping professor at {url} due to errors")
            return None

    def _extract_professor_name(self, retry: bool = True) -> str:
        """
        Extract professor name from detail page with retry logic.
        
        Args:
            retry: Whether to retry once if extraction fails
            
        Returns:
            Professor name string
        """
        try:
            # Try multiple selectors for professor name
            selectors = [
                "div[class*='NameTitle__Name']",
                "div[class*='TeacherInfo__Name']",
                "h1[class*='NameTitle']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = self.cleaner.clean_text(element.text)
                    if name:
                        logger.debug(f"Extracted professor name: {name}")
                        return name
                except NoSuchElementException:
                    continue
            
            raise NoSuchElementException("Professor name not found with any selector")
            
        except Exception as e:
            if retry:
                logger.warning(f"First attempt to extract professor name failed, retrying: {e}")
                time.sleep(2)
                return self._extract_professor_name(retry=False)
            else:
                logger.error(f"Failed to extract professor name: {e}")
                return "Unknown"
    
    def _extract_department(self, retry: bool = True) -> str:
        """
        Extract department from detail page with retry logic.
        
        Args:
            retry: Whether to retry once if extraction fails
            
        Returns:
            Department string
        """
        try:
            # Try multiple selectors for department
            selectors = [
                "div[class*='NameTitle__Title'] a",
                "a[class*='TeacherDepartment']",
                "div[class*='Department']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    department = self.cleaner.clean_text(element.text)
                    if department:
                        logger.debug(f"Extracted department: {department}")
                        return department
                except NoSuchElementException:
                    continue
            
            raise NoSuchElementException("Department not found with any selector")
            
        except Exception as e:
            if retry:
                logger.warning(f"First attempt to extract department failed, retrying: {e}")
                time.sleep(2)
                return self._extract_department(retry=False)
            else:
                logger.error(f"Failed to extract department: {e}")
                return "Unknown"
    
    def _extract_overall_quality(self, retry: bool = True) -> float:
        """
        Extract overall quality rating with retry logic.
        
        Args:
            retry: Whether to retry once if extraction fails
            
        Returns:
            Quality rating as float (0-5)
        """
        try:
            # Try multiple selectors for quality rating
            selectors = [
                "div[class*='RatingValue__Numerator']",
                "div[class*='TeacherRating__Rating']",
                "div[class*='Quality'] div[class*='RatingValue']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    quality_text = element.text.strip()
                    quality = self.cleaner.parse_number(quality_text)
                    if quality is not None:
                        logger.debug(f"Extracted overall quality: {quality}")
                        return quality
                except NoSuchElementException:
                    continue
            
            raise NoSuchElementException("Overall quality not found with any selector")
            
        except Exception as e:
            if retry:
                logger.warning(f"First attempt to extract overall quality failed, retrying: {e}")
                time.sleep(2)
                return self._extract_overall_quality(retry=False)
            else:
                logger.error(f"Failed to extract overall quality: {e}")
                return 0.0
    
    def _extract_difficulty_level(self, retry: bool = True) -> float:
        """
        Extract difficulty level with retry logic.
        
        Args:
            retry: Whether to retry once if extraction fails
            
        Returns:
            Difficulty level as float (0-5)
        """
        try:
            # Try multiple selectors for difficulty
            selectors = [
                "div[class*='FeedbackItem__FeedbackNumber'][class*='Difficulty']",
                "div[class*='Difficulty'] div[class*='FeedbackNumber']"
            ]
            
            # First try to find the difficulty section
            difficulty_sections = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='FeedbackItem']")
            
            for section in difficulty_sections:
                try:
                    # Check if this section contains "Level of Difficulty" or similar text
                    section_text = section.text.lower()
                    if 'difficulty' in section_text:
                        # Extract the number from this section
                        number_element = section.find_element(By.CSS_SELECTOR, "div[class*='FeedbackNumber']")
                        difficulty_text = number_element.text.strip()
                        difficulty = self.cleaner.parse_number(difficulty_text)
                        if difficulty is not None:
                            logger.debug(f"Extracted difficulty level: {difficulty}")
                            return difficulty
                except NoSuchElementException:
                    continue
            
            # Fallback to direct selectors
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    difficulty_text = element.text.strip()
                    difficulty = self.cleaner.parse_number(difficulty_text)
                    if difficulty is not None:
                        logger.debug(f"Extracted difficulty level: {difficulty}")
                        return difficulty
                except NoSuchElementException:
                    continue
            
            raise NoSuchElementException("Difficulty level not found with any selector")
            
        except Exception as e:
            if retry:
                logger.warning(f"First attempt to extract difficulty level failed, retrying: {e}")
                time.sleep(2)
                return self._extract_difficulty_level(retry=False)
            else:
                logger.error(f"Failed to extract difficulty level: {e}")
                return 0.0
    
    def _extract_would_take_again(self, retry: bool = True) -> Optional[int]:
        """
        Extract would take again percentage with retry logic.
        
        Args:
            retry: Whether to retry once if extraction fails
            
        Returns:
            Percentage as integer (0-100) or None if not available
        """
        try:
            # Find the "Would Take Again" section
            feedback_sections = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='FeedbackItem']")
            
            for section in feedback_sections:
                try:
                    section_text = section.text.lower()
                    if 'would take again' in section_text:
                        # Extract the percentage from this section
                        number_element = section.find_element(By.CSS_SELECTOR, "div[class*='FeedbackNumber']")
                        percentage_text = number_element.text.strip()
                        percentage = self.cleaner.parse_percentage(percentage_text)
                        if percentage is not None:
                            logger.debug(f"Extracted would take again: {percentage}%")
                            return percentage
                except NoSuchElementException:
                    continue
            
            logger.debug("Would take again percentage not found")
            return None
            
        except Exception as e:
            if retry:
                logger.warning(f"First attempt to extract would take again failed, retrying: {e}")
                time.sleep(2)
                return self._extract_would_take_again(retry=False)
            else:
                logger.error(f"Failed to extract would take again: {e}")
                return None

    def extract_rating_distribution(self) -> Dict[str, int]:
        """
        Extract rating distribution counts (Awesome, Great, Good, OK, Awful).
        
        Returns:
            Dictionary with rating categories as keys and counts as values
        """
        distribution = {
            "Awesome": 0,
            "Great": 0,
            "Good": 0,
            "OK": 0,
            "Awful": 0
        }
        
        try:
            # Try to find the rating distribution section
            # Common selectors for rating distribution
            selectors = [
                "div[class*='RatingDistribution']",
                "div[class*='Histogram']",
                "div[class*='RatingBreakdown']"
            ]
            
            distribution_section = None
            for selector in selectors:
                try:
                    distribution_section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not distribution_section:
                logger.warning("Rating distribution section not found")
                return distribution
            
            # Extract individual rating counts
            # Look for elements that contain rating labels and counts
            rating_elements = distribution_section.find_elements(By.CSS_SELECTOR, "div[class*='Rating']")
            
            for element in rating_elements:
                try:
                    text = element.text.strip()
                    
                    # Check for each rating category
                    for category in distribution.keys():
                        if category.lower() in text.lower():
                            # Extract the number from the text
                            # Look for patterns like "Awesome 28" or "28 Awesome"
                            numbers = [int(s) for s in text.split() if s.isdigit()]
                            if numbers:
                                distribution[category] = numbers[0]
                                logger.debug(f"Found {category}: {numbers[0]}")
                                break
                except Exception as e:
                    logger.debug(f"Error parsing rating element: {e}")
                    continue
            
            logger.info(f"Extracted rating distribution: {distribution}")
            return distribution
            
        except Exception as e:
            logger.error(f"Error extracting rating distribution: {e}")
            return distribution

    def extract_tags(self) -> List[str]:
        """
        Extract all professor characteristic tags from the page.
        
        Returns:
            List of tag strings
        """
        tags = []
        
        try:
            # Try multiple selectors for tags
            selectors = [
                "span[class*='Tag-']",
                "div[class*='TeacherTag']",
                "span[class*='TeacherTags']",
                "div[class*='Tag'] span"
            ]
            
            tag_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        tag_elements = elements
                        break
                except NoSuchElementException:
                    continue
            
            if not tag_elements:
                logger.warning("No tag elements found")
                return tags
            
            # Extract text from each tag element
            for element in tag_elements:
                try:
                    tag_text = self.cleaner.clean_text(element.text)
                    if tag_text and tag_text not in tags:  # Avoid duplicates
                        tags.append(tag_text)
                except Exception as e:
                    logger.debug(f"Error extracting tag text: {e}")
                    continue
            
            logger.info(f"Extracted {len(tags)} tags: {tags}")
            return tags
            
        except Exception as e:
            logger.error(f"Error extracting tags: {e}")
            return tags
