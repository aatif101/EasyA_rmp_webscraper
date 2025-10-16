"""Professor data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class ProfessorSummary:
    """Summary data from main professor listing page."""
    
    professor_name: str
    department: str
    university: str
    num_ratings: int
    avg_quality: float
    avg_difficulty: float
    would_take_again_pct: Optional[int]
    professor_page_url: str
    
    def validate(self) -> None:
        """Validate required fields are present and valid."""
        if not self.professor_name or not self.professor_name.strip():
            raise ValueError("professor_name is required")
        if not self.department or not self.department.strip():
            raise ValueError("department is required")
        if not self.university or not self.university.strip():
            raise ValueError("university is required")
        if self.num_ratings < 0:
            raise ValueError("num_ratings must be non-negative")
        if not (0 <= self.avg_quality <= 5):
            raise ValueError("avg_quality must be between 0 and 5")
        if not (0 <= self.avg_difficulty <= 5):
            raise ValueError("avg_difficulty must be between 0 and 5")
        if not self.professor_page_url or not self.professor_page_url.strip():
            raise ValueError("professor_page_url is required")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'professor_name': self.professor_name,
            'department': self.department,
            'university': self.university,
            'num_ratings': self.num_ratings,
            'avg_quality': self.avg_quality,
            'avg_difficulty': self.avg_difficulty,
            'would_take_again_pct': self.would_take_again_pct,
            'professor_page_url': self.professor_page_url
        }


@dataclass
class Professor:
    """Complete professor data including metadata and reviews."""
    
    professor_name: str
    department: str
    overall_quality: float
    difficulty_level: float
    would_take_again: Optional[int]
    rating_distribution: Dict[str, int] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    reviews: List['Review'] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate required fields are present and valid."""
        if not self.professor_name or not self.professor_name.strip():
            raise ValueError("professor_name is required")
        if not self.department or not self.department.strip():
            raise ValueError("department is required")
        if not (0 <= self.overall_quality <= 5):
            raise ValueError("overall_quality must be between 0 and 5")
        if not (0 <= self.difficulty_level <= 5):
            raise ValueError("difficulty_level must be between 0 and 5")
        if self.would_take_again is not None and not (0 <= self.would_take_again <= 100):
            raise ValueError("would_take_again must be between 0 and 100")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'professor_name': self.professor_name,
            'department': self.department,
            'overall_quality': self.overall_quality,
            'difficulty_level': self.difficulty_level,
            'would_take_again': self.would_take_again,
            'rating_distribution': self.rating_distribution,
            'tags': self.tags,
            'reviews': [review.to_dict() for review in self.reviews]
        }
