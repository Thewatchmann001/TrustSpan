"""
Job Aggregator Module
Aggregates jobs from multiple sources for Sierra Leonean job seekers:
- RemoteOK (remote tech jobs)
- Freelancer.com (freelance projects)
- We Work Remotely (quality remote jobs)
- Adzuna (global job aggregator)

Built for TrustBridge - Sierra Leone job access platform
"""
from typing import List, Dict, Any, Optional
import requests
import re
from app.utils.logger import logger
from app.core.config import settings


class JobAggregator:
    """Job aggregation service combining multiple remote job sources."""
    
    def __init__(self):
        self.remoteok_base_url = "https://remoteok.io/api"
        self.freelancer_base_url = "https://www.freelancer.com/api"
        self.freelancer_sandbox_url = "https://www.freelancer-sandbox.com/api"
        self.arbeitnow_url = "https://www.arbeitnow.com/api/job-board-api"  # Replaced WWR
        self.adzuna_base_url = "https://api.adzuna.com/v1/api/jobs"
        
    def search_jobs(
        self,
        keywords: List[str],
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search jobs from all configured APIs.
        Distributes limit across sources for variety.
        
        Returns:
            List of job/project dictionaries from multiple sources
        """
        logger.info(f"Searching jobs for keywords: {keywords}")
        
        all_jobs = []
        per_source_limit = max(15, limit // 3)  # More jobs per source
        
        # 1. RemoteOK API (free, no auth)
        try:
            remoteok_jobs = self._search_remoteok(keywords, per_source_limit)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Found {len(remoteok_jobs)} jobs from RemoteOK")
        except Exception as e:
            logger.error(f"RemoteOK API error: {str(e)}")
        
        # 2. Arbeitnow API (free, replaced WWR which is deprecated)
        try:
            arbeitnow_jobs = self._search_arbeitnow(keywords, per_source_limit)
            all_jobs.extend(arbeitnow_jobs)
            logger.info(f"Found {len(arbeitnow_jobs)} jobs from Arbeitnow")
        except Exception as e:
            logger.error(f"Arbeitnow API error: {str(e)}")
        
        # 3. Freelancer.com API (requires OAuth token)
        try:
            freelancer_projects = self._search_freelancer(keywords, per_source_limit)
            all_jobs.extend(freelancer_projects)
            logger.info(f"Found {len(freelancer_projects)} projects from Freelancer.com")
        except Exception as e:
            logger.error(f"Freelancer.com API error: {str(e)}")
        
        # 4. Adzuna API (requires API key, optional)
        try:
            adzuna_jobs = self._search_adzuna(keywords, location, per_source_limit)
            all_jobs.extend(adzuna_jobs)
            logger.info(f"Found {len(adzuna_jobs)} jobs from Adzuna")
        except Exception as e:
            logger.error(f"Adzuna API error: {str(e)}")
        
        logger.info(f"Total jobs found: {len(all_jobs)} from all sources")
        return all_jobs[:limit]
    
    def _search_remoteok(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search RemoteOK API for remote jobs."""
        try:
            url = self.remoteok_base_url
            
            headers = {
                'User-Agent': 'TrustBridge Job Aggregator (https://trustbridge.sl)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            jobs_data = response.json()
            
            # Filter jobs by keywords
            filtered_jobs = []
            for job in jobs_data[1:]:  # Skip first element (metadata)
                if not isinstance(job, dict):
                    continue
                
                job_title = job.get('position', '').lower()
                job_description = job.get('description', '').lower()
                company = job.get('company', '').lower()
                
                # Check if any keyword matches
                keyword_match = any(
                    keyword.lower() in job_title or 
                    keyword.lower() in job_description or 
                    keyword.lower() in company
                    for keyword in keywords
                )
                
                if keyword_match:
                    formatted_job = {
                        'title': job.get('position', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'description': self._clean_html(job.get('description', ''))[:500],
                        'applyUrl': job.get('url', ''),
                        'source': 'RemoteOK',
                        'type': 'Remote Job',
                        'posted_date': job.get('date', ''),
                        'skills': job.get('tags', []),
                        'salary': job.get('salary', ''),
                    }
                    filtered_jobs.append(formatted_job)
                
                if len(filtered_jobs) >= limit:
                    break
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"RemoteOK search error: {str(e)}")
            return []
    
    def _search_arbeitnow(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search Arbeitnow for remote jobs (replaced broken WWR API)."""
        try:
            headers = {
                'User-Agent': 'TrustBridge Job Aggregator (https://trustbridge.sl)',
                'Accept': 'application/json'
            }
            
            response = requests.get(self.arbeitnow_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs_data = data.get('data', [])
            
            filtered_jobs = []
            for job in jobs_data:
                if not isinstance(job, dict):
                    continue
                
                title = job.get('title', '').lower()
                description = job.get('description', '').lower()
                company = job.get('company_name', '').lower()
                tags = ' '.join(job.get('tags', [])).lower()
                
                # Check if any keyword matches
                keyword_match = any(
                    keyword.lower() in title or 
                    keyword.lower() in description or 
                    keyword.lower() in company or
                    keyword.lower() in tags
                    for keyword in keywords
                )
                
                if keyword_match:
                    formatted_job = {
                        'title': job.get('title', ''),
                        'company': job.get('company_name', 'Unknown'),
                        'location': job.get('location', 'Remote'),
                        'description': self._clean_html(job.get('description', ''))[:500],
                        'applyUrl': job.get('url', ''),
                        'source': 'Arbeitnow',
                        'type': 'Remote Job' if job.get('remote', False) else 'Job',
                        'posted_date': job.get('created_at', ''),
                        'skills': job.get('tags', []),
                        'salary': '',
                    }
                    filtered_jobs.append(formatted_job)
                
                if len(filtered_jobs) >= limit:
                    break
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"Arbeitnow search error: {str(e)}")
            return []
    
    def _search_freelancer(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Freelancer.com API for freelance projects.
        Requires FREELANCER_OAUTH_TOKEN in environment.
        """
        oauth_token = getattr(settings, 'FREELANCER_OAUTH_TOKEN', None)
        
        if not oauth_token:
            logger.debug("No Freelancer OAuth token configured - skipping Freelancer.com")
            return []
        
        try:
            # Use production or sandbox based on config
            use_sandbox = getattr(settings, 'FREELANCER_SANDBOX', False)
            base_url = self.freelancer_sandbox_url if use_sandbox else self.freelancer_base_url
            
            # Freelancer.com Projects API endpoint
            url = f"{base_url}/projects/0.1/projects/active/"
            
            headers = {
                'freelancer-oauth-v1': oauth_token,
                'Content-Type': 'application/json',
                'User-Agent': 'TrustBridge/1.0'
            }
            
            # Build query params
            params = {
                'query': ' '.join(keywords[:3]),  # Max 3 keywords
                'limit': limit,
                'compact': 'true',
                'project_types[]': ['fixed', 'hourly'],
                'full_description': 'false',
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 401:
                logger.error("Freelancer OAuth token expired or invalid")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            # Parse Freelancer projects
            projects = data.get('result', {}).get('projects', [])
            formatted_projects = []
            
            for project in projects:
                budget_min = project.get('budget', {}).get('minimum', 0)
                budget_max = project.get('budget', {}).get('maximum', 0)
                currency = project.get('currency', {}).get('code', 'USD')
                
                formatted_project = {
                    'title': project.get('title', ''),
                    'company': project.get('owner', {}).get('username', 'Freelancer Client'),
                    'location': 'Remote (Freelancer.com)',
                    'description': project.get('preview_description', '')[:500],
                    'applyUrl': f"https://www.freelancer.com/projects/{project.get('seo_url', '')}",
                    'source': 'Freelancer.com',
                    'type': 'Freelance Project',
                    'posted_date': '',
                    'skills': [s.get('name', '') for s in project.get('jobs', [])],
                    'salary': f"{currency} {budget_min}-{budget_max}",
                    'budget': {'min': budget_min, 'max': budget_max, 'currency': currency},
                    'bid_count': project.get('bid_stats', {}).get('bid_count', 0),
                }
                formatted_projects.append(formatted_project)
            
            return formatted_projects
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Freelancer.com request error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Freelancer.com search error: {str(e)}")
            return []
    
    def _search_adzuna(self, keywords: List[str], location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Adzuna API for global jobs.
        Requires ADZUNA_APP_ID and ADZUNA_API_KEY in environment.
        Falls back gracefully if not configured.
        """
        app_id = getattr(settings, 'ADZUNA_APP_ID', None)
        api_key = getattr(settings, 'ADZUNA_API_KEY', None)
        
        if not app_id or not api_key:
            logger.debug("No Adzuna API credentials configured - skipping Adzuna")
            return []
        
        try:
            # Use 'gb' (UK) as default country for remote jobs, or 'za' for Africa
            country = 'gb'
            url = f"{self.adzuna_base_url}/{country}/search/1"
            
            params = {
                'app_id': app_id,
                'app_key': api_key,
                'results_per_page': limit,
                'what': ' '.join(keywords[:5]),
                'content-type': 'application/json',
            }
            
            # Add location filter if provided
            if location:
                params['where'] = location
            
            headers = {
                'User-Agent': 'TrustBridge Job Aggregator (https://trustbridge.sl)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('results', [])
            
            formatted_jobs = []
            for job in jobs:
                formatted_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('display_name', 'Unknown'),
                    'location': job.get('location', {}).get('display_name', 'Unknown'),
                    'description': self._clean_html(job.get('description', ''))[:500],
                    'applyUrl': job.get('redirect_url', ''),
                    'source': 'Adzuna',
                    'type': 'Job',
                    'posted_date': job.get('created', ''),
                    'skills': [],
                    'salary': self._format_adzuna_salary(job),
                }
                formatted_jobs.append(formatted_job)
            
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"Adzuna search error: {str(e)}")
            return []
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ''
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _format_adzuna_salary(self, job: Dict) -> str:
        """Format Adzuna salary range with safe type conversion."""
        min_sal = job.get('salary_min')
        max_sal = job.get('salary_max')
        
        # Safe conversion helper
        def safe_int(val):
            if val is None:
                return None
            try:
                return int(float(val))  # Handle string/float values
            except (ValueError, TypeError):
                return None
        
        min_val = safe_int(min_sal)
        max_val = safe_int(max_sal)
        
        if min_val is not None and max_val is not None:
            return f"£{min_val:,} - £{max_val:,}"
        elif min_val is not None:
            return f"£{min_val:,}+"
        elif max_val is not None:
            return f"Up to £{max_val:,}"
        return ''