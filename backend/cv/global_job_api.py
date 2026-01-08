"""
Global Job API Module
Handles global job search across multiple platforms and APIs.
"""
from typing import List, Dict, Any, Optional
import requests
from app.utils.logger import logger


class GlobalJobAPI:
    """Global job search service."""
    
    def __init__(self):
        self.remoteok_base_url = "https://remoteok.io/api"
    
    def search_global_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search global job market.
        
        Returns:
            List of job opportunities from various sources
        """
        logger.info(f"Searching global jobs for: {query}")
        
        all_jobs = []
        
        # Search RemoteOK
        try:
            remoteok_jobs = self._search_remoteok_by_query(query, limit)
            all_jobs.extend(remoteok_jobs)
        except Exception as e:
            logger.error(f"RemoteOK search error: {str(e)}")
        
        return all_jobs[:limit]
    
    def match_cv_to_global_jobs(
        self,
        cv_data: Dict[str, Any],
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Match CV to global job opportunities.
        
        Returns:
            List of matched jobs with compatibility scores
        """
        logger.info("Matching CV to global jobs")
        
        # Extract skills from CV
        skills = []
        if cv_data.get("skills"):
            skills_data = cv_data["skills"]
            if isinstance(skills_data, dict):
                skills.extend(skills_data.get("job_related_skills", []))
                skills.extend(skills_data.get("computer_skills", []))
        
        # Search jobs
        jobs = self.search_global_jobs(query, location, limit)
        
        # Add match scores
        for job in jobs:
            job["match_score"] = self._calculate_job_match(cv_data, job)
        
        # Sort by match score
        jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return jobs
    
    def _search_remoteok_by_query(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search RemoteOK by query."""
        try:
            url = f"{self.remoteok_base_url}"
            
            headers = {
                'User-Agent': 'TrustBridge Job Matcher (https://trustbridge.com)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            jobs_data = response.json()
            
            # Filter by query
            filtered_jobs = []
            query_lower = query.lower()
            
            for job in jobs_data[1:]:  # Skip metadata
                if not isinstance(job, dict):
                    continue
                
                job_text = f"{job.get('position', '')} {job.get('company', '')} {job.get('description', '')}".lower()
                
                if query_lower in job_text:
                    formatted_job = {
                        'title': job.get('position', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'description': job.get('description', ''),
                        'applyUrl': job.get('url', ''),
                        'source': 'RemoteOK',
                        'posted_date': job.get('date', ''),
                        'skills': job.get('tags', []),
                        'salary': job.get('salary', ''),
                    }
                    filtered_jobs.append(formatted_job)
                
                if len(filtered_jobs) >= limit:
                    break
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"RemoteOK query search error: {str(e)}")
            return []
    
    def _calculate_job_match(self, cv_data: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculate match score between CV and job."""
        score = 0.0
        
        # Extract CV skills
        cv_skills = []
        if cv_data.get("skills"):
            skills_data = cv_data["skills"]
            if isinstance(skills_data, dict):
                cv_skills.extend(skills_data.get("job_related_skills", []))
                cv_skills.extend(skills_data.get("computer_skills", []))
        
        cv_skills_lower = [s.lower() for s in cv_skills]
        
        # Check skill matches
        job_skills = job.get("skills", [])
        if job_skills:
            matches = sum(1 for skill in job_skills if skill.lower() in cv_skills_lower)
            score += (matches / len(job_skills)) * 0.6
        
        # Check title/description matches
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        cv_text = str(cv_data).lower()
        
        # Simple keyword overlap
        job_words = set(job_text.split())
        cv_words = set(cv_text.split())
        overlap = len(job_words.intersection(cv_words))
        
        if len(job_words) > 0:
            score += (overlap / len(job_words)) * 0.4
        
        return min(1.0, score)