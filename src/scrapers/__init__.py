"""Scrapers for RateMyProfessor data extraction."""

from .list_scraper import ProfessorListScraper
from .detail_scraper import ProfessorDetailScraper

__all__ = ['ProfessorListScraper', 'ProfessorDetailScraper']
