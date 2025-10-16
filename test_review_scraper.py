"""Test script for ReviewScraper functionality."""

import logging
from src.utils.webdriver_manager import WebDriverManager
from src.scrapers.detail_scraper import ProfessorDetailScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_review_scraper():
    """Test the review scraper with a real professor page."""
    
    # Initialize WebDriver
    logger.info("Initializing WebDriver...")
    driver_manager = WebDriverManager(headless=False)  # Set to False to see the browser
    driver = driver_manager.get_driver()
    
    try:
        # Test with a USF professor page
        # Using a professor URL from the USF listing
        test_url = "https://www.ratemyprofessors.com/professor/2166891"  # Example professor
        
        logger.info(f"Testing with professor URL: {test_url}")
        
        # Create detail scraper (which includes review scraper)
        detail_scraper = ProfessorDetailScraper(driver)
        
        # Scrape professor data (includes reviews)
        professor = detail_scraper.scrape_professor(test_url)
        
        if professor:
            logger.info(f"\n{'='*60}")
            logger.info(f"Professor: {professor.professor_name}")
            logger.info(f"Department: {professor.department}")
            logger.info(f"Overall Quality: {professor.overall_quality}")
            logger.info(f"Difficulty: {professor.difficulty_level}")
            logger.info(f"Would Take Again: {professor.would_take_again}%")
            logger.info(f"Tags: {professor.tags}")
            logger.info(f"Rating Distribution: {professor.rating_distribution}")
            logger.info(f"\nTotal Reviews: {len(professor.reviews)}")
            logger.info(f"{'='*60}\n")
            
            # Display first 3 reviews as sample
            for idx, review in enumerate(professor.reviews[:3], 1):
                logger.info(f"\nReview {idx}:")
                logger.info(f"  Course: {review.course_code}")
                logger.info(f"  Quality: {review.quality_score}, Difficulty: {review.difficulty_score}")
                logger.info(f"  For Credit: {review.for_credit}")
                logger.info(f"  Attendance: {review.attendance}")
                logger.info(f"  Grade: {review.grade}")
                logger.info(f"  Textbook: {review.textbook_used}")
                logger.info(f"  Tags: {review.tags}")
                logger.info(f"  Date: {review.date_posted}")
                logger.info(f"  Helpful: {review.helpful_upvotes} up, {review.helpful_downvotes} down")
                logger.info(f"  Text: {review.review_text[:100]}..." if len(review.review_text) > 100 else f"  Text: {review.review_text}")
            
            if len(professor.reviews) > 3:
                logger.info(f"\n... and {len(professor.reviews) - 3} more reviews")
            
            logger.info("\n✓ Review scraper test completed successfully!")
            return True
        else:
            logger.error("Failed to scrape professor data")
            return False
            
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return False
        
    finally:
        # Clean up
        logger.info("Closing WebDriver...")
        driver_manager.quit_driver()


if __name__ == "__main__":
    success = test_review_scraper()
    exit(0 if success else 1)
