"""
Freelancer.com Job Provider
Fetches freelance projects from Freelancer.com API.
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_provider import BaseJobProvider, JobSchema
from app.core.config import settings
from app.utils.logger import logger


class FreelancerProvider(BaseJobProvider):
    """Freelancer.com job provider."""
    
    def __init__(self):
        super().__init__("Freelancer")
        self.base_url = "https://www.freelancer.com/api"
        self.sandbox_url = "https://www.freelancer-sandbox.com/api"
        self.timeout = 10
        self.oauth_token = getattr(settings, 'FREELANCER_OAUTH_TOKEN', None)
        
        if not self.oauth_token:
            self.enabled = False
            logger.warning("Freelancer.com OAuth token not configured - provider disabled")
    
    async def fetch_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[JobSchema]:
        """Fetch projects from Freelancer.com."""
        if not self.is_enabled():
            return []
        
        import asyncio
        
        try:
            start_time = datetime.now()
            
            use_sandbox = getattr(settings, 'FREELANCER_SANDBOX', False)
            base_url = self.sandbox_url if use_sandbox else self.base_url
            url = f"{base_url}/projects/0.1/projects/active/"
            
            headers = {
                'freelancer-oauth-v1': self.oauth_token,
                'Content-Type': 'application/json',
                'User-Agent': 'TrustSpan/1.0',
            }
            
            # Build search query
            query = ' '.join(keywords[:3])  # Limit to 3 keywords
            
            params = {
                'query': query,
                'limit': min(limit, 100),
                'offset': 0
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, params=params, timeout=self.timeout)
            )
            
            if response.status_code == 429:
                self.log_rate_limit()
                return []
            
            response.raise_for_status()
            data = response.json()
            
            projects = data.get('result', {}).get('projects', [])
            normalized_jobs = []
            
            for project in projects:
                normalized = self.normalize_job(project)
                if normalized:
                    normalized_jobs.append(normalized)
                
                if len(normalized_jobs) >= limit:
                    break
            
            duration = (datetime.now() - start_time).total_seconds()
            self.log_fetch(len(normalized_jobs), duration)
            
            return normalized_jobs
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.log_rate_limit()
            elif e.response.status_code == 401:
                self.enabled = False
                logger.error("Freelancer.com authentication failed - provider disabled")
            self.log_error(e)
            return []
        except Exception as e:
            self.log_error(e)
            return []
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Optional[JobSchema]:
        """Normalize Freelancer project to JobSchema."""
        try:
            description = raw_job.get('description', '')
            skills = self.extract_skills_from_text(description)
            
            # Add skills from project attributes
            if 'jobs' in raw_job:
                skills.extend([j.get('name', '') for j in raw_job['jobs']])
            
            skills = list(set(skills))[:15]
            
            # Parse date
            date_str = raw_job.get('submitdate', '')
            try:
                job_date = datetime.fromtimestamp(int(date_str))
            except:
                job_date = datetime.now()
            
            # Generate unique ID
            job_id = f"freelancer_{raw_job.get('id', '')}"
            
            return JobSchema(
                id=job_id,
                title=raw_job.get('title', 'Untitled Project'),
                company="Freelancer.com",
                location="Remote",
                description=description[:1000],
                skills=skills,
                source="Freelancer.com",
                url=f"https://www.freelancer.com/projects/{raw_job.get('seo_url', '')}",
                date=job_date,
                metadata={
                    "budget": raw_job.get('budget', {}),
                    "job_type": "Freelance Project",
                    "currency": raw_job.get('currency', {}).get('code', 'USD')
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to normalize Freelancer job: {e}")
            return None
