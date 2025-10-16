"""
RateMyProfessor Scraper for University of South Florida
Main entry point with command-line interface
"""
import argparse
import sys
import logging
import json
import time
import random
from pathlib import Path
from typing import List

from src.utils.webdriver_manager import WebDriverManager
from src.scrapers.list_scraper import ProfessorListScraper
from src.scrapers.detail_scraper import ProfessorDetailScraper
from src.utils.json_writer import JSONWriter
from src.models import Professor


def setup_logging():
    """Configure logging for the scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Scrape professor and review data from RateMyProfessor for USF'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='usf_professors.json',
        help='Output file path (default: usf_professors.json)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.5,
        help='Delay between requests in seconds (default: 1.5)'
    )
    
    parser.add_argument(
        '--max-professors',
        type=int,
        default=None,
        help='Maximum number of professors to scrape (for testing)'
    )
    
    return parser.parse_args()


def run_scraping_workflow(args) -> tuple[List[Professor], List[str], List[str]]:
    """
    Main scraping workflow that orchestrates all scraping operations.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Tuple of (professors, errors, skipped_professors)
    """
    logger = logging.getLogger(__name__)
    professors = []
    start_time = time.time()
    
    # Initialize WebDriverManager
    logger.info("Initializing WebDriver...")
    webdriver_manager = WebDriverManager(headless=args.headless, timeout=10)
    driver = webdriver_manager.get_driver()
    
    try:
        # Run ProfessorListScraper to get all professor URLs
        logger.info("Starting professor list scraping...")
        base_url = "https://www.ratemyprofessors.com/search/professors/1262?q=*"
        list_scraper = ProfessorListScraper(driver, base_url)
        
        professor_summaries = list_scraper.scrape(save_output=True, output_file="usf_professors_main.json")
        
        # Apply max-professors limit if specified
        if args.max_professors:
            professor_summaries = professor_summaries[:args.max_professors]
            logger.info(f"Limited to {args.max_professors} professors for testing")
        
        total_professors = len(professor_summaries)
        logger.info(f"Found {total_professors} professors to scrape")
        
        # Initialize detail scraper
        detail_scraper = ProfessorDetailScraper(driver)
        
        # Track progress metrics
        successful_count = 0
        failed_count = 0
        total_reviews = 0
        errors = []
        skipped_professors = []
        
        # Loop through each professor URL
        for idx, prof_summary in enumerate(professor_summaries, 1):
            try:
                # Calculate and display progress
                progress_pct = (idx / total_professors) * 100
                elapsed_time = time.time() - start_time
                
                # Estimate time remaining based on average time per professor
                if idx > 1:
                    avg_time_per_prof = elapsed_time / (idx - 1)
                    remaining_profs = total_professors - idx + 1
                    estimated_remaining = avg_time_per_prof * remaining_profs
                    eta_minutes = estimated_remaining / 60
                    
                    logger.info(f"Progress: {idx}/{total_professors} ({progress_pct:.1f}%) | "
                              f"Elapsed: {elapsed_time/60:.1f}m | "
                              f"ETA: {eta_minutes:.1f}m | "
                              f"Success: {successful_count} | Failed: {failed_count}")
                
                logger.info(f"Processing professor {idx}/{total_professors}: {prof_summary.professor_name}")
                
                # Add rate limiting with randomized delay
                if idx > 1:  # Skip delay for first professor
                    delay = args.delay + random.uniform(-0.3, 0.3)  # Randomize delay slightly
                    logger.debug(f"Waiting {delay:.2f} seconds before next request...")
                    time.sleep(delay)
                
                # For each URL: run ProfessorDetailScraper and ReviewScraper
                professor = detail_scraper.scrape_professor(prof_summary.professor_page_url)
                
                # Collect Professor objects
                if professor:
                    professors.append(professor)
                    successful_count += 1
                    total_reviews += len(professor.reviews)
                    logger.info(f"✓ Successfully scraped {prof_summary.professor_name} "
                              f"({len(professor.reviews)} reviews)")
                else:
                    failed_count += 1
                    skipped_professors.append(prof_summary.professor_name)
                    logger.warning(f"✗ Failed to scrape professor: {prof_summary.professor_name}")
                
                # Log progress at regular intervals (every 10 professors)
                if idx % 10 == 0:
                    logger.info("=" * 60)
                    logger.info(f"PROGRESS UPDATE: {idx}/{total_professors} professors processed")
                    logger.info(f"Successful: {successful_count} | Failed: {failed_count}")
                    logger.info(f"Total reviews collected: {total_reviews}")
                    logger.info(f"Time elapsed: {elapsed_time/60:.1f} minutes")
                    logger.info("=" * 60)
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Error processing professor {prof_summary.professor_name}: {e}"
                errors.append(error_msg)
                skipped_professors.append(prof_summary.professor_name)
                logger.error(error_msg)
                continue
        
        # Final summary
        total_time = time.time() - start_time
        logger.info("=" * 80)
        logger.info("SCRAPING WORKFLOW COMPLETE")
        logger.info(f"Total professors processed: {total_professors}")
        logger.info(f"Successfully scraped: {successful_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total reviews collected: {total_reviews}")
        logger.info(f"Total time: {total_time/60:.1f} minutes")
        logger.info(f"Average time per professor: {total_time/total_professors:.1f} seconds")
        logger.info("=" * 80)
        
    finally:
        # Clean up WebDriver
        logger.info("Closing WebDriver...")
        webdriver_manager.quit_driver()
    
    return professors, errors, skipped_professors


def save_professors_to_json(professors: List[Professor], output_file: str):
    """
    Save professor data to JSON file using JSONWriter.
    
    Args:
        professors: List of Professor objects
        output_file: Output file path
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Use JSONWriter to handle serialization, validation, and writing
        json_writer = JSONWriter()
        success = json_writer.save_professors(professors, output_file)
        
        if not success:
            raise Exception("Failed to save professors to JSON")
        
    except Exception as e:
        logger.error(f"Error saving to JSON: {e}")
        raise


def main():
    """Main execution function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    args = parse_arguments()
    
    logger.info("=" * 80)
    logger.info("Starting RateMyProfessor scraper for USF")
    logger.info("=" * 80)
    logger.info(f"Configuration: headless={args.headless}, output={args.output}, "
                f"delay={args.delay}, max_professors={args.max_professors}")
    
    try:
        # Run the main scraping workflow
        professors, errors, skipped_professors = run_scraping_workflow(args)
        
        # Save results to JSON and generate summary report
        if professors:
            save_professors_to_json(professors, args.output)
            
            # Generate and log summary report
            json_writer = JSONWriter()
            summary = json_writer.generate_summary_report(professors, errors, skipped_professors)
            json_writer.log_summary_report(summary)
            json_writer.save_summary_report(summary, "scraping_summary.json")
            
            logger.info("=" * 80)
            logger.info(f"Scraping complete! Collected {len(professors)} professors")
            logger.info(f"Total reviews: {sum(len(p.reviews) for p in professors)}")
            logger.info(f"Output saved to: {args.output}")
            logger.info(f"Summary report saved to: scraping_summary.json")
            logger.info("=" * 80)
        else:
            logger.warning("No professors were successfully scraped")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error during scraping: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
