# Design Document: RateMyProfessor Scraper for EasyA

## Overview

The RateMyProfessor scraper is a Python-based web scraping application that uses Selenium WebDriver for dynamic content handling. The scraper follows a two-phase approach: first collecting professor summary data from the main listing page, then visiting each professor's individual page to extract detailed metadata and reviews. The architecture emphasizes modularity, error resilience, and data quality to ensure the output is ready for AI processing and database import.

## Architecture

### Technology Stack

- **Language**: Python 3.9+
- **Web Automation**: Selenium WebDriver with Chrome/ChromeDriver
- **HTML Parsing**: BeautifulSoup4 (for parsing extracted HTML)
- **Data Handling**: Python standard library (json, dataclasses)
- **Logging**: Python logging module

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Scraper                          │
│                     (orchestrator.py)                        │
└────────────┬────────────────────────────────────┬───────────┘
             │                                    │
             ▼                                    ▼
┌────────────────────────┐          ┌────────────────────────┐
│  Professor List        │          │  Professor Detail      │
│  Scraper               │          │  Scraper               │
│  (list_scraper.py)     │          │  (detail_scraper.py)   │
└────────┬───────────────┘          └────────┬───────────────┘
         │                                    │
         ▼                                    ▼
┌────────────────────────┐          ┌────────────────────────┐
│  Data Cleaner          │          │  Review Scraper        │
│  (cleaner.py)          │          │  (review_scraper.py)   │
└────────┬───────────────┘          └────────┬───────────────┘
         │                                    │
         └────────────────┬───────────────────┘
                          ▼
                ┌─────────────────────┐
                │  JSON Writer        │
                │  (writer.py)        │
                └─────────────────────┘
```

### Component Responsibilities

1. **Main Scraper (orchestrator.py)**: Coordinates the scraping workflow, manages WebDriver lifecycle, and handles high-level error recovery
2. **Professor List Scraper**: Handles pagination and extraction from the main listing page
3. **Professor Detail Scraper**: Extracts metadata from individual professor pages
4. **Review Scraper**: Handles review pagination and extraction
5. **Data Cleaner**: Normalizes and validates all extracted data
6. **JSON Writer**: Serializes cleaned data to JSON files

## Components and Interfaces

### 1. WebDriver Manager

**Purpose**: Centralized WebDriver initialization and configuration

```python
class WebDriverManager:
    def __init__(self, headless: bool = True, timeout: int = 10)
    def get_driver(self) -> webdriver.Chrome
    def quit_driver(self)
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR) -> WebElement
    def click_with_retry(self, element: WebElement, retries: int = 3) -> bool
```

**Configuration**:
- Headless mode for production
- 10-second default timeout
- User-agent rotation to avoid detection
- Implicit wait of 5 seconds

### 2. Professor List Scraper

**Purpose**: Extract all professors from the main listing page

```python
class ProfessorListScraper:
    def __init__(self, driver: webdriver.Chrome, base_url: str)
    def load_all_professors(self) -> None
    def extract_professor_cards(self) -> List[ProfessorSummary]
    def _click_show_more(self) -> bool
```

**Key Methods**:
- `load_all_professors()`: Clicks "Show More" until all professors are loaded
- `extract_professor_cards()`: Parses all visible cards and returns structured data
- Uses XPath `//button[contains(., 'Show More')]` for pagination button

**Selectors**:
- Card: `a[class^='TeacherCard__StyledTeacherCard']`
- Quality rating: `div[class^='TeacherCard__NumRatingWrapper']`
- Info block: `div[class^='TeacherCard__CardInfo']`

### 3. Professor Detail Scraper

**Purpose**: Extract metadata and reviews from individual professor pages

```python
class ProfessorDetailScraper:
    def __init__(self, driver: webdriver.Chrome)
    def scrape_professor(self, url: str) -> Professor
    def extract_metadata(self) -> ProfessorMetadata
    def extract_rating_distribution(self) -> Dict[str, int]
    def extract_tags(self) -> List[str]
```

**Key Methods**:
- `scrape_professor()`: Orchestrates metadata and review extraction
- `extract_metadata()`: Pulls overall ratings and stats
- `extract_rating_distribution()`: Parses the 5-tier rating breakdown
- `extract_tags()`: Collects all professor characteristic tags

### 4. Review Scraper

**Purpose**: Extract all reviews with pagination handling

```python
class ReviewScraper:
    def __init__(self, driver: webdriver.Chrome)
    def load_all_reviews(self) -> None
    def extract_reviews(self) -> List[Review]
    def _parse_review_element(self, element: WebElement) -> Review
```

**Key Methods**:
- `load_all_reviews()`: Clicks "Load More Ratings" until all reviews are visible
- `extract_reviews()`: Parses all review elements into structured objects
- `_parse_review_element()`: Extracts all fields from a single review card

### 5. Data Cleaner

**Purpose**: Normalize and validate all extracted data

```python
class DataCleaner:
    @staticmethod
    def clean_text(text: str) -> str
    @staticmethod
    def parse_number(value: str) -> Optional[float]
    @staticmethod
    def parse_percentage(value: str) -> Optional[int]
    @staticmethod
    def parse_boolean(value: str) -> bool
    @staticmethod
    def clean_professor(professor: Professor) -> Professor
```

**Cleaning Rules**:
- Remove HTML tags using regex
- Strip emojis and special characters
- Normalize whitespace (collapse multiple spaces/newlines)
- Convert numeric strings to float/int types
- Handle "N/A" and missing values consistently

## Data Models

### ProfessorSummary (from main listing)

```python
@dataclass
class ProfessorSummary:
    professor_name: str
    department: str
    university: str
    num_ratings: int
    avg_quality: float
    avg_difficulty: float
    would_take_again_pct: Optional[int]
    professor_page_url: str
```

### Professor (complete data)

```python
@dataclass
class Professor:
    professor_name: str
    department: str
    overall_quality: float
    difficulty_level: float
    would_take_again: Optional[int]
    rating_distribution: Dict[str, int]  # {"Awesome": 28, "Great": 2, ...}
    tags: List[str]
    reviews: List[Review]
```

### Review

```python
@dataclass
class Review:
    course_code: str
    for_credit: bool
    attendance: str
    grade: str
    textbook_used: str
    quality_score: float
    difficulty_score: float
    review_text: str
    tags: List[str]
    date_posted: str
    helpful_upvotes: int
    helpful_downvotes: int
```

## Error Handling

### Retry Strategy

- **Network Errors**: Exponential backoff (1s, 2s, 4s) for up to 3 retries
- **Element Not Found**: Single retry after 2-second wait
- **Stale Element**: Re-locate element and retry operation

### Error Recovery

```python
class ErrorHandler:
    def __init__(self, max_retries: int = 3)
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any
    def handle_missing_element(self, selector: str) -> Optional[Any]
    def log_error(self, error: Exception, context: str) -> None
```

### Logging Strategy

- **INFO**: Progress updates (professors scraped, reviews collected)
- **WARNING**: Missing elements, retries, skipped professors
- **ERROR**: Failed requests, parsing errors, critical failures
- Log file: `scraper.log` with rotation (10MB max, 3 backups)

## Testing Strategy

### Unit Tests

- Test data cleaning functions with various input formats
- Test selector parsing with mock HTML
- Test retry logic with simulated failures
- Test data model validation

### Integration Tests

- Test full scraping workflow with a single professor
- Test pagination handling (mock "Show More" clicks)
- Test error recovery with intentionally broken selectors
- Validate output JSON structure

### Manual Testing

- Run scraper on USF RateMyProfessor page
- Verify all professors are collected
- Spot-check random professors for data accuracy
- Validate JSON can be imported into Supabase

## Performance Considerations

### Rate Limiting

- Add 1-2 second delay between professor page requests
- Randomize delays slightly to appear more human-like
- Monitor for 429 (Too Many Requests) responses

### Memory Management

- Process professors in batches if dataset is very large
- Write intermediate results to disk periodically
- Clear WebDriver cache between professors

### Execution Time

- Estimated time: 2-3 seconds per professor page
- For 500 professors: ~20-25 minutes total
- Progress bar to show completion status

## Deployment and Usage

### Installation

```bash
pip install selenium beautifulsoup4 webdriver-manager
```

### Execution

```bash
python main.py --headless --output usf_professors.json
```

### Configuration Options

- `--headless`: Run browser in headless mode (default: True)
- `--output`: Output file path (default: usf_professors.json)
- `--delay`: Delay between requests in seconds (default: 1.5)
- `--max-professors`: Limit number of professors to scrape (for testing)

## Future Enhancements

- Support for multiple universities (parameterized school ID)
- Incremental updates (only scrape new/updated professors)
- Database direct insertion (skip JSON intermediate)
- Parallel scraping with multiple WebDriver instances
- Proxy rotation for large-scale scraping
