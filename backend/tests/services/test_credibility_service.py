import pytest
from app.services.credibility_service import CredibilityService


def test_get_credibility_grade():
    """Test credibility grade calculation."""
    service = CredibilityService()
    
    assert service._get_credibility_grade(85) == "A+"
    assert service._get_credibility_grade(75) == "A"
    assert service._get_credibility_grade(65) == "B"
    assert service._get_credibility_grade(55) == "C"
    assert service._get_credibility_grade(45) == "D"
    assert service._get_credibility_grade(40) == "D"
    assert service._get_credibility_grade(35) == "F"

