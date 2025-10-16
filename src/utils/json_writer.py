"""JSON writer utility for serializing professor data."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.models import Professor


class JSONWriter:
    """Handles serialization and writing of professor data to JSON files."""
    
    def __init__(self):
        """Initialize the JSONWriter."""
        self.logger = logging.getLogger(__name__)
    
    def serialize_professors(self, professors: List[Professor]) -> List[Dict[str, Any]]:
        """
        Serialize Professor objects to dictionaries for JSON output.
        
        Args:
            professors: List of Professor objects to serialize
            
        Returns:
            List of dictionaries representing professor data
        """
        self.logger.info(f"Serializing {len(professors)} professors to JSON format...")
        
        serialized_data = []
        for professor in professors:
            try:
                # Use the to_dict method from Professor model
                prof_dict = professor.to_dict()
                serialized_data.append(prof_dict)
            except Exception as e:
                self.logger.error(f"Error serializing professor {professor.professor_name}: {e}")
                continue
        
        self.logger.info(f"Successfully serialized {len(serialized_data)} professors")
        return serialized_data
    
    def write_json(self, data: List[Dict[str, Any]], output_file: str) -> bool:
        """
        Write serialized data to JSON file with UTF-8 encoding.
        
        Args:
            data: List of dictionaries to write
            output_file: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to JSON file with UTF-8 encoding and indentation for readability
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully wrote {len(data)} records to {output_file}")
            return True
            
        except IOError as e:
            self.logger.error(f"IO error writing to {output_file}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error writing to {output_file}: {e}")
            return False
    
    def validate_json_structure(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate that the JSON structure is correct before writing.
        
        Args:
            data: List of dictionaries to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, list):
            self.logger.error("Data must be a list")
            return False
        
        if len(data) == 0:
            self.logger.warning("Data list is empty")
            return True  # Empty list is valid
        
        # Check that each item is a dictionary with required fields
        required_fields = ['professor_name', 'department', 'overall_quality', 
                          'difficulty_level', 'reviews']
        
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                self.logger.error(f"Item at index {idx} is not a dictionary")
                return False
            
            # Check for required fields
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                self.logger.error(f"Item at index {idx} missing required fields: {missing_fields}")
                return False
            
            # Check that reviews is a list
            if not isinstance(item.get('reviews'), list):
                self.logger.error(f"Item at index {idx} has invalid 'reviews' field (must be a list)")
                return False
        
        self.logger.info(f"JSON structure validation passed for {len(data)} items")
        return True
    
    def save_professors(self, professors: List[Professor], output_file: str) -> bool:
        """
        Complete workflow to serialize, validate, and save professors to JSON.
        
        Args:
            professors: List of Professor objects
            output_file: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize professors to dictionaries
            serialized_data = self.serialize_professors(professors)
            
            if not serialized_data:
                self.logger.error("No data to write after serialization")
                return False
            
            # Validate JSON structure
            if not self.validate_json_structure(serialized_data):
                self.logger.error("JSON structure validation failed")
                return False
            
            # Write to file
            success = self.write_json(serialized_data, output_file)
            
            if success:
                self.logger.info(f"Successfully saved {len(professors)} professors to {output_file}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in save_professors workflow: {e}")
            return False

    def generate_summary_report(self, professors: List[Professor], 
                                errors: Optional[List[str]] = None,
                                skipped: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a summary report of the scraping operation.
        
        Args:
            professors: List of successfully scraped Professor objects
            errors: List of error messages encountered during scraping
            skipped: List of professor names that were skipped
            
        Returns:
            Dictionary containing summary statistics
        """
        total_professors = len(professors)
        total_reviews = sum(len(prof.reviews) for prof in professors)
        
        # Calculate average reviews per professor
        avg_reviews_per_prof = total_reviews / total_professors if total_professors > 0 else 0
        
        # Count professors by department
        departments = {}
        for prof in professors:
            dept = prof.department
            departments[dept] = departments.get(dept, 0) + 1
        
        summary = {
            'total_professors_scraped': total_professors,
            'total_reviews_collected': total_reviews,
            'average_reviews_per_professor': round(avg_reviews_per_prof, 2),
            'departments': departments,
            'errors_encountered': len(errors) if errors else 0,
            'professors_skipped': len(skipped) if skipped else 0,
            'error_list': errors if errors else [],
            'skipped_list': skipped if skipped else []
        }
        
        return summary
    
    def log_summary_report(self, summary: Dict[str, Any]) -> None:
        """
        Log the summary report to console and log file.
        
        Args:
            summary: Summary dictionary from generate_summary_report
        """
        self.logger.info("=" * 80)
        self.logger.info("SCRAPING SUMMARY REPORT")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Professors Scraped: {summary['total_professors_scraped']}")
        self.logger.info(f"Total Reviews Collected: {summary['total_reviews_collected']}")
        self.logger.info(f"Average Reviews per Professor: {summary['average_reviews_per_professor']}")
        self.logger.info(f"Errors Encountered: {summary['errors_encountered']}")
        self.logger.info(f"Professors Skipped: {summary['professors_skipped']}")
        
        if summary['departments']:
            self.logger.info("\nProfessors by Department:")
            for dept, count in sorted(summary['departments'].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  - {dept}: {count}")
        
        if summary['error_list']:
            self.logger.warning("\nErrors Encountered:")
            for error in summary['error_list'][:10]:  # Show first 10 errors
                self.logger.warning(f"  - {error}")
            if len(summary['error_list']) > 10:
                self.logger.warning(f"  ... and {len(summary['error_list']) - 10} more errors")
        
        if summary['skipped_list']:
            self.logger.warning("\nSkipped Professors:")
            for skipped in summary['skipped_list'][:10]:  # Show first 10 skipped
                self.logger.warning(f"  - {skipped}")
            if len(summary['skipped_list']) > 10:
                self.logger.warning(f"  ... and {len(summary['skipped_list']) - 10} more skipped")
        
        self.logger.info("=" * 80)
    
    def save_summary_report(self, summary: Dict[str, Any], output_file: str = "scraping_summary.json") -> bool:
        """
        Save the summary report to a JSON file.
        
        Args:
            summary: Summary dictionary from generate_summary_report
            output_file: Path to output file for summary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary report saved to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving summary report: {e}")
            return False
