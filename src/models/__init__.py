"""Data models for RateMyProfessor scraper."""

from .professor import ProfessorSummary, Professor
from .review import Review

__all__ = ['ProfessorSummary', 'Professor', 'Review']
