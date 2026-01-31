"""
Domain Filter Module
Implements strict domain-based filtering for job matching.

STAGE 1: Domain Filtering (STRICT)
- Extracts domain from CV
- Excludes jobs that don't match domain
- Only passes domain-matched jobs to Stage 2 (relevance scoring)
"""
from typing import List, Dict, Any, Set, Optional
from app.utils.logger import logger
from cv.domain_extractor import DomainExtractor


class DomainFilter:
    """Filters jobs by domain before relevance scoring."""
    
    def __init__(self):
        self.domain_extractor = DomainExtractor()
    
    def filter_jobs_by_domain(
        self,
        jobs: List[Dict[str, Any]],
        cv_data: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter jobs by domain match.
        
        Args:
            jobs: List of job dictionaries
            cv_data: CV data dictionary
        
        Returns:
            Tuple of (matched_jobs, excluded_jobs)
        """
        if not jobs:
            return [], []
        
        # Extract domains from CV with timeout
        from cv.timeout_utils import safe_execute_with_timeout
        cv_domains = safe_execute_with_timeout(
            self.domain_extractor.extract_domains,
            timeout_seconds=15,
            fallback=set(),
            cv_data=cv_data
        )
        
        # HARD GATE: If no domains extracted, check for tech skills fallback
        # This handles cases where domain extraction fails but CV clearly has tech skills
        if not cv_domains:
            logger.warning("No domains extracted from CV - checking tech skills fallback")
            
            # Extract skills to check for tech indicators
            skills = self.domain_extractor._extract_skills(cv_data)
            skills_text = " ".join(skills).lower()
            
            # Tech skills that clearly indicate technology domain
            tech_indicators = [
                "python", "javascript", "java", "c++", "c#", "react", "node", "angular", "vue",
                "programming", "coding", "software", "developer", "engineer", "backend", "frontend",
                "database", "sql", "postgresql", "mongodb", "api", "rest", "graphql",
                "blockchain", "web3", "ai", "ml", "machine learning", "artificial intelligence",
                "docker", "kubernetes", "aws", "azure", "cloud", "git", "github", "gitlab",
                "flask", "django", "fastapi", "tensorflow", "pytorch", "data science"
            ]
            
            # Count tech indicators in skills
            tech_match_count = sum(1 for indicator in tech_indicators if indicator in skills_text)
            
            if tech_match_count >= 3:  # If 3+ tech skills found, assume technology domain
                logger.info(f"Tech skills fallback: Found {tech_match_count} tech indicators - assuming technology domain")
                cv_domains = {"technology"}
            else:
                # Not enough tech skills - reject all jobs
                logger.warning(f"Tech skills fallback: Only {tech_match_count} tech indicators found - REJECTING all jobs (hard gate)")
                return [], jobs  # Return empty matched, all excluded
        
        matched_jobs = []
        excluded_jobs = []
        
        for job in jobs:
            if self.domain_extractor.is_domain_match(job, cv_domains):
                matched_jobs.append(job)
                logger.debug(f"[DOMAIN MATCHING] Matched job '{job.get('title', 'Unknown')}' - domains: {cv_domains}")
            else:
                excluded_jobs.append(job)
                logger.debug(
                    f"[DOMAIN MATCHING] Excluded job '{job.get('title', 'Unknown')}' "
                    f"from '{job.get('company', 'Unknown')}' - domain mismatch "
                    f"(CV domains: {cv_domains})"
                )
        
        logger.info(
            f"[DOMAIN FILTERING] Result: {len(matched_jobs)}/{len(jobs)} jobs matched domains {cv_domains}. "
            f"Excluded {len(excluded_jobs)} jobs."
        )
        
        # Log sample excluded jobs for debugging
        if excluded_jobs:
            excluded_samples = excluded_jobs[:5]
            logger.debug(f"[DOMAIN FILTERING] Sample excluded jobs: {[job.get('title', 'Unknown') for job in excluded_samples]}")
        
        # Log sample matched jobs for debugging
        if matched_jobs:
            matched_samples = matched_jobs[:5]
            logger.debug(f"[DOMAIN FILTERING] Sample matched jobs: {[job.get('title', 'Unknown') for job in matched_samples]}")
        
        return matched_jobs, excluded_jobs
    
    def get_domain_explanation(
        self,
        cv_data: Dict[str, Any],
        job: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get explanation for why a job was matched or excluded.
        
        Returns:
            Explanation string or None
        """
        cv_domains = self.domain_extractor.extract_domains(cv_data)
        
        if not cv_domains:
            return None
        
        job_text = " ".join([
            str(job.get("title", "")),
            str(job.get("description", ""))
        ]).lower()
        
        # Find matching domain
        for domain in cv_domains:
            domain_keywords = self.domain_extractor.get_domain_keywords(domain)
            
            for keyword in domain_keywords.get("roles", []):
                if keyword in job_text:
                    return f"Matched {domain} domain: job title/description contains '{keyword}'"
        
        return f"Excluded: job does not match CV domains {cv_domains}"
