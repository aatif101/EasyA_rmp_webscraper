"""Review data model."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Review:
    """Individual review data from professor page."""
    
    course_code: str
    for_credit: bool
    attendance: str
    grade: str
    textbook_used: str
    quality_score: float
    difficulty_score: float
    review_text: str
    tags: List[str] = field(default_factory=list)
    date_posted: str = ""
    helpful_upvotes: int = 0
    helpful_downvotes: int = 0
    
    def validate(self) -> None:
        """Validate required fields are present and valid."""
        if not self.course_code or not self.course_code.strip():
            raise ValueError("course_code is required")
        if not (0 <= self.quality_score <= 5):
            raise ValueError("quality_score must be between 0 and 5")
        if not (0 <= self.difficulty_score <= 5):
            raise ValueError("difficulty_score must be between 0 and 5")
        if self.helpful_upvotes < 0:
            raise ValueError("helpful_upvotes must be non-negative")
        if self.helpful_downvotes < 0:
            raise ValueError("helpful_downvotes must be non-negative")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'course_code': self.course_code,
            'for_credit': self.for_credit,
            'attendance': self.attendance,
            'grade': self.grade,
            'textbook_used': self.textbook_used,
            'quality_score': self.quality_score,
            'difficulty_score': self.difficulty_score,
            'review_text': self.review_text,
            'tags': self.tags,
            'date_posted': self.date_posted,
            'helpful_upvotes': self.helpful_upvotes,
            'helpful_downvotes': self.helpful_downvotes
        }
