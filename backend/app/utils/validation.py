"""
Validation utilities for authentication.
Includes email, password, and security validations.
"""
import re
from typing import Dict, List, Tuple, Optional
from app.utils.logger import logger

# Email validation regex
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# Disposable email domains (common ones - can be expanded)
DISPOSABLE_EMAIL_DOMAINS = {
    'tempmail.com', '10minutemail.com', 'guerrillamail.com', 
    'mailinator.com', 'throwaway.email', 'temp-mail.org',
    'getnada.com', 'mohmal.com', 'fakeinbox.com', 'trashmail.com'
}

# Password strength requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True

# Special characters allowed in passwords
SPECIAL_CHARS = r'!@#$%^&*()_+-=[]{}|;:,.<>?'


def validate_email(email: str, check_disposable: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate email format and optionally check for disposable domains.
    
    Args:
        email: Email address to validate
        check_disposable: Whether to check for disposable email domains
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip().lower()
    
    # Check format
    if not EMAIL_REGEX.match(email):
        return False, "Enter a valid email address"
    
    # Check disposable domains
    if check_disposable:
        domain = email.split('@')[1] if '@' in email else ''
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            return False, "Disposable email addresses are not allowed"
    
    return True, None


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength and return feedback.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_suggestions)
    """
    suggestions = []
    
    if not password:
        return False, ["Password is required"]
    
    # Check length
    if len(password) < PASSWORD_MIN_LENGTH:
        suggestions.append(f"Use at least {PASSWORD_MIN_LENGTH} characters")
    
    # Check uppercase
    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        suggestions.append("Add an uppercase letter")
    
    # Check lowercase
    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        suggestions.append("Add a lowercase letter")
    
    # Check number
    if PASSWORD_REQUIRE_NUMBER and not re.search(r'\d', password):
        suggestions.append("Add a number")
    
    # Check special character
    if PASSWORD_REQUIRE_SPECIAL:
        special_pattern = re.escape(SPECIAL_CHARS)
        if not re.search(f'[{special_pattern}]', password):
            suggestions.append("Add a special character (!@#$%^&*...)")
    
    is_valid = len(suggestions) == 0
    return is_valid, suggestions


def calculate_password_strength(password: str) -> Tuple[str, int]:
    """
    Calculate password strength (Weak/Medium/Strong) and score (0-100).
    
    Args:
        password: Password to evaluate
        
    Returns:
        Tuple of (strength_label, score_0_to_100)
    """
    if not password:
        return "Weak", 0
    
    score = 0
    length = len(password)
    
    # Length scoring (0-30 points)
    if length >= 12:
        score += 30
    elif length >= 10:
        score += 20
    elif length >= 8:
        score += 10
    
    # Character variety (0-40 points)
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_number = bool(re.search(r'\d', password))
    has_special = bool(re.search(f'[{re.escape(SPECIAL_CHARS)}]', password))
    
    variety_count = sum([has_upper, has_lower, has_number, has_special])
    score += variety_count * 10  # 10 points per variety type
    
    # Complexity bonus (0-30 points)
    if length >= 12 and variety_count == 4:
        score += 30
    elif length >= 10 and variety_count >= 3:
        score += 20
    elif length >= 8 and variety_count >= 2:
        score += 10
    
    # Determine strength label
    if score >= 80:
        strength = "Strong"
    elif score >= 50:
        strength = "Medium"
    else:
        strength = "Weak"
    
    return strength, min(100, score)


def validate_role(role: str, allowed_roles: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate user role against whitelist.
    
    Args:
        role: Role to validate
        allowed_roles: List of allowed roles (if None, uses default)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not role:
        return False, "Role is required"
    
    # Default allowed roles
    if allowed_roles is None:
        allowed_roles = ["student", "founder", "investor", "admin", "user", "employer", "enumerator", "vendor"]
    
    if role not in allowed_roles:
        return False, f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"
    
    return True, None
