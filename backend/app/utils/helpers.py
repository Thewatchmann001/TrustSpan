"""
Helper functions for TrustBridge backend
"""
from typing import Dict, Any, Optional
import json
import re


def calculate_match_score(
    skills_match: float,
    location_match: float,
    degree_match: float,
    experience_match: float,
    verified: bool = False
) -> float:
    """
    Calculate weighted job match score.
    
    Weights:
    - Skills: 40%
    - Location: 20%
    - Degree: 20%
    - Experience: 10%
    - Verified credentials: 10%
    """
    weights = {
        'skills': 0.4,
        'location': 0.2,
        'degree': 0.2,
        'experience': 0.1,
        'verified': 0.1
    }
    
    verified_score = 1.0 if verified else 0.0
    
    total_score = (
        skills_match * weights['skills'] +
        location_match * weights['location'] +
        degree_match * weights['degree'] +
        experience_match * weights['experience'] +
        verified_score * weights['verified']
    )
    
    return min(1.0, max(0.0, total_score))


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON response from subprocess output.
    
    Args:
        response_text: Raw text output from subprocess
        
    Returns:
        Parsed JSON data
    """
    try:
        # Clean the response text
        cleaned = response_text.strip()
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        # If no JSON found, try parsing the entire response
        return json.loads(cleaned)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {response_text[:200]}...") from e