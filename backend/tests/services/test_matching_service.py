import pytest
from app.services.matching_service import MatchingService
from app.db.models import User, Job, Startup
from app.db.models.user import UserRole


def test_calculate_skills_match():
    """Test skills matching calculation."""
    service = MatchingService()
    
    required = ["Python", "JavaScript", "SQL"]
    user_skills = ["Python", "JavaScript", "React"]
    
    match = service._calculate_skills_match(required, user_skills)
    assert match == pytest.approx(0.67, 0.01)  # 2 out of 3 match


def test_calculate_experience_match():
    """Test experience matching calculation."""
    service = MatchingService()
    
    # User has more experience than required
    match1 = service._calculate_experience_match(2, 5)
    assert match1 == 1.0
    
    # User has less experience
    match2 = service._calculate_experience_match(5, 2)
    assert match2 == pytest.approx(0.4, 0.01)  # 2/5
    
    # No experience required
    match3 = service._calculate_experience_match(0, 2)
    assert match3 == 1.0

