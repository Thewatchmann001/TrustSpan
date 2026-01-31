"""
Deterministic ATS Scoring Engine

Production-grade ATS analyzer with:
- Explicit component scoring (30 components × individual weights)
- CV hashing for deterministic caching
- Tiered scoring thresholds (not linear averaging)
- Mandatory feedback fields for weak CVs
- Full transparency and explainability

Formula:
ATS_SCORE = Σ (ComponentScore × Weight)
  - Keyword & Skill Match: 30%
  - Experience Quality: 20%
  - Formatting & ATS Readability: 15%
  - Section Completeness: 10%
  - Achievement Quantification: 10%
  - Role Consistency: 10%
  - Red Flags Penalty: -5%
"""

import hashlib
import json
import re
from typing import Dict, List, Any, Tuple, Optional
from app.utils.logger import logger


class ATSEngine:
    """Deterministic ATS scoring engine with component-based formula."""

    # ATS-friendly keywords grouped by category
    ATS_FRIENDLY_KEYWORDS = {
        "technical": {
            "languages": ["python", "java", "javascript", "c++", "c", "typescript", "golang", "rust", "scala", "kotlin", "php", "swift", "matlab", "sql"],
            "frameworks": ["react", "angular", "vue", "django", "flask", "fastapi", "spring", "rails", "nodejs", "node.js", "express", "next.js", "nextjs", "web3.js", "web3", "sqlalchemy", "tensorflow", "pytorch"],
            "tools": ["git", "docker", "kubernetes", "jenkins", "terraform", "ansible", "jira", "confluence", "jupyter", "linux", "ubuntu", "gitlab", "github"],
            "cloud": ["aws", "azure", "gcp", "google cloud", "cloud", "devops", "render", "heroku", "vercel"],
            "data": ["sql", "nosql", "mongodb", "postgresql", "postgres", "sqlite", "mysql", "elasticsearch", "spark", "hadoop", "data", "pandas", "numpy", "matplotlib", "seaborn", "tableau", "power bi", "powerbi"],
            "ai_ml": ["machine learning", "ai", "artificial intelligence", "tensorflow", "pytorch", "scikit-learn", "scikit", "sklearn", "nlp", "deep learning", "openai", "gpt", "llm", "rag", "neural network"],
            "blockchain": ["solana", "blockchain", "smart contracts", "web3", "decentralized", "did", "cryptocurrency", "crypto", "ethereum", "defi"],
            "mobile": ["flutter", "react native", "ios", "android", "mobile", "swift", "kotlin"],
            "databases": ["postgresql", "postgres", "sqlite", "mysql", "mongodb", "redis", "database", "sql", "nosql", "pgvector"],
        },
        "action_verbs": [
            "developed", "designed", "implemented", "led", "managed", "optimized", "improved",
            "built", "created", "architected", "engineered", "accelerated", "scaled", "deployed",
            "reduced", "increased", "enhanced", "automated", "achieved", "delivered", "launched",
            "collaborated", "contributed", "mentored", "pioneered", "transformed",
            "supported", "assisted", "engaged", "promoted", "integrated", "processed",
            "generated", "established", "conducted", "coordinated", "facilitated",
            "executed", "initiated", "drove", "directed", "spearheaded", "modernized"
        ],
        "metrics_indicators": [
            "increased", "decreased", "reduced", "improved", "optimized", "accelerated",
            "%", "x", "multiplied", "saved", "earned", "gained", "captured", "exceeded"
        ]
    }

    # Red flags that negatively impact scoring
    RED_FLAGS = {
        "grammar_issues": ["teh ", "recieved", "occured", "seperate", "neccessary"],
        "formatting": ["inconsistent ", "misaligned", "poor spacing"],
        "suspicious": ["lorem ipsum", "pending", "to be added", "tba", "tbf"],
        "passive_voice": ["was responsible", "was involved in", "was part of"],
    }

    def __init__(self):
        pass

    def calculate_ats_score(
        self, 
        cv_data: Dict[str, Any], 
        stored_hash: Optional[str] = None, 
        force_recompute: bool = False,
        job_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate ATS score with component breakdown.
        
        NEW: Optional job_context parameter for job-specific scoring:
        - job_description: str - Job posting description
        - job_skills: List[str] - Required skills for the job
        - job_title: str - Job title
        
        If job_context is provided, returns job-specific relevance score.

        Returns deterministic score with:
        - ats_score (0-100) - Generic ATS score OR job-specific score if job_context provided
        - ats_grade (A+, A, B, C, D)
        - cv_hash (for caching)
        - component_scores (breakdown)
        - ats_issues (problems found)
        - ats_recommendations (areas to improve)
        - analysis_details (full transparency)
        - job_specific_score (if job_context provided) - Relevance score for this specific job
        - keyword_overlap (if job_context provided) - How many job keywords match CV
        - missing_skills (if job_context provided) - Required skills missing from CV
        """
        logger.info("ATSEngine: Starting ATS analysis")
        
        # DEBUG: Log CV data structure to diagnose issues
        logger.info(f"ATSEngine: CV data keys: {list(cv_data.keys()) if isinstance(cv_data, dict) else 'NOT A DICT'}")
        logger.info(f"ATSEngine: CV data has experience: {bool(cv_data.get('experience') or cv_data.get('work_experience'))}")
        logger.info(f"ATSEngine: CV data has skills: {bool(cv_data.get('skills') or cv_data.get('personal_skills'))}")
        logger.info(f"ATSEngine: CV data has summary: {bool(cv_data.get('summary') or cv_data.get('professional_summary'))}")

        # Generate CV hash
        cv_hash = self._generate_cv_hash(cv_data)
        logger.info(f"ATSEngine: CV hash = {cv_hash[:16]}...")

        # FIX 3: Respect cached scores when hash matches (unless force_recompute OR job_context provided)
        # CRITICAL: If job_context is provided, we MUST calculate job-specific scores (even if CV hash matches)
        # Job-specific scores depend on job context, not just CV content
        if not force_recompute and stored_hash and stored_hash == cv_hash and not job_context:
            # Only return cached score if NO job_context (generic ATS only)
            logger.info(f"ATSEngine: CV hash matches stored hash (reusing cached score). Set force_recompute=True to recalculate.")
            return {
                "reused_from_cache": True,
                "cv_hash": cv_hash,
                "ats_score": None,  # Caller should use stored value
                "ats_grade": None,  # Caller should use stored value
                "component_scores": {},
                "ats_issues": [],
                "ats_recommendations": [],
                "message": "CV content unchanged - use stored ATS score"
            }

        # Extract normalized text for analysis
        normalized_text = self._normalize_cv_text(cv_data)
        logger.info(f"ATSEngine: Normalized text length: {len(normalized_text)} chars")
        if len(normalized_text) < 50:
            logger.warning(f"ATSEngine: Normalized text is very short ({len(normalized_text)} chars) - CV data may be incomplete!")
            logger.warning(f"ATSEngine: Normalized text preview: {normalized_text[:200]}")

        # ========== COMPONENT SCORING ==========
        components = {}

        # 1. Keyword & Skill Match (30%)
        components["keyword_match"] = self._score_keyword_match(cv_data, normalized_text)

        # 2. Experience Quality (20%)
        components["experience_quality"] = self._score_experience_quality(cv_data, normalized_text)

        # 3. Formatting & ATS Readability (15%)
        components["formatting"] = self._score_formatting(cv_data, normalized_text)

        # 4. Section Completeness (10%)
        components["completeness"] = self._score_completeness(cv_data)

        # 5. Achievement Quantification (10%)
        components["quantification"] = self._score_quantification(normalized_text)

        # 6. Role Consistency (10%)
        components["role_consistency"] = self._score_role_consistency(cv_data)

        # 7. Red Flags (−5%)
        components["red_flags_penalty"] = self._score_red_flags(normalized_text)

        # ========== CALCULATE FINAL SCORE ==========
        weights = {
            "keyword_match": 0.30,
            "experience_quality": 0.20,
            "formatting": 0.15,
            "completeness": 0.10,
            "quantification": 0.10,
            "role_consistency": 0.10,
            # Note: red_flags_penalty handled separately below (not weighted)
        }

        # Calculate base score from weighted components
        ats_score = sum(components[key]["score"] * weights[key] for key in weights if key != "red_flags_penalty")
        
        # FIX 4: Subtract red flags penalty (max 5 points)
        red_flags_penalty = components.get("red_flags_penalty", {}).get("penalty", 0)
        ats_score -= red_flags_penalty
        
        ats_score = max(0, min(100, int(ats_score)))  # Clamp to 0-100

        # Assign grade
        ats_grade = self._score_to_grade(ats_score)

        # Build component scores for logging (handle red_flags_penalty specially)
        component_scores_log = {}
        for k in components:
            if k == "red_flags_penalty":
                component_scores_log[k] = components[k].get("penalty", 0)
            else:
                component_scores_log[k] = components[k].get("score", 0)

        logger.info(f"ATSEngine: Final score = {ats_score}/100 (Grade: {ats_grade})")
        logger.info(f"ATSEngine: Component scores = {component_scores_log}")

        # ========== GENERATE ISSUES & RECOMMENDATIONS ==========
        issues, recommendations = self._generate_feedback(cv_data, normalized_text, components, ats_score)

        # ========== VALIDATE MANDATORY FIELDS ==========
        if ats_score < 90:
            if not issues or len(issues) == 0:
                logger.warning(f"ATSEngine: Score {ats_score} < 90 but no issues found. Adding defaults.")
                issues = [{"category": "content", "severity": "warning", "message": "CV could benefit from more specific achievements and metrics"}]
            if not recommendations or len(recommendations) == 0:
                logger.warning(f"ATSEngine: Score {ats_score} < 90 but no recommendations found. Adding defaults.")
                recommendations = [
                    "Quantify achievements with measurable results (e.g., '30% faster', '5M+ users')",
                    "Expand technical skills with industry-standard technologies",
                    "Ensure consistent formatting and section organization"
                ]

        # ========== JOB-SPECIFIC SCORING (if job_context provided) ==========
        job_specific_data = None
        if job_context:
            job_specific_data = self._calculate_job_specific_score(cv_data, normalized_text, job_context, ats_score)
            logger.info(f"[JOB-SPECIFIC ATS] Job: {job_context.get('job_title', 'Unknown')}, "
                       f"Generic Score: {ats_score}, Job-Specific Score: {job_specific_data.get('job_specific_score', 'N/A')}, "
                       f"Relevance: {job_specific_data.get('relevance_factor', 0):.2%}")
        
        # FIX 5: Include ATS context for persistence
        ats_context = {
            "ats_version": "1.0.0",  # Version of ATS engine used
            "cv_hash": cv_hash,
            "job_keywords_used": components.get("keyword_match", {}).get("matched_keywords", [])[:10],  # Top 10 keywords
            "calculation_timestamp": None,  # Will be set by caller if needed
        }
        
        # Build component_scores dict (handle red_flags_penalty specially)
        component_scores_dict = {}
        for k in components:
            if k == "red_flags_penalty":
                component_scores_dict[k] = components[k].get("penalty", 0)
            else:
                component_scores_dict[k] = components[k]["score"]
        
        result = {
            "ats_score": ats_score,
            "ats_grade": ats_grade,
            "cv_hash": cv_hash,
            "component_scores": component_scores_dict,
            "component_details": components,
            "ats_issues": issues,
            "ats_recommendations": recommendations,
            "analysis_details": {
                "keyword_density": components["keyword_match"].get("keyword_count", 0),
                "formatting_score": components["formatting"]["score"],
                "section_completeness": {sec: components["completeness"].get(f"{sec}_present", False) for sec in ["experience", "education", "skills"]},
            },
            "ats_context": ats_context,  # FIX 5: For persistence
            "reused_from_cache": False,
        }
        
        # Add job-specific data if job_context was provided
        if job_specific_data:
            result.update({
                "job_specific_score": job_specific_data["job_specific_score"],
                "job_relevance_factor": job_specific_data["relevance_factor"],
                "keyword_overlap": job_specific_data["keyword_overlap"],
                "keyword_overlap_percentage": job_specific_data["keyword_overlap_percentage"],
                "missing_skills": job_specific_data["missing_skills"],
                "matched_job_keywords": job_specific_data["matched_job_keywords"],
            })
            # Use job-specific score as primary score if provided
            result["ats_score"] = job_specific_data["job_specific_score"]
            result["ats_grade"] = self._score_to_grade(job_specific_data["job_specific_score"])
        
        return result

    def _generate_cv_hash(self, cv_data: Dict[str, Any]) -> str:
        """
        Generate deterministic hash of canonical CV content only.
        
        FIX 1: Only hash stable CV fields, exclude dynamic ATS metadata.
        This ensures same CV content → same hash → same score.
        """
        canonical_cv = self._normalize_cv_for_hash(cv_data)
        # Sort keys for deterministic JSON
        normalized_json = json.dumps(canonical_cv, sort_keys=True, default=str)
        return hashlib.sha256(normalized_json.encode()).hexdigest()
    
    def _normalize_cv_for_hash(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract only canonical CV content for hashing.
        
        Excludes:
        - ats_score, ats_grade, ats_metadata, ats_analysis
        - ats_recommendations, ats_issues
        - ats_optimized_content, ats_changes
        - created_at, updated_at (timestamps)
        - Any other dynamic/metadata fields
        """
        if not cv_data or not isinstance(cv_data, dict):
            return {}
        
        # Extract only stable CV content
        canonical = {}
        
        # Summary
        if cv_data.get("summary"):
            canonical["summary"] = str(cv_data["summary"]).strip()
        elif cv_data.get("professional_summary"):
            canonical["summary"] = str(cv_data["professional_summary"]).strip()
        
        # Experience - normalize structure
        experience_list = []
        for exp in (cv_data.get("experience", []) or cv_data.get("work_experience", []) or []):
            if isinstance(exp, dict):
                exp_normalized = {
                    "title": str(exp.get("job_title") or exp.get("position") or exp.get("title") or "").strip(),
                    "company": str(exp.get("company") or exp.get("employer") or exp.get("organization") or "").strip(),
                    "description": str(exp.get("description") or exp.get("responsibilities") or exp.get("duties") or "").strip(),
                }
                # Only include if has meaningful content
                if exp_normalized["title"] or exp_normalized["company"] or exp_normalized["description"]:
                    experience_list.append(exp_normalized)
        if experience_list:
            canonical["experience"] = experience_list
        
        # Education - normalize structure
        education_list = []
        for edu in (cv_data.get("education", []) or []):
            if isinstance(edu, dict):
                edu_normalized = {
                    "degree": str(edu.get("degree") or edu.get("qualification") or "").strip(),
                    "institution": str(edu.get("institution") or edu.get("school") or edu.get("university") or "").strip(),
                    "field": str(edu.get("field_of_study") or edu.get("major") or "").strip(),
                }
                # Only include if has meaningful content
                if edu_normalized["degree"] or edu_normalized["institution"]:
                    education_list.append(edu_normalized)
        if education_list:
            canonical["education"] = education_list
        
        # Skills - normalize to sorted lists
        skills_data = cv_data.get("skills", {}) or cv_data.get("personal_skills", {})
        if isinstance(skills_data, dict):
            skills_normalized = {}
            # Collect all skills from various keys
            all_skills = []
            for skill_type in ["technical", "job_related_skills", "computer_skills", "programming_skills", 
                             "soft", "social_skills", "languages", "tools",
                             "Programming Languages", "Frameworks and Libraries", "Blockchain", 
                             "Databases", "Data Science", "Tools and Platforms"]:
                skill_list = skills_data.get(skill_type) or []
                if isinstance(skill_list, list):
                    all_skills.extend([str(s).strip() for s in skill_list if s])
                elif isinstance(skill_list, str) and skill_list.strip():
                    all_skills.append(skill_list.strip())
            
            # Sort and deduplicate
            if all_skills:
                canonical["skills"] = sorted(list(set(all_skills)))
        
        return canonical

    def _normalize_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """Extract and normalize CV text for analysis."""
        parts = []
        
        if not cv_data or not isinstance(cv_data, dict):
            logger.warning(f"ATSEngine: Invalid CV data - not a dict or empty. Type: {type(cv_data)}, Value: {cv_data}")
            return ""

        try:
            # Personal info
            if cv_data.get("personal_info") and isinstance(cv_data["personal_info"], dict):
                pi = cv_data["personal_info"]
                if pi.get("full_name"):
                    parts.append(str(pi.get("full_name", "")))
                if pi.get("email"):
                    parts.append(str(pi.get("email", "")))

            # Summary
            if cv_data.get("summary"):
                parts.append(str(cv_data["summary"]))
            elif cv_data.get("professional_summary"):
                parts.append(str(cv_data["professional_summary"]))

            # Experience
            exp_list = cv_data.get("experience", []) or []
            work_exp_list = cv_data.get("work_experience", []) or []
            for exp in exp_list + work_exp_list:
                if isinstance(exp, dict):
                    job_title = exp.get("job_title") or exp.get("position") or exp.get("title") or ""
                    company = exp.get("company") or exp.get("employer") or exp.get("organization") or ""
                    desc = exp.get("description") or exp.get("responsibilities") or exp.get("duties") or ""
                    parts.append(f"{job_title} {company} {desc}")

            # Education
            edu_list = cv_data.get("education", []) or []
            for edu in edu_list:
                if isinstance(edu, dict):
                    degree = edu.get("degree") or edu.get("qualification") or ""
                    institution = edu.get("institution") or edu.get("school") or edu.get("university") or ""
                    field = edu.get("field_of_study") or edu.get("major") or ""
                    parts.append(f"{degree} {institution} {field}")

            # Skills - handle both lowercase and capitalized category names
            skills_data = cv_data.get("skills", {}) or cv_data.get("personal_skills", {})
            if isinstance(skills_data, dict):
                # Standard lowercase keys
                for skill_type in ["technical", "job_related_skills", "computer_skills", "programming_skills", "soft", "social_skills", "languages", "tools"]:
                    skill_list = skills_data.get(skill_type) or []
                    if isinstance(skill_list, list):
                        parts.append(" ".join(str(s) for s in skill_list))
                    elif isinstance(skill_list, str):
                        parts.append(skill_list)
                
                # Capitalized category names (from user's CV)
                for skill_category in ["Programming Languages", "Frameworks and Libraries", "Blockchain", "Databases", "Data Science", "Tools and Platforms"]:
                    skill_list = skills_data.get(skill_category) or []
                    if isinstance(skill_list, list):
                        parts.append(" ".join(str(s) for s in skill_list))
                    elif isinstance(skill_list, str):
                        parts.append(skill_list)
            
            # Projects
            projects = cv_data.get("projects", []) or []
            for proj in projects:
                if isinstance(proj, dict):
                    title = proj.get("title") or proj.get("name") or ""
                    desc = proj.get("description") or ""
                    tech = proj.get("technologies") or proj.get("tech_stack") or ""
                    if isinstance(tech, list):
                        tech = " ".join(str(t) for t in tech)
                    parts.append(f"{title} {desc} {tech}")

            # Normalize: lowercase, remove extra spaces
            normalized = " ".join(parts).lower()
            normalized = re.sub(r"\s+", " ", normalized).strip()
            return normalized
        except Exception as e:
            logger.warning(f"ATSEngine: Error normalizing CV text: {e}")
            return ""

    def _score_keyword_match(self, cv_data: Dict[str, Any], normalized_text: str) -> Dict[str, Any]:
        """Score keyword & skill match (30% weight)."""
        base_score = 0
        keyword_count = 0
        matched_keywords = []

        # Make search case-insensitive
        normalized_lower = normalized_text.lower()

        # Count technical keywords (more lenient matching)
        for category, keywords in self.ATS_FRIENDLY_KEYWORDS["technical"].items():
            for kw in keywords:
                kw_lower = kw.lower()
                # Search with word boundaries or substring
                if kw_lower in normalized_lower:
                    base_score += 2  # 2 points per keyword
                    keyword_count += 1
                    matched_keywords.append(kw)

        # Extract skills from CV structure - handle ALL skill categories
        skills_data = cv_data.get("skills", {}) or cv_data.get("personal_skills", {})
        skill_boost = 0
        total_skills_listed = 0
        
        if isinstance(skills_data, dict):
            # Check ALL possible skill keys (both standard and user-provided)
            all_skill_keys = [
                "technical", "job_related_skills", "computer_skills", "programming_skills", 
                "languages", "tools", "soft", "social_skills", "frameworks", "databases", 
                "blockchain", "mobile", "data", "ai_ml", "cloud",
                # Also check capitalized versions
                "Programming Languages", "Frameworks and Libraries", "Blockchain", 
                "Databases", "Data Science", "Tools and Platforms"
            ]
            
            for skill_type in all_skill_keys:
                skills = skills_data.get(skill_type, [])
                if isinstance(skills, list):
                    # Filter out empty strings and count
                    valid_skills = [s for s in skills if isinstance(s, str) and s.strip()]
                    total_skills_listed += len(valid_skills)
                    skill_boost += len(valid_skills) * 1.5  # 1.5 points per explicit skill
                elif isinstance(skills, str) and skills.strip():
                    # Parse comma/pipe/semicolon-separated string
                    skills_list = [s.strip() for s in re.split(r'[,|;]', skills) if s.strip()]
                    total_skills_listed += len(skills_list)
                    skill_boost += len(skills_list) * 1.5

        base_score += skill_boost
        
        # Ensure good CVs get high scores
        if keyword_count >= 10 and total_skills_listed >= 10:
            base_score = max(base_score, 80)  # Minimum 80 if well-stocked
        elif keyword_count >= 5 and total_skills_listed >= 5:
            base_score = max(base_score, 60)  # Minimum 60 if decent
        
        base_score = min(100, base_score)  # Cap at 100

        return {
            "score": base_score,
            "keyword_count": keyword_count,
            "total_skills_listed": total_skills_listed,
            "matched_keywords": matched_keywords[:15],  # Top 15
            "rationale": f"Found {keyword_count} technical keywords and {total_skills_listed} explicit skills"
        }

    def _score_experience_quality(self, cv_data: Dict[str, Any], normalized_text: str) -> Dict[str, Any]:
        """Score experience quality (20% weight)."""
        score = 0
        experience_list = cv_data.get("experience", []) or []
        work_exp_list = cv_data.get("work_experience", []) or []
        experience_entries = experience_list + work_exp_list
        
        if not experience_entries:
            return {"score": 0, "rationale": "No experience entries found"}

        action_verbs_used = 0
        detailed_descriptions = 0

        for exp in experience_entries:
            if not isinstance(exp, dict):
                continue

            # Check for action verbs in description/responsibilities
            desc = str(exp.get("description") or exp.get("responsibilities") or exp.get("duties") or "").lower()
            
            if desc:
                # Count ALL action verbs found (not just first one)
                verbs_in_this_entry = 0
                for verb in self.ATS_FRIENDLY_KEYWORDS["action_verbs"]:
                    if verb in desc:
                        verbs_in_this_entry += 1
                action_verbs_used += verbs_in_this_entry

                # Length of description as indicator of detail (more lenient threshold)
                if len(desc) > 50:  # Was 100, too harsh
                    detailed_descriptions += 1

        # Scoring logic (MORE GENEROUS)
        score += min(40, action_verbs_used * 3)  # Up to 40 for action verbs
        score += min(30, detailed_descriptions * 15)  # Up to 30 for detailed descriptions
        score += min(20, len(experience_entries) * 10)  # Up to 20 for number of roles
        score += 10  # Base for having experience

        return {
            "score": min(100, score),
            "action_verbs_count": action_verbs_used,
            "detailed_descriptions": detailed_descriptions,
            "experience_entries": len(experience_entries),
            "rationale": f"{len(experience_entries)} roles with {action_verbs_used} action verbs and {detailed_descriptions} detailed descriptions"
        }

    def _score_formatting(self, cv_data: Dict[str, Any], normalized_text: str) -> Dict[str, Any]:
        """Score formatting & ATS readability (15% weight)."""
        score = 50  # Base score

        # Check for required sections
        has_summary = bool(cv_data.get("summary") or cv_data.get("professional_summary"))
        has_experience = bool(cv_data.get("experience") or cv_data.get("work_experience"))
        has_education = bool(cv_data.get("education"))
        has_skills = bool(cv_data.get("skills"))

        if has_summary:
            score += 15
        if has_experience and has_education:
            score += 20
        if has_skills:
            score += 15

        # Penalize red flags
        red_flag_count = 0
        for flag_type, flags in self.RED_FLAGS.items():
            for flag in flags:
                if flag.lower() in normalized_text:
                    red_flag_count += 1
                    score -= 5

        return {
            "score": max(0, min(100, score)),
            "sections_present": {
                "summary": has_summary,
                "experience": has_experience,
                "education": has_education,
                "skills": has_skills,
            },
            "red_flags_found": red_flag_count,
            "rationale": f"Complete structure ({sum([has_summary, has_experience, has_education, has_skills])}/4 sections) with {red_flag_count} formatting issues"
        }

    def _score_completeness(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score section completeness (10% weight)."""
        score = 0

        # Experience completeness
        exp_list = cv_data.get("experience", []) or []
        work_exp_list = cv_data.get("work_experience", []) or []
        exp_entries = exp_list + work_exp_list
        exp_present = False
        if exp_entries:
            complete_exp = sum(1 for e in exp_entries if isinstance(e, dict) and 
                             (e.get("job_title") or e.get("position") or e.get("title")) and 
                             (e.get("company") or e.get("employer") or e.get("organization")))
            if complete_exp > 0:
                score += min(25, complete_exp * 10)
                exp_present = True

        # Education completeness
        edu_entries = cv_data.get("education", []) or []
        edu_present = False
        if edu_entries:
            complete_edu = sum(1 for e in edu_entries if isinstance(e, dict) and 
                             (e.get("degree") or e.get("qualification")) and 
                             (e.get("institution") or e.get("school") or e.get("university")))
            if complete_edu > 0:
                score += min(25, complete_edu * 15)
                edu_present = True

        # Skills completeness - COUNT ALL SKILLS PROPERLY
        skills_data = cv_data.get("skills", {}) or cv_data.get("personal_skills", {}) or {}
        skills_present = False
        if isinstance(skills_data, dict):
            # Count all skills across all categories
            total_skills = 0
            for skill_type in ["technical", "job_related_skills", "computer_skills", "programming_skills", 
                              "languages", "tools", "soft", "social_skills", "frameworks", "databases", 
                              "blockchain", "mobile", "data", "ai_ml", "cloud",
                              "Programming Languages", "Frameworks and Libraries", "Blockchain", 
                              "Databases", "Data Science", "Tools and Platforms"]:
                skill_list = skills_data.get(skill_type, [])
                if isinstance(skill_list, list):
                    total_skills += len([s for s in skill_list if isinstance(s, str) and s.strip()])
                elif isinstance(skill_list, str) and skill_list.strip():
                    total_skills += len([s for s in re.split(r'[,|;]', skill_list) if s.strip()])
            
            if total_skills > 0:
                score += 25
                skills_present = True

        # Summary completeness
        has_summary = bool(cv_data.get("summary") or cv_data.get("professional_summary") or cv_data.get("about"))
        if has_summary:
            score += 25

        # Contact info completeness
        personal = cv_data.get("personal_info", {}) or {}
        has_email = bool(personal.get("email") if isinstance(personal, dict) else False)
        has_phone = bool(personal.get("phone") if isinstance(personal, dict) else False)
        contact_score = sum([has_email, has_phone]) * 5  # Bonus points for contact
        score += contact_score

        sections_complete = sum([exp_present, edu_present, skills_present, has_summary])

        return {
            "score": min(100, score),
            "experience_present": exp_present,
            "education_present": edu_present,
            "skills_present": skills_present,
            "summary_present": has_summary,
            "contact_complete": has_email or has_phone,
            "rationale": f"{sections_complete}/4 key sections complete"
        }

    def _score_quantification(self, normalized_text: str) -> Dict[str, Any]:
        """Score achievement quantification (10% weight)."""
        score = 0

        # Look for metrics patterns
        metrics_found = 0

        # Patterns: "X% improvement", "X million", "X thousand", etc.
        patterns = [
            r"\d+%",  # Percentages: 40%, 35%, 60%
            r"\$\d+",  # Currency
            r"\d+\s*(million|billion|thousand|k|m|b)",  # Large numbers
            r"\d+x",  # Multipliers
            r"top\s+\d+",  # Rankings
            r"r²\s*[=:]\s*\d+\.\d+",  # R-squared scores
            r"\d+\.\d+\s*/\s*\d+\.\d+",  # GPA scores like 3.93/4.00
            r"\d+\+\s*(?:sku|user|customer|client|project|system|device|country|countries)",  # 200+ SKUs, 50+ countries
            r"(?:by|from|to|of)\s+\d+",  # reduction/increase by 40
        ]

        for pattern in patterns:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            metrics_found += len(matches)

        score = min(100, metrics_found * 10)  # 10 points per metric

        # Bonus for action verbs with metrics
        action_with_metric = 0
        for verb in self.ATS_FRIENDLY_KEYWORDS["action_verbs"]:
            if verb in normalized_text:
                action_with_metric += 1

        score += min(30, action_with_metric * 3)
        score = min(100, score)

        return {
            "score": score,
            "metrics_found": metrics_found,
            "rationale": f"Found {metrics_found} quantified metrics and {action_with_metric} achievement phrases"
        }

    def _score_role_consistency(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score role consistency and progression (10% weight)."""
        score = 50  # Base score

        exp_list = cv_data.get("experience", []) or []
        work_exp_list = cv_data.get("work_experience", []) or []
        experience = exp_list + work_exp_list
        
        if not experience:
            return {"score": 0, "rationale": "No experience entries for consistency check"}

        # Extract job titles
        titles = [str(e.get("job_title") or e.get("position") or e.get("title") or "").lower() for e in experience if isinstance(e, dict)]
        titles = [t for t in titles if t]  # Filter empty titles

        if not titles:
            return {"score": 0, "rationale": "No job titles found"}

        # Check for career progression
        has_progression = False
        progression_keywords = ["senior", "lead", "principal", "architect", "director"]
        for i in range(1, len(titles)):
            prev_title = titles[i - 1] if i - 1 < len(titles) else ""
            curr_title = titles[i] if i < len(titles) else ""
            # If title gets more senior, that's progression
            for prog_kw in progression_keywords:
                if prog_kw in curr_title and prog_kw not in prev_title:
                    has_progression = True

        if has_progression:
            score += 30
        elif len(titles) > 1:
            score += 15  # Some experience variety

        # Similar role consistency (staying in one field)
        unique_role_types = len(set(titles))
        if unique_role_types <= len(titles) / 2:
            score += 20  # Good focus on related roles

        return {
            "score": min(100, score),
            "titles": titles[:5],  # Show first 5
            "progression_detected": has_progression,
            "role_variety": unique_role_types,
            "rationale": f"{'Career progression detected' if has_progression else 'Stable role focus'} across {len(titles)} positions"
        }

    def _score_red_flags(self, normalized_text: str) -> Dict[str, Any]:
        """
        Score red flags penalty (max -5 points).
        
        FIX 4: Penalty should SUBTRACT from score, not add.
        Returns penalty amount (0 to -5), not a component score.
        """
        penalties = []
        red_flag_count = 0

        for flag_type, flag_list in self.RED_FLAGS.items():
            for flag in flag_list:
                if flag.lower() in normalized_text:
                    penalties.append(f"{flag_type}: {flag}")
                    red_flag_count += 1

        # Calculate penalty: max 5 points, 2 points per flag detected
        penalty_amount = min(5, red_flag_count * 2)
        
        return {
            "penalty": penalty_amount,  # Amount to subtract (0-5)
            "flags_found": red_flag_count,
            "penalty_items": penalties[:5],  # Top 5
            "rationale": f"Found {red_flag_count} red flags ({penalty_amount} point penalty)" if penalties else "No major red flags"
        }

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _calculate_job_specific_score(
        self, 
        cv_data: Dict[str, Any], 
        normalized_text: str, 
        job_context: Dict[str, Any],
        generic_ats_score: float
    ) -> Dict[str, Any]:
        """
        Calculate job-specific ATS relevance score.
        
        Args:
            cv_data: CV data dictionary
            normalized_text: Normalized CV text
            job_context: Job context dict with:
                - job_description: str - Job posting description
                - job_skills: List[str] - Required skills
                - job_title: str - Job title
            generic_ats_score: Generic ATS score (0-100)
        
        Returns:
            Dict with job-specific scoring data:
                - job_specific_score: float (0-100) - Relevance-adjusted score
                - relevance_factor: float (0-1) - How relevant CV is to job
                - keyword_overlap: int - Number of job keywords found in CV
                - keyword_overlap_percentage: float - Percentage of job keywords matched
                - missing_skills: List[str] - Required skills missing from CV
                - matched_job_keywords: List[str] - Job keywords found in CV
        """
        job_description = job_context.get("job_description", "").lower()
        job_skills = [s.lower().strip() for s in job_context.get("job_skills", []) if s]
        job_title = job_context.get("job_title", "").lower()
        
        # Combine all job text for keyword extraction
        job_text = f"{job_title} {job_description}".lower()
        
        # Extract job keywords from description and title
        # Simple keyword extraction (can be enhanced with NLP)
        job_keywords = set()
        
        # Add explicit job skills
        job_keywords.update(job_skills)
        
        # Extract keywords from job description (common tech/business terms)
        import re
        # Extract multi-word phrases
        phrases = re.findall(r'\b[\w\s]{2,3}\s+\w+\b', job_description)
        job_keywords.update([p.strip() for p in phrases if len(p.strip()) > 3])
        
        # Extract single words (important terms)
        words = re.findall(r'\b[a-z]{4,}\b', job_description)
        # Filter out common stop words
        stop_words = {"that", "this", "with", "from", "will", "have", "would", "should", "could", "being", "been", "have"}
        important_words = [w for w in words if w not in stop_words and len(w) > 4]
        job_keywords.update(important_words[:20])  # Top 20 important words
        
        # Add job title words
        title_words = re.findall(r'\b[a-z]{4,}\b', job_title)
        job_keywords.update(title_words)
        
        # Normalize CV text for matching (already normalized)
        cv_text_lower = normalized_text.lower()
        
        # Find matching keywords
        matched_keywords = []
        for keyword in job_keywords:
            if keyword in cv_text_lower:
                matched_keywords.append(keyword)
        
        # Calculate keyword overlap
        keyword_overlap = len(matched_keywords)
        keyword_overlap_percentage = (keyword_overlap / len(job_keywords)) * 100 if job_keywords else 0
        
        # Find missing required skills
        missing_skills = []
        cv_skills = self._extract_all_cv_skills(cv_data)
        cv_skills_lower = [s.lower() for s in cv_skills]
        for skill in job_skills:
            # Check exact match or substring match
            if not any(skill in cv_skill or cv_skill in skill for cv_skill in cv_skills_lower):
                missing_skills.append(skill)
        
        # Calculate relevance factor (0-1)
        # IMPROVED: More lenient and realistic scoring
        
        # 1. More lenient keyword relevance (30% match = full relevance instead of 50%)
        # This means: 30% keyword match gives full credit, making scoring less strict
        keyword_relevance = min(1.0, keyword_overlap_percentage / 30.0)  # Changed from 50.0 to 30.0
        
        # 2. More lenient skill relevance (don't penalize so harshly)
        if job_skills:
            # Calculate skill match percentage instead of just missing skills
            matched_skills = len(job_skills) - len(missing_skills)
            skill_match_percentage = (matched_skills / len(job_skills)) * 100 if job_skills else 100
            # Use a curve: 50% skill match = 0.8 relevance (not 0.5), 100% = 1.0
            # This gives partial credit for partial matches
            skill_relevance = min(1.0, (skill_match_percentage / 50.0) * 0.8 + 0.2)
        else:
            # If no job skills specified, don't penalize
            skill_relevance = 1.0
        
        # Combined relevance factor
        relevance_factor = (keyword_relevance * 0.6) + (skill_relevance * 0.4)
        
        # 3. Ensure minimum relevance (even if match is poor, give some credit)
        # This prevents scores from dropping to 0/100 for jobs that are somewhat relevant
        # Minimum 15% relevance means worst case: 68 × 0.15 = ~10/100 (not 0/100)
        relevance_factor = max(0.15, min(1.0, relevance_factor))
        
        # Calculate job-specific score
        # Job-specific score = Generic ATS score × Relevance factor
        # With minimum relevance, scores will be more realistic:
        # - Very poor match: 68 × 0.15 = 10/100 (instead of 0/100)
        # - Poor match: 68 × 0.4 = 27/100 (stays similar)
        # - Good match: 68 × 0.8 = 54/100
        # - Excellent match: 68 × 1.0 = 68/100
        job_specific_score = generic_ats_score * relevance_factor
        job_specific_score = max(0, min(100, int(job_specific_score)))
        
        logger.info(f"[JOB-SPECIFIC ATS] Job keywords: {len(job_keywords)}, Matched: {keyword_overlap} ({keyword_overlap_percentage:.1f}%), "
                   f"Missing skills: {len(missing_skills)}, Relevance: {relevance_factor:.2%}")
        
        return {
            "job_specific_score": job_specific_score,
            "relevance_factor": relevance_factor,
            "keyword_overlap": keyword_overlap,
            "keyword_overlap_percentage": keyword_overlap_percentage,
            "missing_skills": missing_skills[:10],  # Top 10 missing
            "matched_job_keywords": matched_keywords[:15],  # Top 15 matched
        }
    
    def _extract_all_cv_skills(self, cv_data: Dict[str, Any]) -> List[str]:
        """Extract all skills from CV in a flat list."""
        skills = []
        
        # Extract from skills dict
        skills_data = cv_data.get("skills", {}) or cv_data.get("personal_skills", {})
        if isinstance(skills_data, dict):
            for key, value in skills_data.items():
                if isinstance(value, list):
                    skills.extend([str(s) for s in value if s])
                elif isinstance(value, str) and value.strip():
                    skills.append(value.strip())
        elif isinstance(skills_data, list):
            skills.extend([str(s) for s in skills_data if s])
        
        # Extract from other locations
        for key in ["programming_languages", "frameworks", "tools", "platforms", "libraries"]:
            if key in cv_data and isinstance(cv_data[key], list):
                skills.extend([str(s) for s in cv_data[key] if s])
        
        return [s.strip() for s in skills if s and s.strip()]

    def _generate_feedback(self, cv_data: Dict[str, Any], normalized_text: str, components: Dict[str, Any], ats_score: int) -> Tuple[List[Dict], List[str]]:
        """Generate ATS issues and recommendations."""
        issues = []
        recommendations = []

        # Identify weak components (< 60/100) - handle red_flags_penalty specially
        weak_components = {}
        for k, v in components.items():
            if k == "red_flags_penalty":
                # Skip red_flags_penalty from weak components (it's a penalty, not a score)
                continue
            score = v.get("score", 0)
            if score < 60:
                weak_components[k] = score

        # === ISSUES ===
        if not components["keyword_match"]["score"] > 50:
            issues.append({
                "category": "keywords",
                "severity": "critical",
                "message": "CV lacks industry-standard technical keywords. ATS systems won't recognize your skills."
            })

        if not components["quantification"]["score"] > 40:
            issues.append({
                "category": "achievements",
                "severity": "critical",
                "message": "Achievements lack quantifiable results (percentages, numbers, metrics). Recruiters can't measure impact."
            })

        if components["formatting"]["red_flags_found"] > 0:
            issues.append({
                "category": "formatting",
                "severity": "warning",
                "message": f"Found {components['formatting']['red_flags_found']} formatting or grammar issues that ATS systems flag."
            })

        if not components["completeness"]["score"] > 50:
            issues.append({
                "category": "completeness",
                "severity": "warning",
                "message": "Missing key sections or incomplete fields. Fill in all major sections: Summary, Experience, Education, Skills."
            })

        # === RECOMMENDATIONS ===
        if components["keyword_match"]["score"] < 70:
            recommendations.append(
                f"Add industry-specific keywords: {', '.join(components['keyword_match'].get('matched_keywords', ['python', 'aws', 'react'])[:5])}. "
                "Use exact tool/framework names you've worked with."
            )

        if components["quantification"]["score"] < 70:
            recommendations.append(
                "Quantify all achievements: 'Improved X by Y%', 'Reduced Z from A to B', 'Served N+ users'. "
                "Numbers make impact measurable."
            )

        if components["experience_quality"]["score"] < 70:
            recommendations.append(
                "Use strong action verbs: started, designed, implemented, optimized, accelerated, scaled. "
                "Begin each bullet with a verb, not 'Responsible for'."
            )

        if components["completeness"]["score"] < 70:
            recommendations.append(
                "Ensure all sections are complete: Add a professional summary, fill education end dates, "
                "and list both technical and soft skills."
            )

        if components["role_consistency"]["score"] < 70:
            recommendations.append(
                "Show clear career progression or thematic consistency. Explain how roles connect. "
                "Avoid unexplained gaps or random career shifts."
            )

        return issues, recommendations


# Singleton instance
_ats_engine = None


def get_ats_engine() -> ATSEngine:
    """Get singleton ATS engine instance."""
    global _ats_engine
    if _ats_engine is None:
        _ats_engine = ATSEngine()
    return _ats_engine
