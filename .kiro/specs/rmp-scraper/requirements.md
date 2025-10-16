# Requirements Document

## Introduction

The EasyA RateMyProfessor Scraper is a web scraping tool designed to collect comprehensive professor and review data from RateMyProfessor for the University of South Florida (USF). The scraped data will be used to power an AI-driven class difficulty ranking application that helps students make informed decisions about course selection. The scraper must extract structured data from both the main professor listing page and individual professor detail pages, ensuring data quality and consistency for downstream AI processing and RAG-based search functionality.

## Requirements

### Requirement 1: Main Professor Listing Page Scraping

**User Story:** As a data collector, I want to scrape all professor summary information from the USF RateMyProfessor listing page, so that I have a complete dataset of all professors to process further.

#### Acceptance Criteria

1. WHEN the scraper starts THEN it SHALL navigate to the URL "https://www.ratemyprofessors.com/search/professors/1262?q=*"
2. WHEN the main listing page loads THEN the scraper SHALL identify all professor cards using the selector `a[class^='TeacherCard__StyledTeacherCard']`
3. WHEN professor cards are visible THEN the scraper SHALL click the "Show More" button repeatedly until all professors are loaded
4. WHEN all professors are loaded THEN the scraper SHALL extract the following fields from each card: professor_name, department, university, num_ratings, avg_quality, avg_difficulty, would_take_again_pct, and professor_page_url
5. WHEN extraction is complete THEN the scraper SHALL save the results to a local file named "usf_professors_main.json"
6. IF the "Show More" button is no longer present THEN the scraper SHALL consider all professors loaded

### Requirement 2: Individual Professor Page Metadata Extraction

**User Story:** As a data collector, I want to extract detailed metadata from each professor's individual page, so that I have comprehensive information about each professor's overall ratings and characteristics.

#### Acceptance Criteria

1. WHEN the main listing scrape is complete THEN the scraper SHALL visit each professor_page_url sequentially
2. WHEN a professor page loads THEN the scraper SHALL extract the following metadata: professor_name, department, overall_quality, difficulty_level, would_take_again percentage
3. WHEN metadata is extracted THEN the scraper SHALL extract the rating_distribution object containing counts for "Awesome", "Great", "Good", "OK", and "Awful"
4. WHEN rating distribution is extracted THEN the scraper SHALL extract all professor tags as an array
5. IF a metadata field is missing THEN the scraper SHALL retry the extraction once before marking it as null or N/A
6. WHEN all metadata is extracted THEN the scraper SHALL proceed to review extraction for that professor

### Requirement 3: Individual Professor Review Extraction

**User Story:** As a data collector, I want to extract all reviews for each professor with complete detail, so that the AI system can analyze student feedback and generate accurate difficulty rankings.

#### Acceptance Criteria

1. WHEN on a professor's page THEN the scraper SHALL scroll and click "Load More Ratings" until all reviews are visible
2. WHEN all reviews are loaded THEN the scraper SHALL extract the following fields from each review: course_code, for_credit, attendance, grade, textbook_used, quality_score, difficulty_score, review_text, tags, date_posted, helpful_upvotes, helpful_downvotes
3. WHEN reviews are extracted THEN the scraper SHALL group all reviews under their professor as a list in the "reviews" field
4. WHEN review extraction is complete for a professor THEN the scraper SHALL combine metadata and reviews into a single professor object
5. IF the "Load More Ratings" button is no longer present THEN the scraper SHALL consider all reviews loaded for that professor
6. WHEN all professors are processed THEN the scraper SHALL save the complete dataset to "usf_professors.json"

### Requirement 4: Data Quality and Cleaning

**User Story:** As a data engineer, I want all scraped data to be cleaned and properly formatted, so that it can be reliably imported into Supabase and used for AI processing without errors.

#### Acceptance Criteria

1. WHEN text content is extracted THEN the scraper SHALL remove HTML tags, emojis, advertisements, and excessive newlines
2. WHEN numeric values are extracted THEN the scraper SHALL convert them to numeric types (e.g., 4.8 as float, not "4.8" as string)
3. WHEN boolean values are extracted THEN the scraper SHALL ensure they are represented as true/false
4. WHEN saving data to JSON THEN the scraper SHALL use UTF-8 encoding
5. IF an expected element is missing during extraction THEN the scraper SHALL retry the extraction once before using a default value
6. WHEN data cleaning is complete THEN all fields SHALL conform to their expected data types as specified in the schema

### Requirement 5: Output Structure and Storage

**User Story:** As a system integrator, I want the scraped data to be saved in a consistent hierarchical JSON structure, so that it can be easily imported into Supabase and used for RAG-based AI search.

#### Acceptance Criteria

1. WHEN scraping is complete THEN the scraper SHALL produce a single JSON file named "usf_professors.json"
2. WHEN the JSON file is created THEN each entry SHALL represent one professor with all associated reviews nested under a "reviews" array
3. WHEN structuring professor data THEN the scraper SHALL include all metadata fields at the top level: professor_name, department, overall_quality, difficulty_level, would_take_again, rating_distribution, and tags
4. WHEN structuring review data THEN each review object SHALL contain all specified fields: course_code, for_credit, attendance, grade, textbook_used, quality_score, difficulty_score, review_text, tags, date_posted, helpful_upvotes, helpful_downvotes
5. WHEN the file is saved THEN it SHALL be valid JSON that can be parsed without errors
6. WHEN the structure is validated THEN it SHALL support hierarchical queries (professor → reviews) for AI processing

### Requirement 6: Error Handling and Resilience

**User Story:** As a system operator, I want the scraper to handle errors gracefully and continue processing, so that temporary issues don't cause complete failure of the scraping job.

#### Acceptance Criteria

1. WHEN a network error occurs THEN the scraper SHALL retry the request up to 3 times with exponential backoff
2. WHEN a page fails to load THEN the scraper SHALL log the error and continue to the next professor
3. WHEN an element selector fails THEN the scraper SHALL log the missing element and use a default value or null
4. WHEN the scraper encounters rate limiting THEN it SHALL wait and retry with appropriate delays
5. IF a professor page is completely inaccessible THEN the scraper SHALL skip that professor and continue with the next one
6. WHEN scraping completes THEN the scraper SHALL generate a summary report showing total professors scraped, total reviews collected, and any errors encountered
