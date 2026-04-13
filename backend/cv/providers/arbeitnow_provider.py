"""
Arbeitnow Job Provider
Fetches remote jobs from Arbeitnow API.
"""
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_provider import BaseJobProvider, JobSchema
from app.utils.logger import logger


class ArbeitnowProvider(BaseJobProvider):
    """Arbeitnow job provider."""
    
    def __init__(self):
        super().__init__("Arbeitnow")
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"
        self.timeout = 10
    
    async def fetch_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[JobSchema]:
        """Fetch jobs from Arbeitnow."""
        import asyncio
        
        try:
            start_time = datetime.now()
            
            headers = {
                'User-Agent': 'TrustSpan Job Aggregator (https://trustspan.sl)',
                'Accept': 'application/json'
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, headers=headers, timeout=self.timeout)
            )
            response.raise_for_status()
            
            data = response.json()
            jobs_data = data.get('data', [])
            normalized_jobs = []
            
            for job in jobs_data:
                if not isinstance(job, dict):
                    continue
                
                # Check keyword match
                title = job.get('title', '').lower()
                description = job.get('description', '').lower()
                company = job.get('company_name', '').lower()
                tags = ' '.join(job.get('tags', [])).lower()
                
                keyword_match = any(
                    keyword.lower() in title or 
                    keyword.lower() in description or 
                    keyword.lower() in company or
                    keyword.lower() in tags
                    for keyword in keywords
                )
                
                if keyword_match:
                    normalized = self.normalize_job(job)
                    if normalized:
                        normalized_jobs.append(normalized)
                    
                    if len(normalized_jobs) >= limit:
                        break
            
            duration = (datetime.now() - start_time).total_seconds()
            self.log_fetch(len(normalized_jobs), duration)
            
            return normalized_jobs
            
        except requests.exceptions.Timeout:
            self.log_error(Exception("Request timeout"))
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.log_rate_limit()
            self.log_error(e)
            return []
        except Exception as e:
            self.log_error(e)
            return []
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Optional[JobSchema]:
        """Normalize Arbeitnow job to JobSchema."""
        try:
            from datetime import timezone
            # Extract skills from tags and description
            tags = raw_job.get('tags', [])
            description = raw_job.get('description', '')
            skills = list(set(tags + self.extract_skills_from_text(description)))[:15]
            
            # Parse date
            date_str = raw_job.get('created_at', '')
            try:
                job_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if job_date.tzinfo is None:
                    job_date = job_date.replace(tzinfo=timezone.utc)
            except:
                job_date = datetime.now(timezone.utc)
            
            # Generate unique ID
            job_id = f"arbeitnow_{raw_job.get('slug', '')}_{raw_job.get('title', '').lower().replace(' ', '_')}"
            
            return JobSchema(
                id=job_id,
                title=raw_job.get('title', 'Untitled Position'),
                company=raw_job.get('company_name', 'Unknown Company'),
                location=raw_job.get('location', 'Remote'),
                description=self._clean_html(description)[:1000],
                skills=skills,
                source="Arbeitnow",
                url=raw_job.get('url', ''),
                date=job_date,
                metadata={
                    "remote": raw_job.get('remote', False),
                    "job_type": "Remote" if raw_job.get('remote', False) else "On-site",
                    "tags": tags
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to normalize Arbeitnow job: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        return text.strip()
