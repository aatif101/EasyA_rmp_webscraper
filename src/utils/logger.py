"""Logging configuration for the RMP scraper."""

import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logging(log_file: str = "scraper.log") -> None:
    """
    Configure logging system with file and console handlers.
    
    Sets up:
    - File handler with rotation (10MB max, 3 backups)
    - Console handler for progress updates
    - INFO, WARNING, ERROR levels
    
    Args:
        log_file: Path to log file (default: scraper.log)
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler with rotation (10MB, 3 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for progress updates
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info("=" * 60)
    logger.info("RateMyProfessor Scraper - Logging initialized")
    logger.info("=" * 60)
