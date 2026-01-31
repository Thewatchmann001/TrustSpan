"""
ATS Analyzer Module
Provides transparent, detailed ATS analysis with explicit issues, scores breakdown, and change tracking.
This service builds TRUST by showing exactly what was detected and why.
"""
from typing import Dict, Any, List, Optional
import re
from app.utils.logger import logger


class ATSAnalyzer:
    """Transparent ATS analysis service - explains everything."""
    
    def __init__(self):
        # Common ATS-unfriendly terms and their issues
        self.weak_action_verbs = [
            "worked", "was responsible for", "helped", "involved", "did", "was part of"
        ]
        
        # Strong action verbs for tech roles
        self.strong_action_verbs = [
            "designed", "developed", "implemented", "optimized", "architected",
            "engineered", "created", "built", "deployed", "led", "managed",
            "automated", "configured", "analyzed"
        ]
        
        # Common ATS issues
        self.ats_issue_types = {
            "weak_verbs": "Weak action verbs reduce keyword recognition",
            "formatting": "Non-standard formatting confuses ATS parsing",
            "headings": "Non-standard section headings hurt organization",
            "keywords": "Missing industry keywords and job-specific terms",
            "bullets": "Unclear or vague bullet points lower match scores",
            "dates": "Inconsistent or unclear date formatting",
            "sections": "Missing standard CV sections"
        }
    
    def analyze_ats_compatibility(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide detailed, transparent ATS compatibility analysis.
        
        Returns complete breakdown with:
        - Overall score
        - Score breakdown by category
        - Specific issues with explanations
        - Actionable recommendations
        """
        logger.info("Starting comprehensive ATS analysis")
        
        analysis = {
            "overall_score": 0,
            "grade": "D",
            "analysis_timestamp": None,
            
            # Detailed breakdown
            "score_breakdown": {
                "keyword_match": {"score": 0, "max": 25, "details": []},
                "skills_alignment": {"score": 0, "max": 25, "details": []},
                "experience_relevance": {"score": 0, "max": 25, "details": []},
                "formatting_compatibility": {"score": 0, "max": 25, "details": []}
            },
            
            # Issues found (specific, actionable)
            "issues": [],
            
            # Recommendations (organized by priority)
            "recommendations": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            }
        }
        
        # 1. KEYWORD MATCH ANALYSIS
        analysis["score_breakdown"]["keyword_match"] = self._analyze_keywords(cv_data)
        
        # 2. SKILLS ALIGNMENT ANALYSIS
        analysis["score_breakdown"]["skills_alignment"] = self._analyze_skills(cv_data)
        
        # 3. EXPERIENCE RELEVANCE ANALYSIS
        analysis["score_breakdown"]["experience_relevance"] = self._analyze_experience(cv_data)
        
        # 4. FORMATTING COMPATIBILITY ANALYSIS
        analysis["score_breakdown"]["formatting_compatibility"] = self._analyze_formatting(cv_data)
        
        # Calculate overall score
        total_score = 0
        for category, data in analysis["score_breakdown"].items():
            total_score += data["score"]
        
        analysis["overall_score"] = min(100, total_score)
        analysis["grade"] = self._calculate_grade(analysis["overall_score"])
        
        # Add all detected issues
        analysis["issues"] = self._collect_all_issues(analysis["score_breakdown"])
        
        # Generate recommendations based on issues
        analysis["recommendations"] = self._prioritize_recommendations(analysis["issues"])
        
        logger.info(f"ATS Analysis complete: {analysis['overall_score']}/100 ({analysis['grade']})")
        
        return analysis
    
    def _analyze_keywords(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze keyword match - what industry terms are present."""
        score = 0
        details = []
        
        # Extract all text
        full_text = self._extract_all_text(cv_data).lower()
        
        # Common tech keywords
        tech_keywords = [
            "python", "java", "javascript", "react", "sql", "database",
            "api", "cloud", "aws", "docker", "git", "agile", "scrum",
            "frontend", "backend", "fullstack", "deployment", "ci/cd"
        ]
        
        found_keywords = []
        for keyword in tech_keywords:
            if keyword in full_text:
                found_keywords.append(keyword)
        
        keyword_coverage = (len(found_keywords) / len(tech_keywords)) * 100
        score = min(25, int(keyword_coverage * 0.25))
        
        if found_keywords:
            details.append(f"Found {len(found_keywords)}/{len(tech_keywords)} common tech keywords")
            details.append(f"Keywords detected: {', '.join(found_keywords[:5])}")
        else:
            details.append("⚠️  Very few industry keywords detected - ATS may not recognize expertise")
        
        if keyword_coverage < 30:
            details.append("❌ CRITICAL: Low keyword coverage means job matching will fail")
        
        return {
            "score": score,
            "max": 25,
            "percentage": round(keyword_coverage, 1),
            "details": details
        }
    
    def _analyze_skills(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skills section quality and clarity."""
        score = 15  # Default if skills exist
        details = []
        
        skills = cv_data.get("personal_skills", {}) or cv_data.get("skills", {})
        
        if not skills:
            details.append("❌ No skills section found")
            return {"score": 0, "max": 25, "details": details}
        
        # Check for organized skills
        if isinstance(skills, dict):
            skill_categories = len(skills)
            if skill_categories >= 3:
                details.append(f"✅ Well-organized skills into {skill_categories} categories")
                score = 22
            elif skill_categories >= 1:
                details.append(f"⚠️  Skills organized into {skill_categories} category - consider more structure")
                score = 18
        elif isinstance(skills, list):
            if len(skills) >= 10:
                details.append(f"✅ Good number of skills listed ({len(skills)})")
                score = 20
            else:
                details.append(f"⚠️  Only {len(skills)} skills listed - consider adding more relevant ones")
                score = 12
        
        return {
            "score": score,
            "max": 25,
            "details": details
        }
    
    def _analyze_experience(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze work experience clarity and relevance."""
        score = 0
        details = []
        
        experience = cv_data.get("work_experience", []) or cv_data.get("experience", [])
        
        if not experience:
            details.append("❌ No work experience found")
            return {"score": 0, "max": 25, "details": details}
        
        score = 10  # Base for having experience
        
        for i, job in enumerate(experience):
            job_title = job.get("job_title", "")
            description = job.get("description", "")
            
            # Check for weak verbs
            weak_verb_found = False
            for verb in self.weak_action_verbs:
                if verb.lower() in description.lower():
                    weak_verb_found = True
                    details.append(f"❌ Job {i+1}: Weak verb '{verb}' in description")
                    break
            
            # Check for strong verbs
            strong_verb_found = any(verb in description.lower() for verb in self.strong_action_verbs)
            if strong_verb_found:
                details.append(f"✅ Job {i+1}: Uses strong action verbs")
                score += 5
            
            # Check for quantifiable results
            if any(char.isdigit() for char in description):
                details.append(f"✅ Job {i+1}: Includes quantifiable metrics")
                score += 3
        
        score = min(25, score)
        
        return {
            "score": score,
            "max": 25,
            "details": details
        }
    
    def _analyze_formatting(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ATS-friendly formatting."""
        score = 20  # Default if structure is reasonable
        details = []
        
        # Check for standard sections
        required_sections = ["personal_info", "work_experience", "education", "personal_skills"]
        found_sections = [s for s in required_sections if s in cv_data and cv_data[s]]
        
        section_coverage = (len(found_sections) / len(required_sections)) * 100
        
        if len(found_sections) >= 4:
            details.append(f"✅ All standard sections present")
            score = 23
        elif len(found_sections) >= 3:
            details.append(f"✅ {len(found_sections)}/4 standard sections found")
            score = 20
        else:
            details.append(f"⚠️  Only {len(found_sections)}/4 standard sections - consider adding missing ones")
            score = 15
        
        # Check for problematic formatting
        full_text = self._extract_all_text(cv_data)
        
        # Check for tables (bad for ATS)
        if "table" in full_text.lower():
            details.append("⚠️  Mentions of tables detected - ATS may not parse correctly")
            score -= 3
        
        # Check for special characters
        special_char_count = len([c for c in full_text if not c.isalnum() and c not in " .,;:-_()[]{}"])
        if special_char_count > 20:
            details.append("⚠️  Many special characters detected - may confuse ATS parser")
            score -= 2
        
        return {
            "score": min(25, max(0, score)),
            "max": 25,
            "details": details
        }
    
    def _extract_all_text(self, cv_data: Dict[str, Any]) -> str:
        """Extract all text from CV data."""
        text_parts = []
        
        # Personal info
        if "personal_info" in cv_data:
            personal = cv_data["personal_info"]
            if isinstance(personal, dict):
                text_parts.extend(personal.values())
        
        # Experience
        for job in cv_data.get("work_experience", []):
            if isinstance(job, dict):
                text_parts.extend(job.values())
        
        # Education
        for edu in cv_data.get("education", []):
            if isinstance(edu, dict):
                text_parts.extend(edu.values())
        
        # Skills
        skills = cv_data.get("personal_skills", {}) or cv_data.get("skills", {})
        if isinstance(skills, dict):
            for skill_list in skills.values():
                if isinstance(skill_list, list):
                    text_parts.extend(skill_list)
        elif isinstance(skills, list):
            text_parts.extend(skills)
        
        # Summary
        if "summary" in cv_data:
            text_parts.append(cv_data["summary"])
        
        return " ".join([str(p) for p in text_parts if p])
    
    def _collect_all_issues(self, score_breakdown: Dict[str, Any]) -> List[Dict[str, str]]:
        """Collect all issues from the breakdown."""
        issues = []
        
        for category, data in score_breakdown.items():
            for detail in data.get("details", []):
                if detail.startswith("❌") or detail.startswith("⚠️"):
                    severity = "critical" if "❌" in detail else "warning"
                    issues.append({
                        "category": category,
                        "severity": severity,
                        "message": detail.replace("❌", "").replace("⚠️", "").strip()
                    })
        
        return issues
    
    def _prioritize_recommendations(self, issues: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Turn issues into prioritized recommendations."""
        recommendations = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for issue in issues:
            severity = issue.get("severity", "medium")
            priority = "critical" if severity == "critical" else "high"
            
            msg = issue["message"]
            if "keyword" in msg.lower():
                recommendations[priority].append(f"Add more industry-specific keywords to increase ATS recognition")
            elif "weak verb" in msg.lower():
                recommendations[priority].append(f"Replace weak action verbs with stronger ones (e.g., 'designed' instead of 'worked')")
            elif "section" in msg.lower():
                recommendations[priority].append(f"Add missing CV section to improve structure and readability")
            elif "skills" in msg.lower():
                recommendations[priority].append(f"Expand and organize skills section into relevant categories")
            else:
                recommendations[priority].append(msg)
        
        # Remove duplicates
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))
        
        return recommendations
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def generate_optimizations(self, cv_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate specific, transparent optimizations with BEFORE/AFTER/REASON.
        
        Returns list of changes, each with:
        - field: what's being changed
        - before: original text
        - after: optimized text
        - reason: why this improves ATS score
        """
        changes = []
        
        # Example: Improve weak verbs
        experience = cv_data.get("work_experience", [])
        for i, job in enumerate(experience):
            description = job.get("description", "")
            
            for weak_verb in self.weak_action_verbs:
                if weak_verb in description.lower():
                    # Create a stronger version
                    improved = self._replace_weak_verb(description, weak_verb)
                    
                    changes.append({
                        "field": f"experience[{i}].description",
                        "before": description,
                        "after": improved,
                        "reason": f"Replaced weak verb '{weak_verb}' with stronger action verb for better ATS keyword matching"
                    })
                    break  # Only one change per job for clarity
        
        return changes
    
    def _replace_weak_verb(self, text: str, weak_verb: str) -> str:
        """Replace a weak verb with a strong one."""
        replacements = {
            "worked": "Engineered",
            "was responsible for": "Led",
            "helped": "Collaborated on",
            "involved": "Spearheaded",
            "did": "Implemented",
            "was part of": "Contributed to"
        }
        
        strong_verb = replacements.get(weak_verb, "Developed")
        return text.replace(weak_verb, strong_verb)
