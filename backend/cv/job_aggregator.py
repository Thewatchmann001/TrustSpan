"""
Job Aggregator Module
Aggregates jobs from multiple sources: RemoteOK + Freelancer.com
Built for TrustBridge - Sierra Leone job access platform
"""
from typing import List, Dict, Any, Optional
import requests
from app.utils.logger import logger
from app.core.config import settings


class JobAggregator:
    """Job aggregation service combining RemoteOK and Freelancer.com."""
    
    def __init__(self):
        self.remoteok_base_url = "https://remoteok.io/api"
        self.freelancer_base_url = "https://www.freelancer.com/api"
        self.freelancer_sandbox_url = "https://www.freelancer-sandbox.com/api"
        
    def search_jobs(
        self,
        keywords: List[str],
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search jobs from RemoteOK and Freelancer.com APIs.
        
        Returns:
            List of job/project dictionaries from both sources
        """
        logger.info(f"Searching jobs for keywords: {keywords}")
        
        all_jobs = []
        
        # 1. RemoteOK API (free, no auth)
        try:
            remoteok_jobs = self._search_remoteok(keywords, limit // 2)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Found {len(remoteok_jobs)} jobs from RemoteOK")
        except Exception as e:
            logger.error(f"RemoteOK API error: {str(e)}")
        
        # 2. Freelancer.com API (requires OAuth token)
        try:
            freelancer_projects = self._search_freelancer(keywords, limit // 2)
            all_jobs.extend(freelancer_projects)
            logger.info(f"Found {len(freelancer_projects)} projects from Freelancer.com")
        except Exception as e:
            logger.error(f"Freelancer.com API error: {str(e)}")
        
        return all_jobs[:limit]
    
    def _search_remoteok(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search RemoteOK API for remote jobs."""
        try:
            url = self.remoteok_base_url
            
            headers = {
                'User-Agent': 'TrustBridge Job Aggregator (https://trustbridge.com)'
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
                keyword_match = False
                for keyword in keywords:
                    if (keyword.lower() in job_title or 
                        keyword.lower() in job_description or 
                        keyword.lower() in company):
                        keyword_match = True
                        break
                
                if keyword_match:
                    formatted_job = {
                        'title': job.get('position', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'description': job.get('description', '')[:500],
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
    
    def _search_freelancer(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Freelancer.com API for freelance projects.
        Requires FREELANCER_OAUTH_TOKEN in environment.
        """
        oauth_token = getattr(settings, 'FREELANCER_OAUTH_TOKEN', None)
        
        if not oauth_token:
            logger.info("No Freelancer OAuth token configured - skipping Freelancer.com")
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