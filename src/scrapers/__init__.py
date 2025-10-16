"""Scrapers for RateMyProfessor data extraction."""

from .list_scraper import ProfessorListScraper
from .detail_scraper import ProfessorDetailScraper
from .review_scraper import ReviewScraper

__all__ = ['ProfessorListScraper', 'ProfessorDetailScraper', 'ReviewScraper']
