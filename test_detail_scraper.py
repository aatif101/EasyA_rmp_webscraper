"""Test script for ProfessorDetailScraper."""

import logging
from src.utils.webdriver_manager import WebDriverManager
from src.scrapers.detail_scraper import ProfessorDetailScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_detail_scraper():
    """Test the ProfessorDetailScraper with a real professor page."""
    
    # Initialize WebDriver
    driver_manager = WebDriverManager(headless=False)
    driver = driver_manager.get_driver()
    
    try:
        # Create scraper instance
        scraper = ProfessorDetailScraper(driver)
        
        # Test with a sample professor URL (you'll need to replace with actual URL)
        test_url = "https://www.ratemyprofessors.com/professor/2450730"
        
        print(f"\nTesting ProfessorDetailScraper with URL: {test_url}")
        print("=" * 80)
        
        # Scrape professor data
        professor = scraper.scrape_professor(test_url)
        
        if professor:
            print(f"\n✓ Successfully scraped professor data!")
            print(f"\nProfessor Name: {professor.professor_name}")
            print(f"Department: {professor.department}")
            print(f"Overall Quality: {professor.overall_quality}")
            print(f"Difficulty Level: {professor.difficulty_level}")
            print(f"Would Take Again: {professor.would_take_again}%")
            print(f"\nRating Distribution:")
            for category, count in professor.rating_distribution.items():
                print(f"  {category}: {count}")
            print(f"\nTags ({len(professor.tags)}):")
            for tag in professor.tags:
                print(f"  - {tag}")
            
            # Validate the data
            try:
                professor.validate()
                print(f"\n✓ Data validation passed!")
            except ValueError as e:
                print(f"\n✗ Data validation failed: {e}")
        else:
            print("\n✗ Failed to scrape professor data")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        driver_manager.quit_driver()
        print("\n" + "=" * 80)
        print("Test completed")

if __name__ == "__main__":
    test_detail_scraper()
