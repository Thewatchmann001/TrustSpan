"""
Unified Job Keyword Extraction Module

Provides consistent keyword extraction across all CV-based job search flows.
Implements keyword tiers and platform-aware mapping to fix inconsistencies
between quick upload and CV editor job matching.
"""
from typing import Dict, List, Any, Optional, Tuple
import re
from app.utils.logger import logger


class JobKeywordExtractor:
    """Unified keyword extraction for consistent job matching across all flows."""
    
    # Keyword tiers
    TIER_1_ROLE_KEYWORDS = {
        # Software/Development
        "software engineer", "developer", "backend engineer", "frontend engineer",
        "fullstack engineer", "python developer", "java developer", "javascript developer",
        "react developer", "node developer", "devops engineer", "systems engineer",
        "data engineer", "machine learning engineer", "ai engineer", "data scientist",
        "product engineer", "solutions architect", "technical lead", "engineering manager",
        "tech lead", "staff engineer", "principal engineer", "architect",
        # Other Tech
        "database administrator", "security engineer", "network engineer", "cloud architect",
        "site reliability engineer", "infrastructure engineer", "platform engineer",
        "quality assurance engineer", "test engineer", "automation engineer",
    }
    
    TIER_2_SKILL_KEYWORDS = {
        # Languages
        "python", "javascript", "java", "c++", "typescript", "golang", "rust", "ruby",
        "php", "scala", "kotlin", "c#", "swift", "objective-c",
        # Frameworks & Libraries
        "react", "angular", "vue", "django", "flask", "fastapi", "spring", "rails",
        "nodejs", "express", "nextjs", "nuxt", "graphql", "rest", "api",
        # Databases
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "sql", "nosql", "database",
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab",
        "terraform", "ansible", "ci/cd", "cloud", "devops",
        # Concepts
        "microservices", "distributed systems", "agile", "scrum", "machine learning",
        "ai", "data science", "analytics", "blockchain", "web3", "saas",
    }
    
    TIER_3_SENIOR_TITLES = {
        "director", "head of", "vp ", "vice president", "chief", "cto", "ceo",
        "lead", "manager", "principal", "staff",
    }
    
    def extract_keywords(self, cv_data: Dict[str, Any], include_senior: bool = True) -> Dict[str, Any]:
        """
        Extract keywords from CV in structured tiers.
        
        Returns:
            {
                "tier_1_roles": [...],        # Job titles & roles
                "tier_2_skills": [...],       # Technical skills
                "tier_3_senior": [...],       # Senior/executive titles (optional)
                "all_keywords": [...],        # All combined for fallback
                "primary_search": [...],      # Tier 1 + Tier 2 (recommended)
                "skills_only": [...]          # Tier 2 only (for skills-specific APIs)
            }
        """
        tier_1_roles = []
        tier_2_skills = []
        tier_3_senior = []
        raw_keywords = []
        
        # ========== Extract Tier 1: Role Titles ==========
        # From job titles in experience
        experience = cv_data.get("work_experience") or cv_data.get("experience") or []
        for exp in experience:
            if isinstance(exp, dict):
                job_title = exp.get("job_title") or exp.get("title") or ""
                if job_title:
                    job_title_str = str(job_title).strip()
                    raw_keywords.append(job_title_str)
                    
                    # Check if it matches Tier 1
                    jt_lower = job_title_str.lower()
                    for role in self.TIER_1_ROLE_KEYWORDS:
                        if role in jt_lower:
                            tier_1_roles.append(role)
                            break
        
        # ========== Extract Tier 2: Skills ==========
        # Technical skills
        skills_data = cv_data.get("personal_skills") or cv_data.get("skills") or {}
        
        if isinstance(skills_data, dict):
            # Try multiple skill field names
            skill_lists = skills_data.get("technical", []) or \
                         skills_data.get("technical_skills", []) or \
                         skills_data.get("computer_skills", []) or []
            
            if isinstance(skill_lists, list):
                for skill in skill_lists:
                    skill_str = str(skill).lower().strip()
                    raw_keywords.append(skill_str)
                    
                    # Check if matches Tier 2
                    for skill_kw in self.TIER_2_SKILL_KEYWORDS:
                        if skill_kw in skill_str or skill_str in skill_kw:
                            tier_2_skills.append(skill_kw)
                            break
        
        # Also extract from job descriptions
        for exp in experience:
            if isinstance(exp, dict):
                description = exp.get("description") or ""
                if description:
                    desc_lower = str(description).lower()
                    for skill_kw in self.TIER_2_SKILL_KEYWORDS:
                        if skill_kw in desc_lower and skill_kw not in tier_2_skills:
                            tier_2_skills.append(skill_kw)
        
        # ========== Extract Tier 3: Senior Titles (Optional) ==========
        if include_senior:
            for exp in experience:
                if isinstance(exp, dict):
                    job_title = exp.get("job_title") or exp.get("title") or ""
                    if job_title:
                        jt_lower = str(job_title).lower()
                        for senior_title in self.TIER_3_SENIOR_TITLES:
                            if senior_title in jt_lower:
                                tier_3_senior.append(senior_title.strip())
                                break
        
        # Derive generic roles from skills if Tier 1 is empty
        if not tier_1_roles:
            derived_roles = self._derive_roles_from_skills(tier_2_skills)
            tier_1_roles.extend([r for r in derived_roles if r not in tier_1_roles])

        # ========== Build result keywords ==========
        # Remove duplicates while preserving order
        tier_1_roles = self._deduplicate(tier_1_roles)
        tier_2_skills = self._deduplicate(tier_2_skills)
        tier_3_senior = self._deduplicate(tier_3_senior)
        
        # Combine for different scenarios
        primary_search = tier_1_roles + tier_2_skills  # Best for general job search
        skills_only = tier_2_skills  # For Freelancer.com
        all_keywords = tier_1_roles + tier_2_skills + tier_3_senior + raw_keywords
        
        logger.info(f"Keyword extraction results:")
        logger.info(f"  Tier 1 Roles: {tier_1_roles}")
        logger.info(f"  Tier 2 Skills: {tier_2_skills}")
        logger.info(f"  Tier 3 Senior: {tier_3_senior}")
        logger.info(f"  Primary search keywords: {primary_search[:10]}")
        
        return {
            "tier_1_roles": tier_1_roles[:5],
            "tier_2_skills": tier_2_skills[:10],
            "tier_3_senior": tier_3_senior[:3],
            "all_keywords": all_keywords[:20],
            "primary_search": primary_search[:15],  # Tier 1 + Tier 2
            "skills_only": skills_only[:10],  # Tier 2 only
            "raw_keywords": raw_keywords[:20]  # Original keywords as fallback
        }
    
    def get_platform_keywords(self, 
                             cv_data: Dict[str, Any], 
                             platform: str) -> List[str]:
        """Get platform-specific keywords optimized for each source."""
        
        all_kw = self.extract_keywords(cv_data)
        
        if platform.lower() in ["remoteok", "arbeitnow"]:
            # Role + Skills works best
            return all_kw["primary_search"]
        
        elif platform.lower() == "freelancer":
            # Skills ONLY for freelancer
            return all_kw["skills_only"]
        
        elif platform.lower() == "adzuna":
            # Adzuna works best with SIMPLE, GENERIC keywords (1-2 words max)
            # Since we're searching for remote jobs from multiple countries,
            # use the most common, universal job titles
            
            # Extract simple job titles (remove seniority, keep core role)
            simple_titles = []
            for role in all_kw["tier_1_roles"][:2]:
                # Normalize to simple form
                role_lower = role.lower()
                # Map to common Adzuna-friendly titles
                if "developer" in role_lower or "programmer" in role_lower:
                    simple_titles.append("developer")
                elif "engineer" in role_lower:
                    simple_titles.append("software engineer")
                elif "analyst" in role_lower:
                    simple_titles.append("data analyst")
                elif "scientist" in role_lower:
                    simple_titles.append("data scientist")
                else:
                    # Keep original if it's already simple (1-2 words)
                    if len(role.split()) <= 2:
                        simple_titles.append(role)
            
            # Use top 2 skills (single words work best)
            top_skills = [s for s in all_kw["tier_2_skills"][:2] if len(s.split()) == 1]
            
            # Return: first title + first skill (Adzuna prefers 1-2 word queries)
            if simple_titles and top_skills:
                return [f"{simple_titles[0]} {top_skills[0]}"]  # e.g., "developer python"
            elif simple_titles:
                return simple_titles[:1]  # Just the title, e.g., "developer"
            elif top_skills:
                return top_skills[:1]  # Just the skill, e.g., "python"
            else:
                return ["developer"]  # Fallback
        
        else:
            # Default: primary search keywords
            return all_kw["primary_search"]
    
    def _deduplicate(self, items: List[str]) -> List[str]:
        """Remove duplicates while preserving order."""
        seen = set()
        result = []
        for item in items:
            item_lower = str(item).lower().strip()
            if item_lower not in seen and item_lower:
                seen.add(item_lower)
                result.append(item_lower)
        return result

    def _derive_roles_from_skills(self, skills: List[str]) -> List[str]:
        """Heuristically derive generic roles from skills when titles are missing."""
        s = set(skills or [])
        derived = []
        if any(k in s for k in ["python", "javascript", "typescript", "java", "react", "nodejs", "fastapi", "django", "spring"]):
            derived.append("software engineer")
        if any(k in s for k in ["django", "fastapi", "nodejs", "express", "graphql", "rest", "api"]):
            derived.append("backend engineer")
        if any(k in s for k in ["react", "vue", "angular", "typescript"]):
            derived.append("frontend engineer")
        if any(k in s for k in ["docker", "kubernetes", "terraform", "ci/cd", "aws", "azure", "gcp"]):
            derived.append("devops engineer")
        if any(k in s for k in ["data science", "sql", "postgresql", "mysql", "mongodb", "spark"]):
            derived.append("data engineer")
        if any(k in s for k in ["machine learning", "ai", "pytorch", "tensorflow"]):
            derived.append("machine learning engineer")
        return self._deduplicate(derived)

    def _normalize_titles(self, titles: List[str]) -> List[str]:
        """Normalize titles: remove seniority, punctuation, keep concise role names."""
        normalized = []
        for t in titles or []:
            tl = str(t).lower()
            # Remove seniority prefixes
            for senior in ["senior", "lead", "principal", "staff", "director", "head", "vp", "chief"]:
                tl = tl.replace(senior, "")
            # Remove punctuation and extra words
            tl = tl.replace("&", " ").replace("/", " ").replace("-", " ")
            tl = re.sub(r"[^a-z\s]", "", tl)
            tl = re.sub(r"\s+", " ", tl).strip()
            # Map to known role keywords if possible
            matched = None
            for role in self.TIER_1_ROLE_KEYWORDS:
                if role in tl:
                    matched = role
                    break
            normalized.append(matched or tl)
        return self._deduplicate(normalized)
