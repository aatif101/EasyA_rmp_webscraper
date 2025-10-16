"""Unit test for save_to_json functionality"""

import json
import os
from src.models import ProfessorSummary
from src.scrapers.list_scraper import ProfessorListScraper

def test_save_to_json():
    """Test that save_to_json correctly saves data with UTF-8 encoding"""
    
    # Create mock professor data
    mock_professors = [
        ProfessorSummary(
            professor_name="Dr. John Smith",
            department="Computer Science",
            university="University of South Florida",
            num_ratings=50,
            avg_quality=4.5,
            avg_difficulty=3.2,
            would_take_again_pct=85,
            professor_page_url="https://www.ratemyprofessors.com/professor/123"
        ),
        ProfessorSummary(
            professor_name="Dr. María García",  # Test UTF-8 with special characters
            department="Mathematics",
            university="University of South Florida",
            num_ratings=30,
            avg_quality=4.8,
            avg_difficulty=4.0,
            would_take_again_pct=90,
            professor_page_url="https://www.ratemyprofessors.com/professor/456"
        ),
        ProfessorSummary(
            professor_name="Dr. 李明",  # Test UTF-8 with Chinese characters
            department="Physics",
            university="University of South Florida",
            num_ratings=25,
            avg_quality=4.2,
            avg_difficulty=3.8,
            would_take_again_pct=None,  # Test optional field
            professor_page_url="https://www.ratemyprofessors.com/professor/789"
        )
    ]
    
    # Create a scraper instance (we don't need driver for this test)
    scraper = ProfessorListScraper(driver=None, base_url="")
    
    # Test file path
    test_output = "test_usf_professors_main.json"
    
    try:
        # Save to JSON
        scraper.save_to_json(mock_professors, test_output)
        
        # Verify file was created
        assert os.path.exists(test_output), "Output file was not created"
        
        # Read and verify the JSON content
        with open(test_output, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # Verify structure
        assert len(loaded_data) == 3, f"Expected 3 professors, got {len(loaded_data)}"
        
        # Verify first professor
        prof1 = loaded_data[0]
        assert prof1['professor_name'] == "Dr. John Smith"
        assert prof1['department'] == "Computer Science"
        assert prof1['num_ratings'] == 50
        assert prof1['avg_quality'] == 4.5
        assert prof1['would_take_again_pct'] == 85
        
        # Verify UTF-8 encoding with special characters
        prof2 = loaded_data[1]
        assert prof2['professor_name'] == "Dr. María García", "UTF-8 special characters not preserved"
        
        # Verify UTF-8 encoding with Chinese characters
        prof3 = loaded_data[2]
        assert prof3['professor_name'] == "Dr. 李明", "UTF-8 Chinese characters not preserved"
        assert prof3['would_take_again_pct'] is None, "Optional field should be None"
        
        print("✓ All tests passed!")
        print(f"✓ File created: {test_output}")
        print(f"✓ UTF-8 encoding verified")
        print(f"✓ Data structure validated")
        print(f"✓ Optional fields handled correctly")
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"✗ Error during test: {e}")
        raise
    finally:
        # Clean up test file
        if os.path.exists(test_output):
            os.remove(test_output)
            print(f"✓ Cleaned up test file: {test_output}")

if __name__ == "__main__":
    test_save_to_json()
