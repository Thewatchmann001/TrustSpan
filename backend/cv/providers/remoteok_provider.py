"""
RemoteOK Job Provider
Fetches remote tech jobs from RemoteOK API.
"""
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_provider import BaseJobProvider, JobSchema
from app.utils.logger import logger


class RemoteOKProvider(BaseJobProvider):
    """RemoteOK job provider."""
    
    def __init__(self):
        super().__init__("RemoteOK")
        self.base_url = "https://remoteok.io/api"
        self.timeout = 10
    
    async def fetch_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[JobSchema]:
        """Fetch jobs from RemoteOK."""
        import asyncio
        
        try:
            start_time = datetime.now()
            
            headers = {
                'User-Agent': 'TrustSpan Job Aggregator (https://trustspan.sl)'
            }
            
            # Use requests in async context (can be improved with aiohttp later)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, headers=headers, timeout=self.timeout)
            )
            response.raise_for_status()
            
            jobs_data = response.json()
            normalized_jobs = []
            
            # Skip first element (metadata)
            for job in jobs_data[1:]:
                if not isinstance(job, dict):
                    continue
                
                # Check keyword match
                job_title = job.get('position', '').lower()
                job_description = job.get('description', '').lower()
                company = job.get('company', '').lower()
                
                keyword_match = any(
                    keyword.lower() in job_title or 
                    keyword.lower() in job_description or 
                    keyword.lower() in company
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
        """Normalize RemoteOK job to JobSchema."""
        try:
            from datetime import timezone
            # Extract skills from tags and description
            tags = raw_job.get('tags', [])
            description = raw_job.get('description', '')
            skills = list(set(tags + self.extract_skills_from_text(description)))[:15]
            
            # Parse date
            date_str = raw_job.get('date', '')
            try:
                job_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if job_date.tzinfo is None:
                    job_date = job_date.replace(tzinfo=timezone.utc)
            except:
                job_date = datetime.now(timezone.utc)
            
            # Generate unique ID
            job_id = f"remoteok_{raw_job.get('id', '')}_{raw_job.get('position', '').lower().replace(' ', '_')}"
            
            return JobSchema(
                id=job_id,
                title=raw_job.get('position', 'Untitled Position'),
                company=raw_job.get('company', 'Unknown Company'),
                location=raw_job.get('location', 'Remote'),
                description=self._clean_html(description)[:1000],  # Limit description
                skills=skills,
                source="RemoteOK",
                url=raw_job.get('url', ''),
                date=job_date,
                metadata={
                    "salary": raw_job.get('salary', ''),
                    "job_type": "Remote",
                    "tags": tags
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to normalize RemoteOK job: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        return text.strip()
