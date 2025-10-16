# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create directory structure: `src/`, `src/scrapers/`, `src/models/`, `src/utils/`
  - Create `requirements.txt` with selenium, beautifulsoup4, webdriver-manager
  - Create `main.py` entry point with argument parsing
  - _Requirements: 1.1, 5.1_

- [x] 2. Implement data models






  - [x] 2.1 Create data model classes using Python dataclasses

    - Define `ProfessorSummary` dataclass with all fields from main listing
    - Define `Professor` dataclass with metadata and reviews list
    - Define `Review` dataclass with all review fields
    - Add type hints for all fields
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 2.2 Add data model validation methods


    - Implement `to_dict()` methods for JSON serialization
    - Add validation for required fields
    - _Requirements: 5.5, 4.2, 4.3_

- [-] 3. Implement data cleaning utilities


  - [x] 3.1 Create DataCleaner class with text cleaning methods



    - Implement `clean_text()` to remove HTML, emojis, and normalize whitespace
    - Implement `parse_number()` to convert string numbers to float
    - Implement `parse_percentage()` to extract percentage values
    - Implement `parse_boolean()` for boolean field conversion
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 3.2 Write unit tests for data cleaning functions
    - Test text cleaning with various HTML and emoji inputs
    - Test number parsing with edge cases (N/A, missing, malformed)
    - Test percentage extraction
    - _Requirements: 4.1, 4.2_

- [x] 4. Implement WebDriver manager






  - [x] 4.1 Create WebDriverManager class

    - Initialize Chrome WebDriver with headless option
    - Configure timeouts and implicit waits
    - Add user-agent configuration
    - Implement `get_driver()` and `quit_driver()` methods
    - _Requirements: 1.1, 6.1_
  

  - [x] 4.2 Add helper methods for element interaction

    - Implement `wait_for_element()` with explicit wait
    - Implement `click_with_retry()` with retry logic
    - Add `scroll_to_element()` helper
    - _Requirements: 6.2, 6.3_

- [x] 5. Implement professor list scraper




  - [x] 5.1 Create ProfessorListScraper class


    - Initialize with WebDriver and base URL
    - Navigate to USF professor listing page
    - _Requirements: 1.1_
  
  - [x] 5.2 Implement pagination handling


    - Implement `_click_show_more()` to find and click "Show More" button using XPath
    - Implement `load_all_professors()` to click until button disappears
    - Add delay between clicks to avoid rate limiting
    - _Requirements: 1.3, 1.6_
  


  - [x] 5.3 Implement professor card extraction




    - Locate all professor cards using `a[class^='TeacherCard__StyledTeacherCard']`
    - Extract professor_name, department, university from each card
    - Extract num_ratings, avg_quality, avg_difficulty, would_take_again_pct
    - Extract professor_page_url from card link
    - Return list of ProfessorSummary objects


    - _Requirements: 1.2, 1.4_
  -

  - [x] 5.4 Save main listing results to JSON



    - Implement method to save ProfessorSummary list to `usf_professors_main.json`
    - Use UTF-8 encoding
    - _Requirements: 1.5, 4.4_
-

- [x] 6. Implement professor detail scraper





  - [x] 6.1 Create ProfessorDetailScraper class

    - Initialize with WebDriver
    - Implement `scrape_professor(url)` orchestration method
    - _Requirements: 2.1_
  

  - [x] 6.2 Implement metadata extraction

    - Extract professor_name, department from detail page
    - Extract overall_quality, difficulty_level, would_take_again
    - Implement retry logic for missing elements
    - _Requirements: 2.2, 2.5_
  
  - [x] 6.3 Implement rating distribution extraction


    - Locate rating distribution section
    - Extract counts for "Awesome", "Great", "Good", "OK", "Awful"
    - Return as dictionary
    - _Requirements: 2.3_
  

  - [x] 6.4 Implement tag extraction

    - Locate all tag elements on professor page
    - Extract tag text and return as list
    - _Requirements: 2.4_

- [x] 7. Implement review scraper




  - [x] 7.1 Create ReviewScraper class


    - Initialize with WebDriver
    - _Requirements: 3.1_
  
  - [x] 7.2 Implement review pagination


    - Implement `load_all_reviews()` to click "Load More Ratings" repeatedly
    - Scroll to button before clicking
    - Stop when button is no longer present
    - _Requirements: 3.1, 3.5_
  
  - [x] 7.3 Implement review extraction


    - Locate all review elements on page
    - Extract course_code, for_credit, attendance, grade, textbook_used
    - Extract quality_score, difficulty_score as floats
    - Extract review_text and clean it
    - Extract tags as list
    - Extract date_posted, helpful_upvotes, helpful_downvotes
    - Return list of Review objects
    - _Requirements: 3.2_
  
  - [x] 7.4 Integrate reviews with professor data


    - Combine metadata and reviews into Professor object
    - Ensure reviews are nested under "reviews" field
    - _Requirements: 3.3, 3.4_

- [x] 8. Implement error handling and logging




  - [x] 8.1 Create ErrorHandler class


    - Implement `retry_with_backoff()` with exponential backoff
    - Implement `handle_missing_element()` with single retry
    - Add logging for all error types
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 8.2 Configure logging system


    - Set up logging with INFO, WARNING, ERROR levels
    - Configure file handler with rotation (10MB, 3 backups)
    - Add console handler for progress updates
    - _Requirements: 6.6_
  
  - [x] 8.3 Add error recovery to scrapers


    - Wrap network requests with retry logic
    - Handle rate limiting with delays
    - Skip failed professors and continue
    - Log all errors with context
    - _Requirements: 6.4, 6.5_

- [ ] 9. Implement main orchestrator
  - [ ] 9.1 Create main scraping workflow
    - Initialize WebDriverManager
    - Run ProfessorListScraper to get all professor URLs
    - Loop through each professor URL
    - For each URL: run ProfessorDetailScraper and ReviewScraper
    - Collect all Professor objects
    - _Requirements: 1.1, 2.1, 3.6_
  
  - [ ] 9.2 Add progress tracking
    - Implement progress bar or counter
    - Log progress at regular intervals
    - Display estimated time remaining
    - _Requirements: 6.6_
  
  - [ ] 9.3 Implement rate limiting
    - Add 1-2 second delay between professor page requests
    - Randomize delays slightly
    - _Requirements: 6.4_

- [ ] 10. Implement JSON output writer
  - [ ] 10.1 Create JSONWriter class
    - Implement method to serialize Professor objects to JSON
    - Ensure UTF-8 encoding
    - Format JSON with indentation for readability
    - _Requirements: 4.4, 5.1_
  
  - [ ] 10.2 Write final output file
    - Save all Professor objects to `usf_professors.json`
    - Validate JSON structure before writing
    - Handle write errors gracefully
    - _Requirements: 5.1, 5.5_
  
  - [ ] 10.3 Generate scraping summary report
    - Count total professors scraped
    - Count total reviews collected
    - List any errors or skipped professors
    - Save summary to log and console
    - _Requirements: 6.6_

- [ ] 11. Add command-line interface
  - [ ] 11.1 Implement argument parsing
    - Add `--headless` flag (default: True)
    - Add `--output` option for output file path
    - Add `--delay` option for request delay
    - Add `--max-professors` option for testing
    - _Requirements: 1.1_
  
  - [ ] 11.2 Wire up CLI to main orchestrator
    - Pass CLI arguments to WebDriverManager and scrapers
    - Handle invalid arguments gracefully
    - Display help message
    - _Requirements: 1.1_

- [ ]* 12. Integration testing
  - [ ]* 12.1 Test full scraping workflow
    - Run scraper with `--max-professors 5` for quick test
    - Verify all 5 professors are scraped with reviews
    - Validate output JSON structure
    - _Requirements: 5.5_
  
  - [ ]* 12.2 Test error handling
    - Simulate network failures
    - Test with invalid URLs
    - Verify graceful degradation
    - _Requirements: 6.1, 6.2, 6.5_

- [ ] 13. Documentation and final touches
  - [ ] 13.1 Create README.md
    - Document installation steps
    - Provide usage examples
    - Explain output format
    - List requirements and dependencies
    - _Requirements: 5.1_
  
  - [ ] 13.2 Add inline code comments
    - Document complex selector logic
    - Explain retry strategies
    - Add docstrings to all classes and methods
    - _Requirements: 4.1, 4.5_
