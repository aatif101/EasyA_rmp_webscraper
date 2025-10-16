"""Test script for JSONWriter functionality."""

import json
import os
from pathlib import Path

from src.models import Professor, Review
from src.utils.json_writer import JSONWriter


def test_json_writer():
    """Test the JSONWriter class with sample data."""
    
    # Create sample review data
    reviews = [
        Review(
            course_code="CSC101",
            for_credit=True,
            attendance="Mandatory",
            grade="A",
            textbook_used="Yes",
            quality_score=4.5,
            difficulty_score=3.0,
            review_text="Great professor, very helpful!",
            tags=["Caring", "Clear grading criteria"],
            date_posted="2023-05-15",
            helpful_upvotes=10,
            helpful_downvotes=1
        ),
        Review(
            course_code="CSC102",
            for_credit=True,
            attendance="Not Mandatory",
            grade="B+",
            textbook_used="No",
            quality_score=4.0,
            difficulty_score=3.5,
            review_text="Challenging but fair.",
            tags=["Tough grader"],
            date_posted="2023-06-20",
            helpful_upvotes=5,
            helpful_downvotes=0
        )
    ]
    
    # Create sample professor data
    professors = [
        Professor(
            professor_name="Dr. John Smith",
            department="Computer Science",
            overall_quality=4.3,
            difficulty_level=3.2,
            would_take_again=85,
            rating_distribution={"Awesome": 15, "Great": 8, "Good": 3, "OK": 1, "Awful": 0},
            tags=["Caring", "Clear grading criteria", "Respected"],
            reviews=reviews
        ),
        Professor(
            professor_name="Dr. Jane Doe",
            department="Mathematics",
            overall_quality=4.7,
            difficulty_level=2.8,
            would_take_again=92,
            rating_distribution={"Awesome": 20, "Great": 5, "Good": 2, "OK": 0, "Awful": 0},
            tags=["Amazing lectures", "Hilarious", "Accessible outside class"],
            reviews=[reviews[0]]  # Just one review for this professor
        )
    ]
    
    # Initialize JSONWriter
    json_writer = JSONWriter()
    
    print("Testing JSONWriter functionality...")
    print("=" * 60)
    
    # Test 1: Serialize professors
    print("\n1. Testing serialization...")
    serialized = json_writer.serialize_professors(professors)
    print(f"   ✓ Serialized {len(serialized)} professors")
    
    # Test 2: Validate JSON structure
    print("\n2. Testing validation...")
    is_valid = json_writer.validate_json_structure(serialized)
    print(f"   ✓ Validation result: {is_valid}")
    
    # Test 3: Write to JSON file
    print("\n3. Testing file writing...")
    output_file = "test_output.json"
    success = json_writer.write_json(serialized, output_file)
    print(f"   ✓ Write result: {success}")
    
    # Test 4: Verify file exists and is valid JSON
    print("\n4. Verifying output file...")
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"   ✓ File exists and contains {len(loaded_data)} professors")
        print(f"   ✓ First professor: {loaded_data[0]['professor_name']}")
        print(f"   ✓ Total reviews in file: {sum(len(p['reviews']) for p in loaded_data)}")
    
    # Test 5: Generate summary report
    print("\n5. Testing summary report generation...")
    errors = ["Error 1: Failed to load page", "Error 2: Element not found"]
    skipped = ["Dr. Missing Person"]
    summary = json_writer.generate_summary_report(professors, errors, skipped)
    print(f"   ✓ Total professors: {summary['total_professors_scraped']}")
    print(f"   ✓ Total reviews: {summary['total_reviews_collected']}")
    print(f"   ✓ Average reviews per professor: {summary['average_reviews_per_professor']}")
    print(f"   ✓ Errors encountered: {summary['errors_encountered']}")
    print(f"   ✓ Professors skipped: {summary['professors_skipped']}")
    
    # Test 6: Log summary report
    print("\n6. Testing summary report logging...")
    json_writer.log_summary_report(summary)
    
    # Test 7: Save summary report
    print("\n7. Testing summary report saving...")
    summary_file = "test_summary.json"
    success = json_writer.save_summary_report(summary, summary_file)
    print(f"   ✓ Summary save result: {success}")
    
    # Test 8: Complete workflow
    print("\n8. Testing complete workflow...")
    complete_output = "test_complete_output.json"
    success = json_writer.save_professors(professors, complete_output)
    print(f"   ✓ Complete workflow result: {success}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("\nGenerated files:")
    print(f"  - {output_file}")
    print(f"  - {summary_file}")
    print(f"  - {complete_output}")
    print("\nYou can inspect these files to verify the output format.")
    
    # Cleanup
    print("\nCleaning up test files...")
    for file in [output_file, summary_file, complete_output]:
        if os.path.exists(file):
            os.remove(file)
            print(f"  - Removed {file}")


if __name__ == "__main__":
    test_json_writer()
