"""
Hallucination Validator
Prevents AI from inventing metrics, projects, leadership roles, or achievements not provided by the user.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from app.utils.logger import logger


class HallucinationValidator:
    """
    Validates AI output to ensure it doesn't invent content not present in user input.
    Enforces strict rules for entry-level users and prevents metric fabrication.
    """
    
    # Forbidden patterns that indicate hallucination
    FORBIDDEN_METRICS = [
        r'\d+%',  # Percentages
        r'\$\d+',  # Dollar amounts
        r'\d+\s*(million|billion|thousand)',  # Large numbers
        r'increased by \d+',  # Growth claims
        r'reduced by \d+',  # Reduction claims
        r'\d+\s*(users|customers|clients)',  # User counts
        r'\d+\s*(team|member|employee)',  # Team sizes
    ]
    
    # Leadership verbs that should only be used if user mentioned leadership
    LEADERSHIP_VERBS = [
        'led', 'spearheaded', 'orchestrated', 'directed', 'managed',
        'oversaw', 'supervised', 'coordinated', 'executed', 'delivered'
    ]
    
    # Systems/tools that should not be mentioned unless user stated them
    FORBIDDEN_SYSTEMS = [
        'crm', 'inventory system', 'erp', 'pos system',
        'salesforce', 'hubspot', 'sap', 'oracle'
    ]
    
    # Entry-level safe verbs
    ENTRY_LEVEL_VERBS = [
        'assisted', 'participated', 'contributed', 'supported',
        'gained exposure', 'learned', 'developed knowledge',
        'demonstrated understanding', 'helped', 'worked with'
    ]
    
    def __init__(self):
        self.metrics_pattern = re.compile('|'.join(self.FORBIDDEN_METRICS), re.IGNORECASE)
        self.leadership_pattern = re.compile(r'\b(' + '|'.join(self.LEADERSHIP_VERBS) + r')\b', re.IGNORECASE)
        self.systems_pattern = re.compile(r'\b(' + '|'.join(self.FORBIDDEN_SYSTEMS) + r')\b', re.IGNORECASE)
    
    def is_entry_level(self, user_data: Dict[str, Any], experience: List[Dict[str, Any]]) -> bool:
        """
        Detect if user is entry-level based on:
        - No experience provided
        - Student role
        - Fresh graduate
        - No years of experience mentioned
        """
        role = user_data.get("role", "").lower()
        is_student = "student" in role or "graduate" in role or "entry" in role
        
        has_experience = len(experience) > 0
        has_years = any(
            "year" in str(exp.get("description", "")).lower() 
            or "year" in str(exp.get("start_date", "")).lower()
            for exp in experience
        )
        
        return is_student or (not has_experience) or (not has_years)
    
    def extract_user_metrics(self, user_text: str) -> List[str]:
        """Extract any metrics/numbers explicitly mentioned by the user."""
        metrics = []
        
        # Find percentages
        percentages = re.findall(r'\d+%', user_text)
        metrics.extend(percentages)
        
        # Find dollar amounts
        dollars = re.findall(r'\$\d+', user_text)
        metrics.extend(dollars)
        
        # Find numbers with context (users, customers, etc.)
        number_context = re.findall(r'\d+\s*(users?|customers?|clients?|team|members?)', user_text, re.IGNORECASE)
        metrics.extend(number_context)
        
        return metrics
    
    def extract_user_leadership(self, user_text: str) -> bool:
        """Check if user explicitly mentioned leadership roles or activities."""
        leadership_indicators = [
            'led', 'managed', 'supervised', 'directed', 'team lead',
            'team leader', 'manager', 'supervisor', 'head of', 'director'
        ]
        
        user_lower = user_text.lower()
        return any(indicator in user_lower for indicator in leadership_indicators)
    
    def extract_user_systems(self, user_text: str) -> List[str]:
        """Extract systems/tools explicitly mentioned by the user."""
        user_lower = user_text.lower()
        mentioned_systems = [sys for sys in self.FORBIDDEN_SYSTEMS if sys in user_lower]
        return mentioned_systems
    
    def validate_no_metrics_invention(
        self, 
        ai_output: str, 
        user_input: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that AI didn't invent metrics.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # Extract metrics from user input
        user_metrics = self.extract_user_metrics(user_input)
        
        # Find all metrics in AI output
        ai_metrics = re.findall(self.metrics_pattern, ai_output)
        
        # Check if AI added metrics not in user input
        for metric in ai_metrics:
            if metric not in user_metrics and user_metrics:  # If user had metrics, check they match
                violations.append(f"Invented metric: {metric}")
            elif not user_metrics and metric:  # User had no metrics, AI added them
                violations.append(f"Fabricated metric: {metric}")
        
        return len(violations) == 0, violations
    
    def validate_no_leadership_invention(
        self,
        ai_output: str,
        user_input: str,
        is_entry_level: bool
    ) -> Tuple[bool, List[str]]:
        """
        Validate that AI didn't invent leadership claims.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # Check if user mentioned leadership
        user_mentioned_leadership = self.extract_user_leadership(user_input)
        
        # Find leadership verbs in AI output
        ai_leadership = self.leadership_pattern.findall(ai_output)
        
        # If entry-level and AI used leadership verbs, it's a violation
        if is_entry_level and ai_leadership and not user_mentioned_leadership:
            violations.append(f"Entry-level user but AI used leadership verbs: {', '.join(ai_leadership)}")
        
        # If user didn't mention leadership but AI did, it's a violation
        if not user_mentioned_leadership and ai_leadership:
            violations.append(f"User didn't mention leadership but AI added: {', '.join(ai_leadership)}")
        
        return len(violations) == 0, violations
    
    def validate_no_system_invention(
        self,
        ai_output: str,
        user_input: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that AI didn't invent systems/tools.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # Extract systems mentioned by user
        user_systems = self.extract_user_systems(user_input)
        
        # Find systems in AI output
        ai_systems = self.systems_pattern.findall(ai_output)
        
        # Check if AI added systems not mentioned by user
        for system in ai_systems:
            if system.lower() not in [s.lower() for s in user_systems]:
                violations.append(f"Invented system/tool: {system}")
        
        return len(violations) == 0, violations
    
    def validate_summary_boundary(
        self,
        summary: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that summary doesn't contain experience-like content.
        
        Summary should be:
        - General (who you are, what you studied, what skills you have)
        - Achievement-light
        - NO project stories
        - NO metrics
        - NO timelines
        """
        violations = []
        
        # Check for project story indicators
        story_indicators = [
            'project', 'built', 'developed', 'created', 'implemented',
            'launched', 'deployed', 'delivered'
        ]
        
        summary_lower = summary.lower()
        found_stories = [indicator for indicator in story_indicators if indicator in summary_lower]
        
        if found_stories:
            violations.append(f"Summary contains project stories (should be in Experience): {', '.join(found_stories)}")
        
        # Check for metrics
        has_metrics = bool(self.metrics_pattern.search(summary))
        if has_metrics:
            violations.append("Summary contains metrics (should be in Experience)")
        
        # Check for timelines
        timeline_patterns = [
            r'\d{4}',  # Years
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(month|year|quarter)'
        ]
        has_timelines = any(re.search(pattern, summary_lower) for pattern in timeline_patterns)
        if has_timelines:
            violations.append("Summary contains timelines (should be in Experience)")
        
        return len(violations) == 0, violations
    
    def validate_complete(
        self,
        ai_output: str,
        user_input: str,
        user_data: Dict[str, Any],
        experience: List[Dict[str, Any]],
        section: str = "experience"
    ) -> Tuple[bool, List[str]]:
        """
        Complete validation of AI output.
        
        Returns:
            (is_valid, list_of_all_violations)
        """
        all_violations = []
        
        is_entry_level = self.is_entry_level(user_data, experience)
        
        # Validate metrics
        metrics_valid, metrics_violations = self.validate_no_metrics_invention(ai_output, user_input)
        if not metrics_valid:
            all_violations.extend(metrics_violations)
        
        # Validate leadership (only for experience/summary)
        if section in ["experience", "summary"]:
            leadership_valid, leadership_violations = self.validate_no_leadership_invention(
                ai_output, user_input, is_entry_level
            )
            if not leadership_valid:
                all_violations.extend(leadership_violations)
        
        # Validate systems
        systems_valid, systems_violations = self.validate_no_system_invention(ai_output, user_input)
        if not systems_valid:
            all_violations.extend(systems_violations)
        
        # Validate summary boundary
        if section == "summary":
            summary_valid, summary_violations = self.validate_summary_boundary(ai_output)
            if not summary_valid:
                all_violations.extend(summary_violations)
        
        is_valid = len(all_violations) == 0
        
        if not is_valid:
            logger.warning(f"Hallucination detected in {section}: {', '.join(all_violations)}")
        
        return is_valid, all_violations
    
    def sanitize_output(
        self,
        ai_output: str,
        user_input: str,
        user_data: Dict[str, Any],
        experience: List[Dict[str, Any]],
        section: str = "experience"
    ) -> str:
        """
        Sanitize AI output by removing hallucinated content.
        
        This is a last resort - better to regenerate than sanitize.
        """
        is_entry_level = self.is_entry_level(user_data, experience)
        sanitized = ai_output
        
        # Remove invented metrics
        user_metrics = self.extract_user_metrics(user_input)
        if not user_metrics:
            # User had no metrics, remove all metrics from output
            for pattern in self.FORBIDDEN_METRICS:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Remove leadership verbs for entry-level users
        if is_entry_level:
            user_mentioned_leadership = self.extract_user_leadership(user_input)
            if not user_mentioned_leadership:
                for verb in self.LEADERSHIP_VERBS:
                    sanitized = re.sub(rf'\b{verb}\b', 'assisted with', sanitized, flags=re.IGNORECASE)
        
        # Remove invented systems
        user_systems = self.extract_user_systems(user_input)
        for system in self.FORBIDDEN_SYSTEMS:
            if system.lower() not in [s.lower() for s in user_systems]:
                sanitized = re.sub(rf'\b{system}\b', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
