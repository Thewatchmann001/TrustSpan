"""
Domain Extraction Module
Extracts primary domain(s) from CV to enable domain-first job matching.

This ensures Business Administration CVs don't match Software Engineering jobs,
and vice versa.
"""
from typing import List, Dict, Any, Set, Optional
from app.utils.logger import logger


class DomainExtractor:
    """Extracts domain/industry from CV data."""
    
    # Domain mappings: domain -> keywords/indicators
    DOMAIN_KEYWORDS = {
        "business": {
            "education": ["business", "administration", "management", "commerce", "economics", "finance", "accounting", "marketing", "mba", "bba"],
            "roles": ["manager", "administrator", "officer", "coordinator", "analyst", "consultant", "executive", "director", "supervisor", "assistant"],
            "skills": ["management", "leadership", "strategy", "planning", "budget", "finance", "accounting", "marketing", "sales", "hr", "operations"],
            "exclude": ["software", "developer", "engineer", "programming", "coding", "technical", "backend", "frontend", "devops", "machine learning", "ai", "artificial intelligence", "data scientist", "data engineer", "ml engineer", "sre", "site reliability", "python", "javascript", "react", "node", "java", "programmer", "coder", "full stack", "fullstack"]
        },
        "technology": {
            "education": ["computer science", "software engineering", "information technology", "it", "cs", "engineering", "computer engineering", "computer engineer", "tech", "technology", "informatics", "computing"],
            "roles": ["developer", "engineer", "programmer", "architect", "devops", "sre", "scientist", "analyst", "specialist", "director of tech", "head of tech", "cto", "tech lead", "tech", "innovation", "technical"],
            "skills": ["programming", "coding", "software", "development", "python", "javascript", "java", "react", "node", "api", "database", "cloud", "blockchain", "ai", "ml", "machine learning", "artificial intelligence", "fullstack", "full-stack", "backend", "frontend", "git", "docker", "kubernetes", "aws", "azure", "sql", "postgresql", "mongodb", "flask", "django", "fastapi", "tensorflow", "web3"],
            "exclude": ["business administration", "accounting", "finance", "marketing", "hr"]
        },
        "accounting": {
            "education": ["accounting", "finance", "cpa", "acca", "accountancy"],
            "roles": ["accountant", "auditor", "bookkeeper", "financial analyst", "tax", "controller"],
            "skills": ["accounting", "bookkeeping", "audit", "tax", "financial", "gaap", "ifrs", "excel", "quickbooks"],
            "exclude": ["software", "developer", "programming", "engineering"]
        },
        "healthcare": {
            "education": ["medicine", "nursing", "pharmacy", "health", "medical", "public health"],
            "roles": ["doctor", "nurse", "physician", "pharmacist", "therapist", "medical", "healthcare"],
            "skills": ["medical", "healthcare", "patient", "clinical", "diagnosis", "treatment"],
            "exclude": ["software", "developer", "business", "accounting"]
        },
        "education": {
            "education": ["education", "teaching", "pedagogy", "curriculum"],
            "roles": ["teacher", "educator", "instructor", "professor", "lecturer", "tutor"],
            "skills": ["teaching", "curriculum", "pedagogy", "education", "training"],
            "exclude": ["software", "developer", "engineering"]
        },
        "engineering": {
            "education": ["engineering", "mechanical", "electrical", "civil", "chemical", "industrial"],
            "roles": ["engineer", "technician", "designer", "architect"],
            "skills": ["engineering", "design", "cad", "mechanical", "electrical", "civil"],
            "exclude": ["software developer", "programming", "coding", "business"]
        },
        "agriculture": {
            "education": ["agriculture", "agricultural", "agribusiness", "agronomy", "farming", "extension", "crop", "livestock", "agricultural science"],
            "roles": ["farmer", "agricultural officer", "extension officer", "agronomist", "agriculturalist", "farm manager", "agricultural consultant", "agricultural extension"],
            "skills": ["agriculture", "farming", "crop production", "livestock", "agribusiness", "extension", "agricultural", "farm management"],
            "exclude": ["software", "developer", "engineer", "programming", "coding", "ai", "machine learning", "artificial intelligence", "backend", "frontend", "devops", "data scientist", "python", "javascript", "react", "node", "java", "programmer", "coder", "full stack", "fullstack", "ml engineer"]
        },
        "arts": {
            "education": ["arts", "fine arts", "design", "art history", "creative", "music", "theatre", "drama"],
            "roles": ["artist", "designer", "creative", "illustrator", "graphic designer", "musician", "actor"],
            "skills": ["art", "design", "creative", "illustration", "graphic design", "music"],
            "exclude": ["software", "developer", "engineer", "programming", "coding", "backend", "frontend", "devops"]
        }
    }
    
    def extract_domains(self, cv_data: Dict[str, Any]) -> Set[str]:
        """
        Extract primary domain(s) from CV.
        
        Returns:
            Set of domain names (e.g., {"business", "accounting"})
        """
        if not cv_data:
            logger.warning("[DOMAIN EXTRACTION] Empty CV data provided to domain extractor")
            return set()
        
        logger.info("[DOMAIN EXTRACTION] Starting domain extraction from CV")
        logger.info(f"[DOMAIN EXTRACTION] CV data keys: {list(cv_data.keys())[:20] if isinstance(cv_data, dict) else 'NOT A DICT'}")
        
        domain_scores = {domain: 0 for domain in self.DOMAIN_KEYWORDS.keys()}
        
        # Extract from education
        education = cv_data.get("education", [])
        if not isinstance(education, list):
            education = []
        
        for edu in education:
            if not isinstance(edu, dict):
                continue
            
            degree_text = " ".join([
                str(edu.get("degree", "")),
                str(edu.get("field", "")),
                str(edu.get("field_of_study", "")),  # Also check field_of_study
                str(edu.get("institution", ""))
            ]).lower()
            
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                for keyword in keywords["education"]:
                    # For technology domain, be more strict with "it" and "cs" to avoid false positives
                    if domain == "technology" and keyword in ["it", "cs"]:
                        # Only match if it's a standalone word or part of a tech-related phrase
                        if keyword in degree_text and (
                            "computer" in degree_text or 
                            "information technology" in degree_text or
                            "software" in degree_text or
                            "engineering" in degree_text
                        ):
                            domain_scores[domain] += 3
                            logger.debug(f"Education match: '{keyword}' found in '{degree_text[:100]}' -> domain: {domain}")
                            break
                    elif keyword in degree_text:
                        domain_scores[domain] += 3  # Education is strong indicator
                        logger.debug(f"Education match: '{keyword}' found in '{degree_text[:100]}' -> domain: {domain}")
                        break
        
        # Extract from experience/job titles
        experience = cv_data.get("experience", []) or cv_data.get("work_experience", [])
        if not isinstance(experience, list):
            experience = []
        
        for exp in experience:
            if not isinstance(exp, dict):
                continue
            
            job_title = str(exp.get("job_title", "")).lower()
            company = str(exp.get("company", "")).lower()
            description = str(exp.get("description", "")).lower()
            
            job_text = f"{job_title} {company} {description}"
            
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                for keyword in keywords["roles"]:
                    # For technology domain, be stricter with generic keywords like "analyst", "specialist"
                    # They should only match if there are other tech indicators
                    if domain == "technology" and keyword in ["analyst", "specialist", "scientist"]:
                        # Only match if there are other tech-related terms in the same text
                        tech_context_words = ["data", "software", "system", "technical", "computer", "it", "tech", "programming", "developer", "engineer"]
                        if keyword in job_text and any(context in job_text for context in tech_context_words):
                            domain_scores[domain] += 2
                            logger.debug(f"Experience match: '{keyword}' found in '{job_text[:100]}' (with tech context) -> domain: {domain}")
                            break
                    elif keyword in job_text:
                        domain_scores[domain] += 2  # Job title is strong indicator
                        logger.debug(f"Experience match: '{keyword}' found in '{job_text[:100]}' -> domain: {domain}")
                        break
        
        # Extract from skills
        skills = self._extract_skills(cv_data)
        skills_text = " ".join(skills).lower()
        
        # CRITICAL FIX: Check if CV has strong non-tech domain indicators from education/experience
        # If yes, tech keywords in skills should require stronger evidence
        non_tech_domains = {"business", "agriculture", "accounting", "healthcare", "education", "arts"}
        tech_domain_score_from_edu_exp = 0
        non_tech_domain_max_score = 0
        
        # Calculate scores from education + experience only (before skills)
        for domain in non_tech_domains:
            if domain_scores[domain] > non_tech_domain_max_score:
                non_tech_domain_max_score = domain_scores[domain]
        tech_domain_score_from_edu_exp = domain_scores["technology"]
        
        # If non-tech domain score (from education/experience) is higher than tech score,
        # then tech skills keywords require STRONG tech context
        has_strong_non_tech_signal = non_tech_domain_max_score > tech_domain_score_from_edu_exp
        
        logger.info(f"[DOMAIN EXTRACTION] Domain scores (before skills): business={domain_scores.get('business', 0)}, "
                   f"technology={tech_domain_score_from_edu_exp}, non-tech_max={non_tech_domain_max_score}, "
                   f"has_strong_non_tech_signal={has_strong_non_tech_signal}")
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords["skills"]:
                # CRITICAL: For technology domain, require STRONG tech context if CV has non-tech education/experience
                if domain == "technology":
                    # Weak tech keywords (can appear in non-tech contexts)
                    weak_tech_keywords = ["ai", "ml", "machine learning", "artificial intelligence", "api", "database", "cloud", "development", "software"]
                    
                    if keyword in weak_tech_keywords:
                        # Require strong tech context (programming languages, frameworks)
                        strong_tech_skills = ["python", "javascript", "java", "react", "node", "typescript", "c++", "c#", "golang", "rust", "scala", 
                                            "programming", "coding", "developer", "engineer", "fullstack", "full-stack", "backend", "frontend",
                                            "django", "flask", "fastapi", "tensorflow", "pytorch", "docker", "kubernetes", "blockchain", "web3"]
                        
                        # Count how many strong tech skills are present
                        strong_tech_count = sum(1 for tech_skill in strong_tech_skills if tech_skill in skills_text)
                        
                        # If CV has strong non-tech signal, require at least 3 strong tech skills
                        # Otherwise, require at least 1 strong tech skill
                        required_tech_skills = 3 if has_strong_non_tech_signal else 1
                        
                        if keyword in skills_text and strong_tech_count >= required_tech_skills:
                            domain_scores[domain] += 1
                            logger.debug(f"Skills match: '{keyword}' found with {strong_tech_count} strong tech skills (requires {required_tech_skills}) -> domain: {domain}")
                            break
                        elif keyword in skills_text:
                            logger.debug(f"Skills REJECTED: '{keyword}' found but only {strong_tech_count} strong tech skills (requires {required_tech_skills}) - CV has non-tech domain signal")
                            break  # Don't count this keyword
                    else:
                        # Strong tech keywords (rarely appear in non-tech contexts) - always count
                        if keyword in skills_text:
                            domain_scores[domain] += 1
                            logger.debug(f"Skills match: '{keyword}' found (strong tech keyword) -> domain: {domain}")
                            break
                elif keyword in skills_text:
                    # Non-tech domains: count skills normally
                    domain_scores[domain] += 1
                    logger.debug(f"Skills match: '{keyword}' found -> domain: {domain}")
                    break
        
        # CRITICAL FIX: If CV has strong non-tech domain (score >= 3 from education/experience)
        # and technology domain score is ONLY from skills (not from education/experience),
        # then REJECT technology domain to prevent false positives
        tech_domain_final_score = domain_scores["technology"]
        
        # Log technology domain score check
        logger.info(f"[DOMAIN EXTRACTION] Technology domain score check: final={tech_domain_final_score}, "
                   f"from_edu_exp={tech_domain_score_from_edu_exp}, "
                   f"non_tech_max={non_tech_domain_max_score}, "
                   f"has_strong_non_tech={has_strong_non_tech_signal}")
        
        # STRICT RULE 1: If non-tech domain has strong signal (>= 3 from education/experience)
        # and tech domain score is <= 3 (weak signal, likely from skills only), REJECT tech domain
        # This ensures Business Admin CVs with score 4 don't get tech domain from score 3 (weak signals)
        if non_tech_domain_max_score >= 3 and tech_domain_final_score > 0 and tech_domain_final_score <= 3:
            logger.warning(f"[DOMAIN EXTRACTION] STRICT REJECTION: Technology domain score {tech_domain_final_score} <= 3 (weak signal), "
                          f"non-tech domain score {non_tech_domain_max_score} >= 3 (strong signal from education/experience) - REJECTING technology domain")
            domain_scores["technology"] = 0
            tech_domain_final_score = 0  # Update for next check
            logger.info(f"[DOMAIN EXTRACTION] Technology domain score after strict rejection: {domain_scores['technology']}")
        
        # STRICT RULE 2: If tech domain is ONLY from skills (0 from education/experience) and non-tech is strong, REJECT
        if has_strong_non_tech_signal and tech_domain_score_from_edu_exp == 0 and tech_domain_final_score > 0:
            # Technology domain exists but ONLY from skills, while non-tech domain has strong education/experience signal
            # This is likely a false positive (e.g., "AI" mentioned in business context)
            logger.warning(f"[DOMAIN EXTRACTION] REJECTING technology domain - score {tech_domain_final_score} from skills only, "
                          f"but non-tech domain has strong signal (score {non_tech_domain_max_score} from education/experience)")
            domain_scores["technology"] = 0  # Remove technology domain score
            logger.info(f"[DOMAIN EXTRACTION] Technology domain score after skills-only rejection: {domain_scores['technology']}")
        
        # Determine primary domains (score >= 2)
        primary_domains = {domain for domain, score in domain_scores.items() if score >= 2}
        
        # If no clear domain, use highest scoring one (but only if score > 0)
        if not primary_domains and domain_scores:
            max_score = max(domain_scores.values())
            if max_score > 0:
                primary_domains = {domain for domain, score in domain_scores.items() if score == max_score}
                logger.info(f"[DOMAIN EXTRACTION] No strong domain match (score >= 2), using highest scoring domain: {primary_domains} (score: {max_score})")
        
        # Enhanced logging for debugging
        if not primary_domains:
            logger.warning(f"[DOMAIN EXTRACTION] FAILED to extract domains from CV. Scores: {domain_scores}")
            logger.warning(f"[DOMAIN EXTRACTION] CV data keys: {list(cv_data.keys()) if isinstance(cv_data, dict) else 'NOT A DICT'}")
            logger.warning(f"[DOMAIN EXTRACTION] Education count: {len(cv_data.get('education', []))}")
            logger.warning(f"[DOMAIN EXTRACTION] Experience count: {len(cv_data.get('experience', []) or cv_data.get('work_experience', []))}")
            logger.warning(f"[DOMAIN EXTRACTION] Skills type: {type(cv_data.get('skills', {}))}")
            logger.warning(f"[DOMAIN EXTRACTION] Skills keys: {list(cv_data.get('skills', {}).keys())[:10] if isinstance(cv_data.get('skills', {}), dict) else 'NOT A DICT'}")
            
            # Log sample education/experience for debugging
            education_sample = cv_data.get('education', [])[:2] if cv_data.get('education') else []
            experience_sample = (cv_data.get('experience', []) or cv_data.get('work_experience', []))[:2] if (cv_data.get('experience') or cv_data.get('work_experience')) else []
            logger.warning(f"[DOMAIN EXTRACTION] Education sample: {education_sample}")
            logger.warning(f"[DOMAIN EXTRACTION] Experience sample: {experience_sample}")
        else:
            logger.info(f"[DOMAIN EXTRACTION] SUCCESS: Extracted domains from CV: {primary_domains} (scores: {domain_scores})")
            logger.info(f"[DOMAIN EXTRACTION] Top 3 domain scores: {sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return primary_domains
    
    def _extract_skills(self, cv_data: Dict[str, Any]) -> List[str]:
        """Extract skills from CV data - handles multiple formats."""
        skills = []
        
        skills_data = cv_data.get("skills", {})
        if isinstance(skills_data, dict):
            # Europass format
            skills.extend(skills_data.get("job_related_skills", []))
            skills.extend(skills_data.get("technical_skills", []))
            skills.extend(skills_data.get("technical", []))
            skills.extend(skills_data.get("soft", []))
            skills.extend(skills_data.get("languages", []))
            skills.extend(skills_data.get("computer_skills", []))
            # Also check for nested skill categories
            for key in skills_data.keys():
                if isinstance(skills_data[key], list):
                    skills.extend(skills_data[key])
        elif isinstance(skills_data, list):
            skills = [s.get("name", s) if isinstance(s, dict) else s for s in skills_data]
        
        # Also check for skills in other locations (PDF parsing may store differently)
        # Check for "Programming Languages", "Frameworks", "Tools", etc.
        for key in ["programming_languages", "frameworks", "tools", "platforms", "libraries"]:
            if key in cv_data and isinstance(cv_data[key], list):
                skills.extend(cv_data[key])
        
        # Extract skills from summary/about section (PDF parsing may put skills there)
        summary = cv_data.get("summary", "") or cv_data.get("about_me", "") or cv_data.get("about", "")
        if summary:
            # Look for common skill patterns in summary
            tech_terms = ["python", "javascript", "react", "node", "blockchain", "ai", "ml", "docker"]
            for term in tech_terms:
                if term.lower() in str(summary).lower():
                    skills.append(term)
        
        return [str(s).lower().strip() for s in skills if s]
    
    def get_domain_keywords(self, domain: str) -> Dict[str, List[str]]:
        """Get keywords for a specific domain."""
        return self.DOMAIN_KEYWORDS.get(domain, {})
    
    def is_domain_match(self, job: Dict[str, Any], cv_domains: Set[str]) -> bool:
        """
        HARD DOMAIN GATING: Check if a job matches the CV's domain(s).
        Returns False if domains don't match - NO FALLBACK.
        
        Args:
            job: Job dictionary with title, description, etc.
            cv_domains: Set of domains extracted from CV
        
        Returns:
            True if job matches at least one domain, False otherwise
            IMPORTANT: If cv_domains is empty, returns False (no fallback)
        """
        # HARD GATE: If no domains extracted, reject ALL jobs
        # This prevents fallback behavior that allows mismatched jobs
        if not cv_domains:
            logger.warning("No domains extracted from CV - REJECTING all jobs (hard gate)")
            return False
        
        job_text = " ".join([
            str(job.get("title", "")),
            str(job.get("description", "")),
            str(job.get("company", "")),
            " ".join(job.get("skills", []))
        ]).lower()
        
        # STRONG TECH KEYWORDS - indicators that this is definitely a tech job
        strong_tech_keywords = [
            "software engineer", "software developer", "programmer", "coder",
            "backend developer", "frontend developer", "full stack", "fullstack",
            "python developer", "javascript developer", "java developer",
            "react developer", "node.js developer", "web developer",
            "machine learning engineer", "ml engineer", "ai engineer",
            "devops engineer", "sre", "site reliability engineer",
            "data engineer", "data scientist", "ml engineer"
        ]
        
        # STRONG TECH KEYWORDS IN JOB TITLE/DESCRIPTION (single words that definitely indicate tech)
        strong_tech_indicators = [
            "software", "developer", "programmer", "coder", "engineer",
            "python", "javascript", "java", "react", "node.js", "backend", "frontend",
            "full stack", "fullstack", "machine learning", "ai", "ml", "devops",
            "sql", "database", "api", "rest", "graphql", "docker", "kubernetes"
        ]
        
        # Check if job is definitely a tech job (contains strong tech keywords)
        is_tech_job = any(tech_kw in job_text for tech_kw in strong_tech_keywords)
        # Also check if job title/description contains strong tech indicators
        job_title = str(job.get("title", "")).lower()
        has_tech_indicators = any(indicator in job_title or indicator in job_text for indicator in strong_tech_indicators[:15])  # Check first 15 to avoid false positives
        
        # If it's clearly a tech job, verify CV has STRONG technology domain evidence
        if is_tech_job or (has_tech_indicators and "developer" in job_title or "engineer" in job_title):
            # Check if CV has technology domain
            if "technology" in cv_domains:
                # CV has technology domain - allow it, but log for debugging
                logger.debug(f"Job '{job.get('title', '')}' matched - tech job and CV has technology domain")
                # Continue to positive match check
            else:
                # This is a tech job but CV doesn't have technology domain - REJECT
                logger.debug(f"Job '{job.get('title', '')}' REJECTED - tech job (keywords: {[kw for kw in strong_tech_keywords if kw in job_text][:2]}) but CV domains {cv_domains} don't include 'technology'")
                return False
        
        # HARD EXCLUSION: Check if job contains excluded keywords for any CV domain
        # This catches tech jobs for non-tech CVs (e.g., agriculture, business)
        # Apply exclusion if CV has non-tech domains and job contains strong tech indicators
        non_tech_domains = cv_domains - {"technology"}
        if non_tech_domains and has_tech_indicators:
            for domain in non_tech_domains:
                domain_keywords = self.DOMAIN_KEYWORDS.get(domain, {})
                exclude_keywords = domain_keywords.get("exclude", [])
                
                # Check if job contains any excluded tech keywords
                excluded_keywords_found = [excl for excl in strong_tech_indicators if excl in job_text]
                if excluded_keywords_found:
                    logger.debug(f"Job '{job.get('title', '')}' HARD EXCLUDED - contains tech keywords {excluded_keywords_found[:3]} but CV has non-tech domain '{domain}' which excludes tech jobs")
                    return False
        
        # POSITIVE MATCH: Check if job matches any CV domain
        for domain in cv_domains:
            domain_keywords = self.DOMAIN_KEYWORDS.get(domain, {})
            
            # Check roles and skills keywords
            for keyword_list in [domain_keywords.get("roles", []), domain_keywords.get("skills", [])]:
                for keyword in keyword_list:
                    if keyword in job_text:
                        # Job matches this domain - accept it
                        logger.debug(f"Job '{job.get('title', '')}' matched domain '{domain}' (keyword: '{keyword}')")
                        return True
        
        # No match found - REJECT job
        logger.debug(f"Job '{job.get('title', '')}' rejected - no domain match for {cv_domains}")
        return False
