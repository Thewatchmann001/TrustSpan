"""
Suggestion Quality Validator
Enforces minimum quality standards for AI-generated CV suggestions.
"""
import re
from typing import List, Dict, Any, Tuple
from app.utils.logger import logger


class SuggestionValidator:
    """Validates AI suggestions for quality, length, grammar, and spelling."""
    
    MIN_CHARACTERS_PER_SUGGESTION = 150  # Minimum 150 characters (roughly 3-4 sentences)
    MIN_WORDS_PER_SUGGESTION = 25  # Minimum 25 words
    MAX_RETRIES = 3
    
    # Common spelling mistakes to catch
    COMMON_MISSPELLINGS = {
        "recieve": "receive",
        "seperate": "separate",
        "occured": "occurred",
        "accomodate": "accommodate",
        "definately": "definitely",
        "existance": "existence",
        "sucess": "success",
        "achievment": "achievement",
        "profesional": "professional",
        "experiance": "experience",
    }
    
    # Weak phrases that should be flagged
    WEAK_PHRASES = [
        "i did",
        "i was",
        "my job was",
        "worked on",
        "helped with",
        "did some",
        "was responsible",
    ]
    
    def validate_suggestion(self, suggestion: str, field: str = None) -> Tuple[bool, List[str]]:
        """
        Validate a single suggestion.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if not suggestion or not isinstance(suggestion, str):
            return False, ["Suggestion is empty or not a string"]
        
        suggestion = suggestion.strip()
        
        # Check minimum length
        if len(suggestion) < self.MIN_CHARACTERS_PER_SUGGESTION:
            issues.append(f"Too short: {len(suggestion)} characters (minimum {self.MIN_CHARACTERS_PER_SUGGESTION})")
        
        # Check minimum word count
        word_count = len(suggestion.split())
        if word_count < self.MIN_WORDS_PER_SUGGESTION:
            issues.append(f"Too few words: {word_count} words (minimum {self.MIN_WORDS_PER_SUGGESTION})")
        
        # Check for common misspellings
        suggestion_lower = suggestion.lower()
        for misspelling, correct in self.COMMON_MISSPELLINGS.items():
            if misspelling in suggestion_lower:
                issues.append(f"Spelling error: '{misspelling}' should be '{correct}'")
        
        # Check for weak phrases (should be avoided in professional CVs)
        for weak_phrase in self.WEAK_PHRASES:
            if weak_phrase in suggestion_lower:
                issues.append(f"Weak phrase detected: '{weak_phrase}' - use stronger action verbs")
        
        # Check for placeholder text
        placeholder_patterns = [
            r"\[.*?\]",  # [placeholder]
            r"\{.*?\}",  # {placeholder}
            r"TODO",
            r"FIXME",
            r"example",
            r"sample",
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, suggestion, re.IGNORECASE):
                issues.append(f"Placeholder text detected: contains '{pattern}'")
        
        # Check for markdown (should be stripped before validation)
        if re.search(r'[*_`]', suggestion):
            issues.append("Contains markdown formatting (should be stripped)")
        
        # Check for proper sentence structure (at least one period, exclamation, or question mark)
        if not re.search(r'[.!?]', suggestion):
            issues.append("Missing sentence-ending punctuation")
        
        # Check for action verbs (especially for experience/summary fields)
        if field and field.lower() in ["experience", "summary", "description"]:
            action_verbs = [
                "led", "delivered", "achieved", "created", "improved", "managed",
                "developed", "executed", "spearheaded", "implemented", "optimized",
                "designed", "built", "established", "increased", "reduced", "enhanced"
            ]
            has_action_verb = any(verb in suggestion_lower for verb in action_verbs)
            if not has_action_verb:
                issues.append("Missing action verb - start with strong verbs like 'Led', 'Delivered', 'Achieved'")
        
        # Check for quantifiable metrics (especially for experience)
        if field and field.lower() == "experience":
            has_numbers = bool(re.search(r'\d+', suggestion))
            if not has_numbers:
                issues.append("Missing quantifiable metrics - add numbers, percentages, or metrics")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def validate_suggestions_list(self, suggestions: List[str], field: str = None) -> Tuple[bool, Dict[int, List[str]]]:
        """
        Validate a list of suggestions.
        
        Returns:
            (all_valid, {index: [issues]})
        """
        all_valid = True
        issues_by_index = {}
        
        for idx, suggestion in enumerate(suggestions):
            is_valid, issues = self.validate_suggestion(suggestion, field)
            if not is_valid:
                all_valid = False
                issues_by_index[idx] = issues
                logger.warning(f"Suggestion {idx} failed validation: {', '.join(issues)}")
        
        return all_valid, issues_by_index
    
    def filter_valid_suggestions(self, suggestions: List[str], field: str = None, min_valid: int = 10) -> List[str]:
        """
        Filter out invalid suggestions, keeping only valid ones.
        
        Args:
            suggestions: List of suggestions to filter
            field: Field name for context-aware validation
            min_valid: Minimum number of valid suggestions required
        
        Returns:
            List of valid suggestions
        """
        valid_suggestions = []
        
        for suggestion in suggestions:
            is_valid, issues = self.validate_suggestion(suggestion, field)
            if is_valid:
                valid_suggestions.append(suggestion)
            else:
                logger.debug(f"Filtered out invalid suggestion: {', '.join(issues)}")
        
        if len(valid_suggestions) < min_valid:
            logger.warning(f"Only {len(valid_suggestions)} valid suggestions found (minimum {min_valid} required)")
        
        return valid_suggestions
    
    def fix_common_issues(self, suggestion: str) -> str:
        """
        Automatically fix common issues in suggestions.
        
        Note: This is a last resort - better to regenerate than fix.
        """
        fixed = suggestion
        
        # Fix common misspellings
        for misspelling, correct in self.COMMON_MISSPELLINGS.items():
            fixed = re.sub(rf'\b{misspelling}\b', correct, fixed, flags=re.IGNORECASE)
        
        # Remove markdown
        fixed = re.sub(r'\*\*(.*?)\*\*', r'\1', fixed)
        fixed = re.sub(r'\*(.*?)\*', r'\1', fixed)
        fixed = re.sub(r'`(.*?)`', r'\1', fixed)
        
        return fixed.strip()
