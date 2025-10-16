"""Review scraper for RateMyProfessor."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from typing import List
import logging
import time

from ..models.review import Review
from ..utils.cleaner import DataCleaner
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class ReviewScraper:
    """Scraper for extracting reviews from professor detail pages."""
    
    def __init__(self, driver: webdriver.Chrome):
        """
        Initialize the ReviewScraper.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.cleaner = DataCleaner()
        self.error_handler = ErrorHandler(max_retries=3)
        logger.debug("ReviewScraper initialized")

    def load_all_reviews(self) -> None:
        """
        Click "Load More Ratings" button repeatedly until all reviews are loaded.
        Scrolls to button before clicking and stops when button is no longer present.
        Includes error handling and rate limiting.
        """
        logger.info("Loading all reviews...")
        clicks = 0
        max_clicks = 100  # Safety limit to prevent infinite loops
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while clicks < max_clicks:
            try:
                # Try to find the "Load More" button using multiple selectors
                button = None
                selectors = [
                    "//button[contains(., 'Load More')]",
                    "//button[contains(., 'Show More')]",
                    "//button[contains(@class, 'Buttons__Button') and contains(., 'Load')]",
                    "//a[contains(., 'Load More')]"
                ]
                
                for selector in selectors:
                    try:
                        button = self.driver.find_element(By.XPATH, selector)
                        if button and button.is_displayed():
                            break
                    except NoSuchElementException:
                        continue
                
                if not button or not button.is_displayed():
                    logger.info(f"Load More button not found after {clicks} clicks. All reviews loaded.")
                    break
                
                # Scroll to button before clicking
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)  # Wait for scroll to complete
                
                # Click the button
                try:
                    button.click()
                    clicks += 1
                    consecutive_errors = 0  # Reset error counter on success
                    logger.debug(f"Clicked Load More button (click #{clicks})")
                    
                    # Add delay to avoid rate limiting and allow content to load
                    time.sleep(1.5)
                    
                except Exception as e:
                    logger.warning(f"Error clicking Load More button: {e}")
                    consecutive_errors += 1
                    
                    # Try JavaScript click as fallback
                    try:
                        self.driver.execute_script("arguments[0].click();", button)
                        clicks += 1
                        consecutive_errors = 0  # Reset error counter on success
                        logger.debug(f"Clicked Load More button via JavaScript (click #{clicks})")
                        time.sleep(1.5)
                    except Exception as js_error:
                        self.error_handler.log_error(js_error, "clicking Load More button")
                        consecutive_errors += 1
                        
                        # If too many consecutive errors, break
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping review loading.")
                            break
                        
                        # Wait before retrying to handle rate limiting
                        time.sleep(2)
                
            except NoSuchElementException:
                logger.info(f"Load More button no longer present after {clicks} clicks. All reviews loaded.")
                break
            except Exception as e:
                self.error_handler.log_error(e, "review pagination")
                consecutive_errors += 1
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping review loading.")
                    break
                
                # Wait before retrying to handle rate limiting
                time.sleep(2)
        
        if clicks >= max_clicks:
            logger.warning(f"Reached maximum click limit ({max_clicks}). Some reviews may not be loaded.")
        
        logger.info(f"Finished loading reviews after {clicks} Load More clicks")

    def extract_reviews(self) -> List[Review]:
        """
        Extract all review data from the current page.
        
        Returns:
            List of Review objects with all extracted fields
        """
        reviews = []
        
        try:
            # Find all review elements on the page
            # Try multiple selectors for review cards
            review_elements = []
            selectors = [
                "div[class*='Rating__StyledRating']",
                "div[class*='Rating-']",
                "li[class*='Rating']",
                "div[class*='RatingItem']"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        review_elements = elements
                        logger.debug(f"Found {len(elements)} review elements using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not review_elements:
                logger.warning("No review elements found on page")
                return reviews
            
            logger.info(f"Extracting data from {len(review_elements)} reviews...")
            
            # Extract data from each review element
            for idx, element in enumerate(review_elements):
                try:
                    review = self._parse_review_element(element)
                    if review:
                        reviews.append(review)
                        logger.debug(f"Successfully parsed review {idx + 1}/{len(review_elements)}")
                except Exception as e:
                    logger.warning(f"Error parsing review {idx + 1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(reviews)} reviews")
            return reviews
            
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
            return reviews
    
    def _parse_review_element(self, element) -> Review:
        """
        Parse a single review element and extract all fields with error handling.
        
        Args:
            element: WebElement containing review data
            
        Returns:
            Review object with extracted data
        """
        # Extract course code
        course_code = self._extract_course_code(element)
        
        # Extract metadata fields (for_credit, attendance, grade, textbook_used)
        for_credit = self._extract_for_credit(element)
        attendance = self._extract_attendance(element)
        grade = self._extract_grade(element)
        textbook_used = self._extract_textbook_used(element)
        
        # Extract quality and difficulty scores
        quality_score = self._extract_quality_score(element)
        difficulty_score = self._extract_difficulty_score(element)
        
        # Extract review text
        review_text = self._extract_review_text(element)
        
        # Extract tags
        tags = self._extract_review_tags(element)
        
        # Extract date posted
        date_posted = self._extract_date_posted(element)
        
        # Extract helpful votes
        helpful_upvotes, helpful_downvotes = self._extract_helpful_votes(element)
        
        # Create Review object
        review = Review(
            course_code=course_code,
            for_credit=for_credit,
            attendance=attendance,
            grade=grade,
            textbook_used=textbook_used,
            quality_score=quality_score,
            difficulty_score=difficulty_score,
            review_text=review_text,
            tags=tags,
            date_posted=date_posted,
            helpful_upvotes=helpful_upvotes,
            helpful_downvotes=helpful_downvotes
        )
        
        return review
    
    def _extract_course_code(self, element) -> str:
        """Extract course code from review element."""
        try:
            # Try multiple selectors for course code
            selectors = [
                "div[class*='RatingHeader__StyledClass']",
                "div[class*='CourseName']",
                "div[class*='Class']"
            ]
            
            for selector in selectors:
                try:
                    course_element = element.find_element(By.CSS_SELECTOR, selector)
                    course_code = self.cleaner.clean_text(course_element.text)
                    if course_code:
                        return course_code
                except NoSuchElementException:
                    continue
            
            logger.debug("Course code not found, using 'Unknown'")
            return "Unknown"
            
        except Exception as e:
            logger.debug(f"Error extracting course code: {e}")
            return "Unknown"
    
    def _extract_for_credit(self, element) -> bool:
        """Extract for_credit field from review element."""
        try:
            # Look for "For Credit" indicator
            text = element.text.lower()
            
            # Check for explicit indicators
            if 'for credit: yes' in text or 'credit: yes' in text:
                return True
            elif 'for credit: no' in text or 'credit: no' in text:
                return False
            
            # Try to find specific element
            selectors = [
                "div[class*='MetaItem'][class*='Credit']",
                "span[class*='Credit']"
            ]
            
            for selector in selectors:
                try:
                    credit_element = element.find_element(By.CSS_SELECTOR, selector)
                    credit_text = credit_element.text.lower()
                    return 'yes' in credit_text
                except NoSuchElementException:
                    continue
            
            # Default to True if not specified
            return True
            
        except Exception as e:
            logger.debug(f"Error extracting for_credit: {e}")
            return True
    
    def _extract_attendance(self, element) -> str:
        """Extract attendance field from review element."""
        try:
            # Look for attendance information
            text = element.text
            
            # Try to find specific element
            selectors = [
                "div[class*='MetaItem'][class*='Attendance']",
                "span[class*='Attendance']"
            ]
            
            for selector in selectors:
                try:
                    attendance_element = element.find_element(By.CSS_SELECTOR, selector)
                    attendance_text = self.cleaner.clean_text(attendance_element.text)
                    # Extract the value after the label
                    if ':' in attendance_text:
                        attendance = attendance_text.split(':', 1)[1].strip()
                        return attendance
                    return attendance_text
                except NoSuchElementException:
                    continue
            
            # Try to extract from full text using regex
            import re
            match = re.search(r'Attendance:\s*(\w+)', text, re.IGNORECASE)
            if match:
                return match.group(1)
            
            return "Not Specified"
            
        except Exception as e:
            logger.debug(f"Error extracting attendance: {e}")
            return "Not Specified"
    
    def _extract_grade(self, element) -> str:
        """Extract grade field from review element."""
        try:
            # Look for grade information
            text = element.text
            
            # Try to find specific element
            selectors = [
                "div[class*='MetaItem'][class*='Grade']",
                "span[class*='Grade']"
            ]
            
            for selector in selectors:
                try:
                    grade_element = element.find_element(By.CSS_SELECTOR, selector)
                    grade_text = self.cleaner.clean_text(grade_element.text)
                    # Extract the value after the label
                    if ':' in grade_text:
                        grade = grade_text.split(':', 1)[1].strip()
                        return grade
                    return grade_text
                except NoSuchElementException:
                    continue
            
            # Try to extract from full text using regex
            import re
            match = re.search(r'Grade\s*(?:Received)?:\s*([A-F][+-]?|Pass|Fail|Incomplete|Withdraw|Audit|Not sure yet|Rather not say)', text, re.IGNORECASE)
            if match:
                return match.group(1)
            
            return "Not Specified"
            
        except Exception as e:
            logger.debug(f"Error extracting grade: {e}")
            return "Not Specified"
    
    def _extract_textbook_used(self, element) -> str:
        """Extract textbook_used field from review element."""
        try:
            # Look for textbook information
            text = element.text
            
            # Try to find specific element
            selectors = [
                "div[class*='MetaItem'][class*='Textbook']",
                "span[class*='Textbook']"
            ]
            
            for selector in selectors:
                try:
                    textbook_element = element.find_element(By.CSS_SELECTOR, selector)
                    textbook_text = self.cleaner.clean_text(textbook_element.text)
                    # Extract the value after the label
                    if ':' in textbook_text:
                        textbook = textbook_text.split(':', 1)[1].strip()
                        return textbook
                    return textbook_text
                except NoSuchElementException:
                    continue
            
            # Try to extract from full text using regex
            import re
            match = re.search(r'Textbook:\s*(\w+(?:\s+\w+)?)', text, re.IGNORECASE)
            if match:
                return match.group(1)
            
            return "Not Specified"
            
        except Exception as e:
            logger.debug(f"Error extracting textbook_used: {e}")
            return "Not Specified"
    
    def _extract_quality_score(self, element) -> float:
        """Extract quality score from review element."""
        try:
            # Try multiple selectors for quality rating
            selectors = [
                "div[class*='CardNumRating__CardNumRatingNumber'][class*='quality']",
                "div[class*='Quality'] div[class*='CardNumRating']",
                "div[class*='RatingValues__RatingValue']:first-child"
            ]
            
            for selector in selectors:
                try:
                    quality_element = element.find_element(By.CSS_SELECTOR, selector)
                    quality_text = quality_element.text.strip()
                    quality = self.cleaner.parse_number(quality_text)
                    if quality is not None:
                        return quality
                except NoSuchElementException:
                    continue
            
            # Try to find any element with "QUALITY" text nearby
            try:
                # Look for elements containing rating numbers
                rating_elements = element.find_elements(By.CSS_SELECTOR, "div[class*='CardNumRating']")
                if len(rating_elements) >= 1:
                    quality_text = rating_elements[0].text.strip()
                    quality = self.cleaner.parse_number(quality_text)
                    if quality is not None:
                        return quality
            except Exception:
                pass
            
            logger.debug("Quality score not found, using 0.0")
            return 0.0
            
        except Exception as e:
            logger.debug(f"Error extracting quality score: {e}")
            return 0.0
    
    def _extract_difficulty_score(self, element) -> float:
        """Extract difficulty score from review element."""
        try:
            # Try multiple selectors for difficulty rating
            selectors = [
                "div[class*='CardNumRating__CardNumRatingNumber'][class*='difficulty']",
                "div[class*='Difficulty'] div[class*='CardNumRating']",
                "div[class*='RatingValues__RatingValue']:last-child"
            ]
            
            for selector in selectors:
                try:
                    difficulty_element = element.find_element(By.CSS_SELECTOR, selector)
                    difficulty_text = difficulty_element.text.strip()
                    difficulty = self.cleaner.parse_number(difficulty_text)
                    if difficulty is not None:
                        return difficulty
                except NoSuchElementException:
                    continue
            
            # Try to find any element with "DIFFICULTY" text nearby
            try:
                # Look for elements containing rating numbers
                rating_elements = element.find_elements(By.CSS_SELECTOR, "div[class*='CardNumRating']")
                if len(rating_elements) >= 2:
                    difficulty_text = rating_elements[1].text.strip()
                    difficulty = self.cleaner.parse_number(difficulty_text)
                    if difficulty is not None:
                        return difficulty
            except Exception:
                pass
            
            logger.debug("Difficulty score not found, using 0.0")
            return 0.0
            
        except Exception as e:
            logger.debug(f"Error extracting difficulty score: {e}")
            return 0.0
    
    def _extract_review_text(self, element) -> str:
        """Extract and clean review text from review element."""
        try:
            # Try multiple selectors for review comment text
            selectors = [
                "div[class*='Comments__StyledComments']",
                "div[class*='RatingComment']",
                "div[class*='CommentText']",
                "div[class*='Comment']"
            ]
            
            for selector in selectors:
                try:
                    text_element = element.find_element(By.CSS_SELECTOR, selector)
                    review_text = self.cleaner.clean_text(text_element.text)
                    if review_text:
                        return review_text
                except NoSuchElementException:
                    continue
            
            logger.debug("Review text not found")
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting review text: {e}")
            return ""
    
    def _extract_review_tags(self, element) -> List[str]:
        """Extract tags from review element."""
        tags = []
        
        try:
            # Try multiple selectors for tags
            selectors = [
                "span[class*='Tag-']",
                "div[class*='RatingTag']",
                "span[class*='RatingTag']"
            ]
            
            tag_elements = []
            for selector in selectors:
                try:
                    elements = element.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        tag_elements = elements
                        break
                except NoSuchElementException:
                    continue
            
            # Extract text from each tag
            for tag_element in tag_elements:
                try:
                    tag_text = self.cleaner.clean_text(tag_element.text)
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)
                except Exception:
                    continue
            
            return tags
            
        except Exception as e:
            logger.debug(f"Error extracting review tags: {e}")
            return tags
    
    def _extract_date_posted(self, element) -> str:
        """Extract date posted from review element."""
        try:
            # Try multiple selectors for date
            selectors = [
                "div[class*='TimeStamp']",
                "div[class*='Date']",
                "time",
                "span[class*='Date']"
            ]
            
            for selector in selectors:
                try:
                    date_element = element.find_element(By.CSS_SELECTOR, selector)
                    date_text = self.cleaner.clean_text(date_element.text)
                    if date_text:
                        return date_text
                except NoSuchElementException:
                    continue
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting date posted: {e}")
            return ""
    
    def _extract_helpful_votes(self, element) -> tuple:
        """
        Extract helpful upvotes and downvotes from review element.
        
        Returns:
            Tuple of (upvotes, downvotes)
        """
        upvotes = 0
        downvotes = 0
        
        try:
            # Try to find helpful/not helpful buttons or counts
            selectors = [
                "div[class*='Helpful']",
                "button[class*='Helpful']",
                "div[class*='Thumbs']"
            ]
            
            for selector in selectors:
                try:
                    helpful_elements = element.find_elements(By.CSS_SELECTOR, selector)
                    
                    for helpful_element in helpful_elements:
                        text = helpful_element.text.lower()
                        
                        # Extract numbers from text
                        import re
                        numbers = re.findall(r'\d+', text)
                        
                        if 'helpful' in text and numbers:
                            upvotes = int(numbers[0])
                        elif 'not helpful' in text and numbers:
                            downvotes = int(numbers[0])
                        elif 'thumbs up' in text and numbers:
                            upvotes = int(numbers[0])
                        elif 'thumbs down' in text and numbers:
                            downvotes = int(numbers[0])
                    
                    if upvotes > 0 or downvotes > 0:
                        break
                        
                except NoSuchElementException:
                    continue
            
            return upvotes, downvotes
            
        except Exception as e:
            logger.debug(f"Error extracting helpful votes: {e}")
            return 0, 0
