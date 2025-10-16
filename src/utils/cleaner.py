"""
Data cleaning utilities for RateMyProfessor scraper.
Handles text normalization, HTML removal, and type conversions.
"""

import re
from typing import Optional


class DataCleaner:
    """Utility class for cleaning and normalizing scraped data."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing HTML tags, emojis, and normalizing whitespace.
        
        Args:
            text: Raw text string to clean
            
        Returns:
            Cleaned text with normalized whitespace
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace: replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove emojis and other non-ASCII characters
        # Keep basic punctuation and alphanumeric characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Strip leading and trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def parse_number(value: str) -> Optional[float]:
        """
        Convert string numbers to float, handling edge cases.
        
        Args:
            value: String representation of a number
            
        Returns:
            Float value or None if conversion fails
        """
        if not value or not isinstance(value, str):
            return None
        
        # Clean the string
        value = value.strip()
        
        # Handle common "not available" cases
        if value.upper() in ['N/A', 'NA', 'NONE', '--', '']:
            return None
        
        try:
            # Remove any non-numeric characters except decimal point and minus sign
            cleaned = re.sub(r'[^\d.\-]', '', value)
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def parse_percentage(value: str) -> Optional[int]:
        """
        Extract percentage values from strings and convert to integer.
        
        Args:
            value: String containing percentage (e.g., "85%", "85 percent")
            
        Returns:
            Integer percentage value or None if extraction fails
        """
        if not value or not isinstance(value, str):
            return None
        
        # Clean the string
        value = value.strip()
        
        # Handle common "not available" cases
        if value.upper() in ['N/A', 'NA', 'NONE', '--', '']:
            return None
        
        try:
            # Extract numeric value from percentage string
            # Matches patterns like "85%", "85 %", "85 percent"
            match = re.search(r'(\d+(?:\.\d+)?)\s*%?', value)
            if match:
                percentage = float(match.group(1))
                # Ensure it's within valid percentage range
                if 0 <= percentage <= 100:
                    return int(round(percentage))
            return None
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        """
        Convert string representations to boolean values.
        
        Args:
            value: String representation of boolean
            
        Returns:
            Boolean value (defaults to False for invalid inputs)
        """
        if not value or not isinstance(value, str):
            return False
        
        # Clean and normalize
        value = value.strip().lower()
        
        # True values
        if value in ['true', 'yes', 'y', '1', 'on', 'enabled']:
            return True
        
        # False values (explicit)
        if value in ['false', 'no', 'n', '0', 'off', 'disabled']:
            return False
        
        # Default to False for unknown values
        return False
