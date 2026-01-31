"""
Job Aggregator Module
Aggregates jobs from multiple sources for Sierra Leonean job seekers:
- RemoteOK (remote tech jobs)
- Freelancer.com (freelance projects)
- Arbeitnow (quality remote jobs)
- Adzuna (global job aggregator)
- Y-Combinator Jobs (startup jobs via RapidAPI)
- Internships (internship opportunities via RapidAPI)

Built for TrustBridge - Sierra Leone job access platform

Enhanced with:
- Platform-aware keyword selection
- Fallback logic for zero results
- Per-platform keyword strategy optimization
"""
from typing import List, Dict, Any, Optional
import requests
import re
import http.client
import json
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
        
        # RapidAPI endpoints
        self.rapidapi_yc_host = "free-y-combinator-jobs-api.p.rapidapi.com"
        self.rapidapi_internships_host = "internships-api.p.rapidapi.com"
        self.rapidapi_key = getattr(settings, 'RAPIDAPI_KEY', None)
        
        if self.rapidapi_key:
            logger.info(f"RapidAPI key configured: {self.rapidapi_key[:10]}...")
        else:
            logger.warning("RapidAPI key not found in settings - Y-Combinator and Internships APIs will be disabled")
        
        # Tier definitions for fallback logic
        self.SKILL_KEYWORDS = {
            "python", "javascript", "java", "c++", "typescript", "golang", "rust",
            "react", "angular", "vue", "django", "flask", "fastapi", "spring",
            "nodejs", "express", "postgresql", "mysql", "mongodb", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
            "machine learning", "ai", "data science", "api", "rest", "graphql"
        }
        
    def search_jobs(
        self,
        keywords: List[str],
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50,
        platform_keywords: Optional[Dict[str, List[str]]] = None,
        cv_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search jobs from all configured APIs.
        Distributes limit across sources for variety.
        
        Args:
            keywords: Raw keywords to search with
            job_titles: Specific job titles (optional)
            location: Location filter (optional)
            limit: Total limit across all sources
            platform_keywords: Dict with platform-specific keywords {platform: [keywords]}
                             If provided, will use these instead of raw keywords
        
        Returns:
            List of job/project dictionaries from multiple sources
        """
        logger.info(f"Searching jobs for keywords: {keywords}")
        
        all_jobs = []
        # Increased per-source limit: max(25, limit // 2) for better coverage
        # With limit=100: per_source_limit = max(25, 50) = 50 jobs per source
        # Total: 50 × 4 sources = 200 jobs (before domain filtering)
        per_source_limit = max(25, limit // 2)  # More jobs per source for better variety
        
        # 1. RemoteOK API (free, no auth) - Works best with role + skills
        try:
            kw = keywords
            if platform_keywords and isinstance(platform_keywords.get("remoteok"), list) and platform_keywords.get("remoteok"):
                kw = platform_keywords.get("remoteok")
            remoteok_jobs = self._search_remoteok(kw, per_source_limit)
            # Fallback with skills-only if zero results
            if not remoteok_jobs:
                skills_only = [k for k in kw if k.lower() in self.SKILL_KEYWORDS]
                if skills_only:
                    logger.info(f"RemoteOK: No results with primary keywords, retrying with skills-only: {skills_only[:3]}...")
                    remoteok_jobs = self._search_remoteok(skills_only, per_source_limit)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Found {len(remoteok_jobs)} jobs from RemoteOK (keywords: {kw[:3]}...)")
        except Exception as e:
            logger.error(f"RemoteOK API error: {str(e)}")
        
        # 2. Arbeitnow API (free, replaced WWR which is deprecated) - Works best with role + skills
        try:
            kw = keywords
            if platform_keywords and isinstance(platform_keywords.get("arbeitnow"), list) and platform_keywords.get("arbeitnow"):
                kw = platform_keywords.get("arbeitnow")
            arbeitnow_jobs = self._search_arbeitnow(kw, per_source_limit)
            # Fallback with skills-only if zero results
            if not arbeitnow_jobs:
                skills_only = [k for k in kw if k.lower() in self.SKILL_KEYWORDS]
                if skills_only:
                    logger.info(f"Arbeitnow: No results with primary keywords, retrying with skills-only: {skills_only[:3]}...")
                    arbeitnow_jobs = self._search_arbeitnow(skills_only, per_source_limit)
            all_jobs.extend(arbeitnow_jobs)
            logger.info(f"Found {len(arbeitnow_jobs)} jobs from Arbeitnow (keywords: {kw[:3]}...)")
        except Exception as e:
            logger.error(f"Arbeitnow API error: {str(e)}")
        
        # 3. Freelancer.com API (requires OAuth token) - Works ONLY with skills
        try:
            # Freelancer needs skills-only keywords
            freelancer_kw = keywords
            if platform_keywords and isinstance(platform_keywords.get("freelancer"), list) and platform_keywords.get("freelancer"):
                freelancer_kw = platform_keywords.get("freelancer")
            freelancer_projects = self._search_freelancer(freelancer_kw, per_source_limit)
            all_jobs.extend(freelancer_projects)
            logger.info(f"Found {len(freelancer_projects)} projects from Freelancer.com (keywords: {freelancer_kw[:3]}...)")
        except Exception as e:
            logger.error(f"Freelancer.com API error: {str(e)}")
        
        # 4. Adzuna API (requires API key, optional) - Works best with short title format
        try:
            kw = keywords
            if platform_keywords and isinstance(platform_keywords.get("adzuna"), list) and platform_keywords.get("adzuna"):
                kw = platform_keywords.get("adzuna")
            adzuna_jobs = self._search_adzuna(kw, location, per_source_limit)
            all_jobs.extend(adzuna_jobs)
            logger.info(f"Found {len(adzuna_jobs)} jobs from Adzuna (keywords: {kw[:3]}...)")
        except Exception as e:
            logger.error(f"Adzuna API error: {str(e)}")
        
        # 5. Y-Combinator Jobs via RapidAPI
        if self.rapidapi_key:
            try:
                yc_jobs = self._search_rapidapi_yc(keywords, per_source_limit)
                all_jobs.extend(yc_jobs)
                logger.info(f"Found {len(yc_jobs)} jobs from Y-Combinator (keywords: {keywords[:3]}...)")
            except Exception as e:
                logger.error(f"Y-Combinator API error: {str(e)}")
        
        # 6. Internships via RapidAPI
        if self.rapidapi_key:
            try:
                internship_jobs = self._search_rapidapi_internships(keywords, per_source_limit)
                all_jobs.extend(internship_jobs)
                logger.info(f"Found {len(internship_jobs)} internships from RapidAPI (keywords: {keywords[:3]}...)")
            except Exception as e:
                logger.error(f"Internships API error: {str(e)}")
        
        logger.info(f"Total jobs found: {len(all_jobs)} from all sources")
        
        # STAGE 1: DOMAIN FILTERING (HARD GATE - NON-NEGOTIABLE)
        # Apply domain filtering if CV data is provided
        # CRITICAL: Domain filtering is a HARD GATE - no fallback
        if cv_data:
            try:
                from cv.domain_filter import DomainFilter
                from cv.timeout_utils import safe_execute_with_timeout
                
                domain_filter = DomainFilter()
                # Apply timeout to domain filtering
                result = safe_execute_with_timeout(
                    domain_filter.filter_jobs_by_domain,
                    timeout_seconds=15,
                    fallback=([], all_jobs),  # On timeout, reject all jobs
                    jobs=all_jobs,
                    cv_data=cv_data
                )
                matched_jobs, excluded_jobs = result
                all_jobs = matched_jobs  # ONLY domain-matched jobs proceed
                logger.info(f"DOMAIN FILTERING (HARD GATE): {len(all_jobs)} jobs passed, {len(excluded_jobs)} jobs REJECTED")
            except Exception as e:
                logger.error(f"Domain filtering error: {str(e)} - REJECTING all jobs (hard gate)")
                # HARD GATE: On error, reject all jobs - NO FALLBACK
                all_jobs = []
        else:
            # HARD GATE: If no CV data, reject all jobs
            logger.warning("No CV data provided for domain filtering - REJECTING all jobs (hard gate)")
            all_jobs = []
        
        # STAGE 2: RELEVANCE SCORING
        # Score jobs by relevance (only domain-matched jobs reach here)
        if cv_data and all_jobs:
            all_jobs = self._score_jobs_by_relevance(all_jobs, cv_data)
            # Sort by relevance score (descending)
            all_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
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
        Note: Freelancer.com API requires authentication and may return 0 results if:
        - OAuth token is not configured or expired
        - No projects match the keywords
        - API endpoint or format is incorrect
        """
        oauth_token = getattr(settings, 'FREELANCER_OAUTH_TOKEN', None)
        
        if not oauth_token:
            logger.debug("No Freelancer OAuth token configured - skipping Freelancer.com")
            logger.debug("To enable Freelancer.com, set FREELANCER_OAUTH_TOKEN in config")
            return []
        
        try:
            # Use production or sandbox based on config
            use_sandbox = getattr(settings, 'FREELANCER_SANDBOX', False)
            base_url = self.freelancer_sandbox_url if use_sandbox else self.freelancer_base_url
            
            # Freelancer.com Projects API endpoint (try different formats)
            url = f"{base_url}/projects/0.1/projects/active/"
            
            logger.info(f"Freelancer.com API: Searching with {len(keywords)} keywords, limit={limit}")
            logger.info(f"Freelancer.com API URL: {url}")
            logger.info(f"Freelancer.com API base URL: {base_url}")
            logger.info(f"Freelancer.com OAuth token present: {bool(oauth_token)}")
            logger.info(f"Freelancer.com OAuth token length: {len(oauth_token) if oauth_token else 0}")
            
            headers = {
                'freelancer-oauth-v1': oauth_token,
                'Content-Type': 'application/json',
                'User-Agent': 'TrustBridge/1.0',
                'Accept': 'application/json'
            }
            
            # Build query params - try simpler format first
            query_string = ' '.join(keywords[:3]) if keywords else 'software'
            params = {
                'query': query_string,
                'limit': min(limit, 50),  # Max 50 per API docs
                'compact': 'true',
                'full_description': 'false',
            }
            
            # Build full URL for logging
            full_url = f"{url}?query={query_string}&limit={params['limit']}"
            logger.info(f"Freelancer.com API full URL: {full_url}")
            logger.info(f"Freelancer.com API params: {params}")
            logger.info(f"Freelancer.com API headers (token masked): {dict((k, v[:20] + '...' if k == 'freelancer-oauth-v1' and len(v) > 20 else v) for k, v in headers.items())}")
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            logger.info(f"Freelancer.com API response status: {response.status_code}")
            logger.info(f"Freelancer.com API response headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                logger.error("Freelancer OAuth token expired or invalid - check FREELANCER_OAUTH_TOKEN")
                logger.error(f"Freelancer.com API full response: {response.text}")
                return []
            
            if response.status_code != 200:
                logger.warning(f"Freelancer.com API returned status {response.status_code}")
                logger.warning(f"Freelancer.com API response body: {response.text[:500]}")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Freelancer.com API response keys: {list(data.keys())}")
            logger.info(f"Freelancer.com API response data sample: {str(data)[:500]}")
            
            # Parse Freelancer projects - handle different response formats
            projects = []
            if 'result' in data:
                result_data = data.get('result', {})
                logger.info(f"Freelancer.com API result keys: {list(result_data.keys())}")
                projects = result_data.get('projects', [])
            elif 'projects' in data:
                projects = data.get('projects', [])
            elif isinstance(data, list):
                projects = data
            else:
                logger.warning(f"Freelancer.com API: Unexpected response structure: {type(data)}")
                logger.warning(f"Freelancer.com API response structure: {str(data)[:500]}")
            
            logger.info(f"Freelancer.com API: Found {len(projects)} raw projects")
            
            formatted_projects = []
            for project in projects:
                if not isinstance(project, dict):
                    continue
                    
                # Extract project data with safe defaults
                budget = project.get('budget', {}) or {}
                owner = project.get('owner', {}) or {}
                currency_info = project.get('currency', {}) or {}
                
                budget_min = budget.get('minimum', 0) if isinstance(budget, dict) else 0
                budget_max = budget.get('maximum', 0) if isinstance(budget, dict) else 0
                currency = currency_info.get('code', 'USD') if isinstance(currency_info, dict) else 'USD'
                
                # Extract skills/jobs
                jobs = project.get('jobs', [])
                skills = []
                if isinstance(jobs, list):
                    skills = [j.get('name', '') if isinstance(j, dict) else str(j) for j in jobs[:5]]
                
                formatted_project = {
                    'title': project.get('title', 'Untitled Project'),
                    'company': owner.get('username', 'Freelancer Client') if isinstance(owner, dict) else 'Freelancer Client',
                    'location': 'Remote (Freelancer.com)',
                    'description': self._clean_html(project.get('preview_description', project.get('description', '')))[:500],
                    'applyUrl': f"https://www.freelancer.com/projects/{project.get('seo_url', project.get('id', ''))}",
                    'source': 'Freelancer.com',
                    'type': 'Freelance Project',
                    'posted_date': project.get('submitdate', ''),
                    'skills': skills,
                    'salary': f"{currency} {budget_min}-{budget_max}" if budget_min or budget_max else "Negotiable",
                    'budget': {'min': budget_min, 'max': budget_max, 'currency': currency},
                    'bid_count': project.get('bid_stats', {}).get('bid_count', 0) if isinstance(project.get('bid_stats'), dict) else 0,
                }
                formatted_projects.append(formatted_project)
            
            logger.info(f"Freelancer.com API: Returning {len(formatted_projects)} formatted projects")
            return formatted_projects
            
        except requests.exceptions.Timeout:
            logger.error("Freelancer.com API request timed out after 15 seconds")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Freelancer.com request error: {str(e)}")
            logger.debug(f"Request details: URL={url}, Headers={headers.get('freelancer-oauth-v1', 'NOT SET')[:20]}...")
            return []
        except KeyError as e:
            logger.error(f"Freelancer.com API response structure error - missing key: {str(e)}")
            logger.debug(f"Response data: {str(data)[:500] if 'data' in locals() else 'No data'}")
            return []
        except Exception as e:
            logger.error(f"Freelancer.com search error: {str(e)}", exc_info=True)
            return []
    
    def _search_adzuna(self, keywords: List[str], location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Adzuna API for global jobs.
        Requires ADZUNA_APP_ID and ADZUNA_API_KEY in environment.
        Falls back gracefully if not configured.
        """
        # Get config values - handle both direct access and getattr
        try:
            app_id = settings.ADZUNA_APP_ID if hasattr(settings, 'ADZUNA_APP_ID') else getattr(settings, 'ADZUNA_APP_ID', None)
        except:
            app_id = getattr(settings, 'ADZUNA_APP_ID', None)
        
        try:
            api_key = settings.ADZUNA_API_KEY if hasattr(settings, 'ADZUNA_API_KEY') else getattr(settings, 'ADZUNA_API_KEY', None)
        except:
            api_key = getattr(settings, 'ADZUNA_API_KEY', None)
        
        # Strip whitespace and check if empty string
        if app_id:
            app_id = str(app_id).strip()
        if api_key:
            api_key = str(api_key).strip()
        
        if not app_id or not api_key or app_id == '' or api_key == '':
            logger.warning("No Adzuna API credentials configured - skipping Adzuna")
            logger.warning(f"ADZUNA_APP_ID: '{app_id}', ADZUNA_API_KEY: {'SET' if api_key else 'NOT SET'}")
            logger.warning("To enable Adzuna, set ADZUNA_APP_ID and ADZUNA_API_KEY in config")
            return []
        
        logger.info(f"Adzuna API configured - App ID: {app_id[:5]}..., API Key: {'SET' if api_key else 'NOT SET'}")
        
        logger.info(f"Adzuna API configured - App ID: {app_id[:5]}..., API Key: {'SET' if api_key else 'NOT SET'}")
        
        try:
            # Try multiple countries for better results
            # Adzuna supports: gb (UK), us (USA), au (Australia), ca (Canada), de (Germany), nl (Netherlands), sg (Singapore), etc.
            # Sierra Leone is NOT supported, so we search supported countries for remote jobs
            # Focus on countries with strong remote job markets
            countries = ['gb', 'us', 'au', 'ca', 'de', 'nl', 'sg']  # UK, US, Australia, Canada, Germany, Netherlands, Singapore
            
            all_formatted_jobs = []
            
            for country in countries:
                try:
                    url = f"{self.adzuna_base_url}/{country}/search/1"
                    
                    # Adzuna works best with 1-2 word queries, especially for remote jobs
                    # Keywords should already be simplified by get_platform_keywords
                    if keywords:
                        # Use first keyword only (should already be simplified, e.g., "developer python")
                        query_string = keywords[0] if keywords else 'developer'
                    else:
                        query_string = 'developer'
                    
                    params = {
                        'app_id': app_id,
                        'app_key': api_key,
                        'results_per_page': min(limit, 50),  # Adzuna max is 50
                        'what': query_string,
                    }
                    
                    # Don't add location filter for Adzuna - search for remote jobs globally
                    # Adzuna doesn't support Sierra Leone, so we search supported countries for remote work
                    # This allows users in Sierra Leone to find remote jobs from other countries
                    # if location and country == countries[0]:
                    #     params['where'] = location
                    
                    headers = {
                        'User-Agent': 'TrustBridge Job Aggregator (https://trustbridge.sl)',
                        'Accept': 'application/json'
                    }
                    
                    # Build full URL for logging
                    full_url = f"{url}?app_id={app_id}&app_key={api_key[:8]}...&what={query_string}&results_per_page={params['results_per_page']}"
                    
                    logger.info(f"Adzuna API ({country}): Searching with keywords: {query_string}")
                    logger.info(f"Adzuna API URL: {full_url}")
                    logger.info(f"Adzuna API params: app_id={app_id}, app_key={api_key[:8]}..., results_per_page={params['results_per_page']}, what={query_string}")
                    
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    
                    logger.info(f"Adzuna API ({country}) response status: {response.status_code}")
                    logger.info(f"Adzuna API ({country}) response headers: {dict(response.headers)}")
                    
                    if response.status_code == 401:
                        logger.error(f"Adzuna API ({country}): Invalid credentials - check ADZUNA_APP_ID and ADZUNA_API_KEY")
                        logger.error(f"Adzuna API ({country}) full response: {response.text}")
                        continue  # Try next country
                    
                    if response.status_code == 403:
                        logger.warning(f"Adzuna API ({country}): Access forbidden - may have hit rate limit or invalid credentials")
                        logger.warning(f"Adzuna API ({country}) full response: {response.text}")
                        continue
                    
                    if response.status_code != 200:
                        logger.warning(f"Adzuna API ({country}) returned status {response.status_code}")
                        logger.warning(f"Adzuna API ({country}) response body: {response.text[:500]}")
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    logger.info(f"Adzuna API ({country}) response keys: {list(data.keys())}")
                    logger.info(f"Adzuna API ({country}) response data sample: {str(data)[:500]}")
                    
                    jobs = data.get('results', [])
                    logger.info(f"Adzuna API ({country}): Found {len(jobs)} jobs in response")
                    
                    if jobs:
                        logger.info(f"Adzuna API ({country}): First job sample: {str(jobs[0])[:200]}")
                    
                    if not jobs:
                        logger.debug(f"Adzuna API ({country}): No jobs found for query '{query_string}'")
                        continue
                    
                    for job in jobs:
                        if not isinstance(job, dict):
                            continue
                            
                        # Extract job data with safe defaults
                        company_data = job.get('company', {}) or {}
                        location_data = job.get('location', {}) or {}
                        
                        company_name = company_data.get('display_name', 'Unknown') if isinstance(company_data, dict) else str(company_data) if company_data else 'Unknown'
                        job_location = location_data.get('display_name', 'Unknown') if isinstance(location_data, dict) else str(location_data) if location_data else 'Unknown'
                        
                        formatted_job = {
                            'title': job.get('title', 'Untitled Job'),
                            'company': company_name,
                            'location': job_location,
                            'description': self._clean_html(job.get('description', ''))[:500],
                            'applyUrl': job.get('redirect_url', job.get('url', '')),
                            'source': 'Adzuna',
                            'type': 'Remote' if 'remote' in job_location.lower() or 'remote' in str(job).lower() else 'Job',
                            'posted_date': job.get('created', job.get('created_at', '')),
                            'skills': [],  # Adzuna doesn't provide skills in basic response
                            'salary': self._format_adzuna_salary(job),
                        }
                        all_formatted_jobs.append(formatted_job)
                        
                        # Stop if we have enough jobs
                        if len(all_formatted_jobs) >= limit:
                            break
                    
                    # Stop searching other countries if we have enough results
                    if len(all_formatted_jobs) >= limit:
                        break
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Adzuna API ({country}) request timed out")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Adzuna API ({country}) request error: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Adzuna API ({country}) error: {str(e)}")
                    continue
            
            logger.info(f"Adzuna API: Returning {len(all_formatted_jobs)} total jobs from {len(countries)} countries")
            return all_formatted_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Adzuna search error: {str(e)}", exc_info=True)
            return []
    
    def _search_rapidapi_yc(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search Y-Combinator jobs via RapidAPI."""
        if not self.rapidapi_key:
            logger.warning("RapidAPI key not configured - skipping Y-Combinator jobs")
            return []
        
        try:
            logger.info(f"Fetching Y-Combinator jobs from RapidAPI (host: {self.rapidapi_yc_host})")
            conn = http.client.HTTPSConnection(self.rapidapi_yc_host)
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': self.rapidapi_yc_host
            }
            
            conn.request("GET", "/active-jb-7d", headers=headers)
            res = conn.getresponse()
            status_code = res.status
            data = res.read()
            conn.close()
            
            if status_code != 200:
                logger.error(f"Y-Combinator API returned status {status_code}: {data.decode('utf-8')[:200]}")
                return []
            
            jobs_data = json.loads(data.decode("utf-8"))
            logger.info(f"Y-Combinator API response type: {type(jobs_data)}")
            if isinstance(jobs_data, dict):
                logger.info(f"Y-Combinator API response keys: {list(jobs_data.keys())}")
            elif isinstance(jobs_data, list):
                logger.info(f"Y-Combinator API response: list with {len(jobs_data)} items")
            
            # Normalize data structure - handle both list and dict responses
            if isinstance(jobs_data, dict):
                # If API returns a dict, try to extract jobs array
                jobs_list = jobs_data.get('jobs', jobs_data.get('results', jobs_data.get('data', jobs_data.get('items', []))))
                if not isinstance(jobs_list, list):
                    # If it's still not a list, try to find any array in the dict
                    for key, value in jobs_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            jobs_list = value
                            break
                    if not isinstance(jobs_list, list):
                        jobs_list = [jobs_data] if jobs_data else []
            elif isinstance(jobs_data, list):
                jobs_list = jobs_data
            else:
                logger.warning(f"Y-Combinator API returned unexpected data type: {type(jobs_data)}")
                jobs_list = []
            
            logger.info(f"Y-Combinator: Extracted {len(jobs_list)} jobs from API response")
            
            # Filter and format jobs
            formatted_jobs = []
            keywords_lower = [k.lower() for k in keywords] if keywords else []
            
            for job in jobs_list:
                if not isinstance(job, dict):
                    continue
                
                # Extract job fields (API structure may vary)
                title = job.get('title') or job.get('position') or job.get('name') or job.get('job_title') or ''
                company = job.get('company') or job.get('company_name') or job.get('employer') or ''
                description = job.get('description') or job.get('summary') or job.get('details') or ''
                location = job.get('location') or job.get('city') or job.get('remote') or 'Remote'
                apply_url = job.get('url') or job.get('apply_url') or job.get('link') or job.get('application_url') or ''
                posted_date = job.get('date') or job.get('posted_date') or job.get('created_at') or ''
                salary = job.get('salary') or job.get('compensation') or ''
                
                # For Y-Combinator, be more lenient - include all jobs if keywords don't match well
                # YC jobs are high-quality startup jobs, so we want to show them even if keyword match is weak
                if keywords:
                    job_text = f"{title} {description} {company}".lower()
                    keyword_match = any(kw in job_text for kw in keywords_lower)
                    # If no match but we have few results, include anyway (YC jobs are valuable)
                    if not keyword_match and len(formatted_jobs) < limit // 2:
                        keyword_match = True  # Include to ensure we have some results
                else:
                    keyword_match = True  # If no keywords, include all
                
                if keyword_match:
                    formatted_job = {
                        'title': title,
                        'company': company or 'Y-Combinator Startup',
                        'location': location or 'Remote',
                        'description': self._clean_html(str(description))[:500] if description else '',
                        'applyUrl': apply_url,
                        'source': 'Y-Combinator',
                        'type': 'Startup Job',
                        'posted_date': str(posted_date),
                        'skills': job.get('tags', job.get('skills', [])),
                        'salary': str(salary) if salary else '',
                    }
                    formatted_jobs.append(formatted_job)
                
                if len(formatted_jobs) >= limit:
                    break
            
            logger.info(f"Y-Combinator: Formatted {len(formatted_jobs)} jobs (from {len(jobs_list)} extracted)")
            
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"Y-Combinator RapidAPI error: {str(e)}")
            return []
    
    def _search_rapidapi_internships(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search internships via RapidAPI."""
        if not self.rapidapi_key:
            logger.warning("RapidAPI key not configured - skipping Internships")
            return []
        
        try:
            logger.info(f"Fetching Internships from RapidAPI (host: {self.rapidapi_internships_host})")
            conn = http.client.HTTPSConnection(self.rapidapi_internships_host)
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': self.rapidapi_internships_host
            }
            
            conn.request("GET", "/active-jb-7d", headers=headers)
            res = conn.getresponse()
            status_code = res.status
            data = res.read()
            conn.close()
            
            if status_code != 200:
                logger.error(f"Internships API returned status {status_code}: {data.decode('utf-8')[:200]}")
                return []
            
            jobs_data = json.loads(data.decode("utf-8"))
            logger.info(f"Internships API response type: {type(jobs_data)}")
            if isinstance(jobs_data, dict):
                logger.info(f"Internships API response keys: {list(jobs_data.keys())}")
            elif isinstance(jobs_data, list):
                logger.info(f"Internships API response: list with {len(jobs_data)} items")
            
            # Normalize data structure - handle both list and dict responses
            if isinstance(jobs_data, dict):
                # If API returns a dict, try to extract jobs array
                jobs_list = jobs_data.get('internships', jobs_data.get('jobs', jobs_data.get('results', jobs_data.get('data', jobs_data.get('items', [])))))
                if not isinstance(jobs_list, list):
                    # If it's still not a list, try to find any array in the dict
                    for key, value in jobs_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            jobs_list = value
                            break
                    if not isinstance(jobs_list, list):
                        jobs_list = [jobs_data] if jobs_data else []
            elif isinstance(jobs_data, list):
                jobs_list = jobs_data
            else:
                logger.warning(f"Internships API returned unexpected data type: {type(jobs_data)}")
                jobs_list = []
            
            logger.info(f"Internships: Extracted {len(jobs_list)} jobs from API response")
            
            # Filter and format jobs
            formatted_jobs = []
            keywords_lower = [k.lower() for k in keywords] if keywords else []
            
            for job in jobs_list:
                if not isinstance(job, dict):
                    continue
                
                # Extract job fields (API structure may vary)
                title = job.get('title') or job.get('position') or job.get('name') or job.get('job_title') or ''
                company = job.get('company') or job.get('company_name') or job.get('employer') or ''
                description = job.get('description') or job.get('summary') or job.get('details') or ''
                location = job.get('location') or job.get('city') or job.get('remote') or 'Remote'
                apply_url = job.get('url') or job.get('apply_url') or job.get('link') or job.get('application_url') or ''
                posted_date = job.get('date') or job.get('posted_date') or job.get('created_at') or ''
                salary = job.get('salary') or job.get('stipend') or job.get('compensation') or ''
                
                # For Internships, be more lenient - include all jobs if keywords don't match well
                # Internships are valuable opportunities, so we want to show them even if keyword match is weak
                if keywords:
                    job_text = f"{title} {description} {company}".lower()
                    keyword_match = any(kw in job_text for kw in keywords_lower)
                    # If no match but we have few results, include anyway (internships are valuable)
                    if not keyword_match and len(formatted_jobs) < limit // 2:
                        keyword_match = True  # Include to ensure we have some results
                else:
                    keyword_match = True  # If no keywords, include all
                
                if keyword_match:
                    formatted_job = {
                        'title': title,
                        'company': company or 'Various Companies',
                        'location': location or 'Remote',
                        'description': self._clean_html(str(description))[:500] if description else '',
                        'applyUrl': apply_url,
                        'source': 'Internships API',
                        'type': 'Internship',
                        'posted_date': str(posted_date),
                        'skills': job.get('tags', job.get('skills', [])),
                        'salary': str(salary) if salary else '',
                    }
                    formatted_jobs.append(formatted_job)
                
                if len(formatted_jobs) >= limit:
                    break
            
            logger.info(f"Internships: Formatted {len(formatted_jobs)} jobs (from {len(jobs_list)} extracted)")
            
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"Internships RapidAPI error: {str(e)}")
            return []
    
    def _score_jobs_by_relevance(
        self,
        jobs: List[Dict[str, Any]],
        cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score jobs by relevance to CV (STAGE 2: Relevance Scoring).
        Only called after domain filtering passes.
        
        Scoring factors:
        - Skills match: 40%
        - Job title match: 30%
        - Experience match: 20%
        - Description keyword overlap: 10%
        
        NEW: Also calculates job-specific ATS score for each job.
        """
        cv_skills = self._extract_cv_skills(cv_data)
        cv_experience = self._extract_cv_experience(cv_data)
        cv_job_titles = [exp.get("job_title", "").lower() for exp in cv_experience if exp.get("job_title")]
        
        # Get generic ATS score first (for job-specific calculation)
        from cv.ats_engine import ATSEngine
        from app.services.pdf_parser_service import PDFParserService
        
        ats_engine = ATSEngine()
        pdf_parser = PDFParserService()
        normalized_cv = pdf_parser.validate_cv_data(cv_data)
        
        # Calculate generic ATS score once (reused for all jobs)
        generic_ats_result = ats_engine.calculate_ats_score(normalized_cv, force_recompute=False)
        generic_ats_score = generic_ats_result.get("ats_score", 0)
        
        scored_jobs = []
        for job in jobs:
            score = 0.0
            
            # Skills match (40%)
            job_skills = [s.lower() if isinstance(s, str) else str(s).lower() for s in job.get("skills", [])]
            if job_skills:
                matches = sum(1 for skill in job_skills if any(cv_skill in skill or skill in cv_skill for cv_skill in cv_skills))
                score += (matches / len(job_skills)) * 0.4
            
            # Job title match (30%)
            job_title = job.get("title", "").lower()
            if cv_job_titles:
                title_match = any(cv_title in job_title or job_title in cv_title for cv_title in cv_job_titles)
                if title_match:
                    score += 0.3
            
            # Experience match (20%)
            # Check if job description mentions experience levels that match CV
            job_desc = job.get("description", "").lower()
            if cv_experience:
                # Simple heuristic: if job mentions "years" and CV has experience
                if "year" in job_desc and len(cv_experience) > 0:
                    score += 0.2
            
            # Description keyword overlap (10%)
            job_text = f"{job_title} {job_desc}".lower()
            cv_text = " ".join(cv_skills).lower()
            job_words = set(job_text.split())
            cv_words = set(cv_text.split())
            overlap = len(job_words.intersection(cv_words))
            if len(job_words) > 0:
                score += min(0.1, (overlap / len(job_words)) * 0.1)
            
            job["match_score"] = min(1.0, score)
            job["relevance_reason"] = self._generate_relevance_reason(job, cv_skills, cv_job_titles)
            
            # NEW: Calculate job-specific ATS score
            try:
                # Extract job description - try multiple fields
                job_desc = job.get("description", "") or job.get("summary", "") or job.get("job_description", "") or ""
                # Get full description if available (not truncated)
                if job.get("full_description"):
                    job_desc = job.get("full_description")
                
                # Extract job skills - try multiple fields
                job_skills_list = job.get("skills", []) or job.get("job_skills", []) or job.get("tags", []) or []
                # Ensure it's a list
                if isinstance(job_skills_list, str):
                    job_skills_list = [job_skills_list]
                elif not isinstance(job_skills_list, list):
                    job_skills_list = []
                
                job_context = {
                    "job_title": job.get("title", "") or job.get("job_title", ""),
                    "job_description": job_desc,
                    "job_skills": job_skills_list
                }
                
                # Log job context for debugging (only first job to avoid spam)
                if len(scored_jobs) == 0:
                    logger.info(f"[JOB ATS DEBUG] First job context - Title: '{job_context['job_title'][:50]}', "
                               f"Description length: {len(job_desc)}, Skills: {len(job_skills_list)}")
                
                # Only calculate job-specific ATS if we have meaningful job context
                if job_context["job_title"] or len(job_desc) > 50 or len(job_skills_list) > 0:
                    # Calculate job-specific ATS score
                    job_ats_result = ats_engine.calculate_ats_score(
                        normalized_cv,
                        stored_hash=generic_ats_result.get("cv_hash"),
                        force_recompute=False,
                        job_context=job_context
                    )
                else:
                    # Skip job-specific calculation if no meaningful context
                    logger.debug(f"[JOB ATS] Skipping job-specific ATS for job '{job.get('title', 'Unknown')}' - insufficient job context")
                    job_ats_result = None
                
                # Add job-specific ATS data to job
                if job_ats_result and job_ats_result.get("job_specific_score") is not None:
                    job["ats_score"] = job_ats_result.get("job_specific_score")
                    job["ats_grade"] = job_ats_result.get("ats_grade", "D")
                    job["ats_relevance"] = job_ats_result.get("job_relevance_factor", 0)
                    job["ats_keyword_overlap"] = job_ats_result.get("keyword_overlap", 0)
                    job["ats_keyword_overlap_percentage"] = job_ats_result.get("keyword_overlap_percentage", 0)
                    job["ats_missing_skills"] = job_ats_result.get("missing_skills", [])
                    job["ats_matched_keywords"] = job_ats_result.get("matched_job_keywords", [])
                else:
                    # Fallback to generic ATS score if job-specific not available
                    job["ats_score"] = generic_ats_score
                    job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                    job["ats_relevance"] = None
            except Exception as e:
                logger.warning(f"Failed to calculate job-specific ATS score for job '{job.get('title', 'Unknown')}': {str(e)}")
                # Fallback to generic ATS score
                job["ats_score"] = generic_ats_score
                job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                job["ats_relevance"] = None
            
            scored_jobs.append(job)
        
        return scored_jobs
    
    def _extract_cv_skills(self, cv_data: Dict[str, Any]) -> List[str]:
        """Extract skills from CV data."""
        skills = []
        skills_data = cv_data.get("skills", {})
        if isinstance(skills_data, dict):
            skills.extend(skills_data.get("job_related_skills", []))
            skills.extend(skills_data.get("technical_skills", []))
            skills.extend(skills_data.get("technical", []))
        elif isinstance(skills_data, list):
            skills = [s.get("name", s) if isinstance(s, dict) else s for s in skills_data]
        return [str(s).lower() for s in skills if s]
    
    def _extract_cv_experience(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract experience from CV data."""
        experience = cv_data.get("experience", []) or cv_data.get("work_experience", [])
        if not isinstance(experience, list):
            return []
        return [exp for exp in experience if isinstance(exp, dict)]
    
    def _generate_relevance_reason(
        self,
        job: Dict[str, Any],
        cv_skills: List[str],
        cv_job_titles: List[str]
    ) -> str:
        """Generate human-readable reason for job match."""
        reasons = []
        
        job_skills = [s.lower() if isinstance(s, str) else str(s).lower() for s in job.get("skills", [])]
        matching_skills = [skill for skill in job_skills if any(cv_skill in skill or skill in cv_skill for cv_skill in cv_skills)]
        if matching_skills:
            reasons.append(f"Skills match: {', '.join(matching_skills[:3])}")
        
        job_title = job.get("title", "").lower()
        if any(cv_title in job_title or job_title in cv_title for cv_title in cv_job_titles):
            reasons.append("Job title aligns with experience")
        
        if not reasons:
            reasons.append("Domain-matched job")
        
        return "; ".join(reasons)
    
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