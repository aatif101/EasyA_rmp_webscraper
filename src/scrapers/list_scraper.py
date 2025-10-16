"""Professor List Scraper for RateMyProfessor main listing page."""

import logging
import time
import json
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.models import ProfessorSummary
from src.utils.cleaner import DataCleaner
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class ProfessorListScraper:
    """Scrapes professor summary data from the main RateMyProfessor listing page."""
    
    def __init__(self, driver: webdriver.Chrome, base_url: str):
        """
        Initialize the professor list scraper.
        
        Args:
            driver: Selenium WebDriver instance
            base_url: URL of the USF professor listing page
        """
        self.driver = driver
        self.base_url = base_url
        self.cleaner = DataCleaner()
        self.error_handler = ErrorHandler(max_retries=3)
        
        logger.info(f"ProfessorListScraper initialized with URL: {base_url}")
    
    def navigate_to_listing(self):
        """Navigate to the USF professor listing page with retry logic."""
        def _navigate():
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(2)  # Wait for initial page load
            logger.info("Successfully navigated to listing page")
        
        try:
            self.error_handler.retry_with_backoff(_navigate)
        except Exception as e:
            self.error_handler.log_error(e, "navigating to listing page")
            raise

    def _click_show_more(self) -> bool:
        """
        Find and click the "Show More" button using XPath with error handling.
        
        Returns:
            True if button was found and clicked, False otherwise
        """
        try:
            # Use XPath to find the "Show More" button
            show_more_button = self.driver.find_element(
                By.XPATH, 
                "//button[contains(., 'Show More')]"
            )
            
            # Scroll to button and click
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", 
                show_more_button
            )
            time.sleep(0.5)  # Brief pause after scroll
            
            show_more_button.click()
            logger.debug("Clicked 'Show More' button")
            
            # Add delay to handle rate limiting
            time.sleep(1.5)
            return True
            
        except NoSuchElementException:
            logger.info("'Show More' button not found - all professors loaded")
            return False
        except Exception as e:
            logger.warning(f"Error clicking 'Show More' button: {e}")
            # Wait before retrying to handle rate limiting
            time.sleep(2)
            return False
    
    def load_all_professors(self) -> None:
        """
        Click "Show More" button repeatedly until all professors are loaded.
        Adds delay between clicks to avoid rate limiting.
        """
        logger.info("Starting to load all professors...")
        click_count = 0
        
        while True:
            try:
                # Try to click the "Show More" button
                if not self._click_show_more():
                    # Button not found or click failed - all professors loaded
                    break
                
                click_count += 1
                logger.info(f"Clicked 'Show More' {click_count} time(s)")
                
            except Exception as e:
                self.error_handler.log_error(e, f"loading professors (click {click_count})")
                logger.warning("Continuing to next iteration after error")
                time.sleep(2)  # Wait before continuing
                break
        
        logger.info(f"Finished loading professors after {click_count} clicks")
        time.sleep(1)  # Final wait for content to settle

    def extract_professor_cards(self) -> List[ProfessorSummary]:
        """
        Extract all professor cards from the loaded page.
        
        Returns:
            List of ProfessorSummary objects
        """
        logger.info("Starting professor card extraction...")
        professors = []
        
        try:
            # Locate all professor cards using CSS selector
            cards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[class^='TeacherCard__StyledTeacherCard']"
            )
            
            logger.info(f"Found {len(cards)} professor cards")
            
            for idx, card in enumerate(cards, 1):
                try:
                    professor = self._extract_single_card(card)
                    if professor:
                        professors.append(professor)
                        logger.debug(f"Extracted professor {idx}/{len(cards)}: {professor.professor_name}")
                except Exception as e:
                    logger.warning(f"Error extracting card {idx}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(professors)} professors")
            return professors
            
        except Exception as e:
            logger.error(f"Error during card extraction: {e}")
            return professors
    
    def _extract_single_card(self, card) -> ProfessorSummary:
        """
        Extract data from a single professor card element with error handling.
        
        Args:
            card: WebElement representing a professor card
            
        Returns:
            ProfessorSummary object or None if extraction fails
        """
        try:
            # Extract professor page URL from the card link
            professor_page_url = card.get_attribute('href')
            
            # Extract professor name
            name_element = card.find_element(
                By.CSS_SELECTOR, 
                "div[class*='CardName']"
            )
            professor_name = self.cleaner.clean_text(name_element.text)
            
            # Extract department and university from CardSchool section
            school_element = card.find_element(
                By.CSS_SELECTOR,
                "div[class*='CardSchool']"
            )
            school_text = school_element.text.strip()
            
            # Split department and university (format: "Department / University")
            parts = school_text.split('/')
            department = self.cleaner.clean_text(parts[0]) if len(parts) > 0 else "Unknown"
            university = self.cleaner.clean_text(parts[1]) if len(parts) > 1 else "University of South Florida"
            
            # Extract average quality rating
            quality_element = card.find_element(
                By.CSS_SELECTOR,
                "div[class*='CardNumRating']"
            )
            avg_quality = self.cleaner.parse_number(quality_element.text) or 0.0
            
            # Extract number of ratings
            num_ratings_element = card.find_element(
                By.CSS_SELECTOR,
                "div[class*='CardNumRating'] + div"
            )
            num_ratings_text = num_ratings_element.text
            num_ratings = self.cleaner.parse_number(num_ratings_text.split()[0]) or 0
            num_ratings = int(num_ratings)
            
            # Extract feedback items (difficulty and would take again)
            feedback_elements = card.find_elements(
                By.CSS_SELECTOR,
                "div[class*='CardFeedback']"
            )
            
            avg_difficulty = 0.0
            would_take_again_pct = None
            
            for feedback in feedback_elements:
                text = feedback.text.strip()
                
                # Check if this is the difficulty rating
                if "Level of Difficulty" in text or "difficulty" in text.lower():
                    # Extract the number from the text
                    difficulty_value = self.cleaner.parse_number(text.split()[0])
                    if difficulty_value is not None:
                        avg_difficulty = difficulty_value
                
                # Check if this is the "would take again" percentage
                elif "Would take again" in text or "would take again" in text.lower():
                    would_take_again_pct = self.cleaner.parse_percentage(text)
            
            # Create ProfessorSummary object
            professor = ProfessorSummary(
                professor_name=professor_name,
                department=department,
                university=university,
                num_ratings=num_ratings,
                avg_quality=avg_quality,
                avg_difficulty=avg_difficulty,
                would_take_again_pct=would_take_again_pct,
                professor_page_url=professor_page_url
            )
            
            # Validate the professor data
            professor.validate()
            
            return professor
            
        except Exception as e:
            logger.warning(f"Error extracting single card: {e}")
            return None

    def save_to_json(self, professors: List[ProfessorSummary], output_file: str = "usf_professors_main.json"):
        """
        Save professor summary list to JSON file with UTF-8 encoding.
        
        Args:
            professors: List of ProfessorSummary objects to save
            output_file: Output file path (default: usf_professors_main.json)
        """
        try:
            # Convert professors to dictionaries
            professors_data = [prof.to_dict() for prof in professors]
            
            # Write to JSON file with UTF-8 encoding
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(professors_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(professors)} professors to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            raise
    
    def scrape(self, save_output: bool = True, output_file: str = "usf_professors_main.json") -> List[ProfessorSummary]:
        """
        Main method to orchestrate the full scraping workflow.
        
        Args:
            save_output: Whether to save results to JSON file
            output_file: Output file path if saving
            
        Returns:
            List of ProfessorSummary objects
        """
        logger.info("Starting professor list scraping workflow...")
        
        # Navigate to the listing page
        self.navigate_to_listing()
        
        # Load all professors by clicking "Show More"
        self.load_all_professors()
        
        # Extract all professor cards
        professors = self.extract_professor_cards()
        
        # Save to JSON if requested
        if save_output:
            self.save_to_json(professors, output_file)
        
        logger.info(f"Scraping workflow complete. Extracted {len(professors)} professors.")
        return professors
