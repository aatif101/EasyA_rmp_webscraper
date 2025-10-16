"""Quick test script for ProfessorListScraper"""

import logging
from src.utils.webdriver_manager import WebDriverManager
from src.scrapers import ProfessorListScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_list_scraper():
    """Test the professor list scraper with a limited run"""
    
    # Initialize WebDriver
    manager = WebDriverManager(headless=False)  # Set to False to see the browser
    driver = manager.get_driver()
    
    try:
        # Create scraper instance
        base_url = "https://www.ratemyprofessors.com/search/professors/1262?q=*"
        scraper = ProfessorListScraper(driver, base_url)
        
        # Run the scraping workflow
        professors = scraper.scrape(save_output=True, output_file="test_output.json")
        
        print(f"\n{'='*60}")
        print(f"Scraping Complete!")
        print(f"{'='*60}")
        print(f"Total professors extracted: {len(professors)}")
        
        if professors:
            print(f"\nFirst professor:")
            first = professors[0]
            print(f"  Name: {first.professor_name}")
            print(f"  Department: {first.department}")
            print(f"  Ratings: {first.num_ratings}")
            print(f"  Quality: {first.avg_quality}")
            print(f"  Difficulty: {first.avg_difficulty}")
            print(f"  Would take again: {first.would_take_again_pct}%")
            print(f"  URL: {first.professor_page_url}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        manager.quit_driver()

if __name__ == "__main__":
    test_list_scraper()
