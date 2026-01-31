from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.utils.logger import logger
from app.core.config import settings
import re
import json
from datetime import datetime


class AIService:
    """Advanced AI service for CV generation with market analysis, ATS optimization, and job tailoring."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY  # Backward compatibility
        # Industry keywords for market analysis
        self.industry_keywords = {
            "Technology": ["software development", "cloud computing", "agile", "devops", "api", "microservices"],
            "Healthcare": ["patient care", "medical records", "HIPAA", "clinical", "healthcare systems"],
            "Finance": ["financial analysis", "risk management", "compliance", "accounting", "audit"],
            "Education": ["curriculum development", "pedagogy", "student engagement", "assessment"],
            "Agriculture": ["sustainable farming", "crop management", "agribusiness", "rural development"],
        }
    
    def analyze_job_market(self, db: Session, sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze job market trends, required skills, and keywords.
        
        Returns:
            Market analysis with trending skills, keywords, and requirements
        """
        logger.info(f"Analyzing job market for sector: {sector}")
        
        from app.db.models import Job
        
        # Get all jobs or filter by sector
        query = db.query(Job)
        if sector:
            from app.db.models import Startup
            query = query.join(Job.startup).filter(Startup.sector.ilike(f"%{sector}%"))
        
        jobs = query.all()
        
        # Extract skills and keywords from job descriptions
        all_skills = []
        all_keywords = []
        
        for job in jobs:
            all_skills.extend(job.skills_required or [])
            # Extract keywords from description
            description_lower = job.description.lower()
            keywords = re.findall(r'\b[a-z]{4,}\b', description_lower)
            all_keywords.extend(keywords)
        
        # Count frequency
        skill_freq = {}
        for skill in all_skills:
            skill_lower = skill.lower()
            skill_freq[skill_lower] = skill_freq.get(skill_lower, 0) + 1
        
        keyword_freq = {}
        for keyword in all_keywords:
            if len(keyword) > 3:  # Filter short words
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Get top skills and keywords
        top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Add industry-specific keywords
        industry_keywords_list = self.industry_keywords.get(sector or "Technology", [])
        
        analysis = {
            "sector": sector,
            "total_jobs_analyzed": len(jobs),
            "trending_skills": [{"skill": skill, "frequency": freq} for skill, freq in top_skills],
            "trending_keywords": [{"keyword": kw, "frequency": freq} for kw, freq in top_keywords],
            "industry_keywords": industry_keywords_list,
            "recommendations": self._generate_market_recommendations(top_skills, industry_keywords_list)
        }
        
        logger.info(f"Market analysis complete: {len(top_skills)} trending skills identified")
        return analysis
    
    def extract_skills_and_achievements(
        self,
        experience: list,
        projects: list,
        education: list
    ) -> Dict[str, Any]:
        """
        Extract hard skills, soft skills, tools, and quantifiable achievements.
        
        Returns:
            Extracted skills, achievements, and impact statements
        """
        logger.info("Extracting skills and achievements from user data")
        
        hard_skills = set()
        soft_skills = set()
        tools = set()
        achievements = []
        impact_statements = []
        
        # Extract from experience
        for exp in experience:
            description = exp.get("description", "").lower()
            title = exp.get("title", "").lower()
            
            # Extract hard skills (technical terms)
            tech_keywords = ["python", "javascript", "react", "node", "sql", "api", "database",
                           "management", "analysis", "design", "development", "marketing",
                           "sales", "finance", "accounting", "healthcare", "education"]
            for keyword in tech_keywords:
                if keyword in description or keyword in title:
                    hard_skills.add(keyword.title())
            
            # Extract soft skills
            soft_keywords = ["leadership", "teamwork", "communication", "collaboration",
                           "problem-solving", "critical thinking", "adaptability"]
            for keyword in soft_keywords:
                if keyword in description:
                    soft_skills.add(keyword.title())
            
            # Extract quantifiable achievements (numbers, percentages)
            numbers = re.findall(r'(\d+%?|\$\d+[KMB]?|\d+\+|\d+[KMB]?)', exp.get("description", ""))
            if numbers:
                achievements.append({
                    "context": exp.get("title", ""),
                    "metrics": numbers,
                    "description": exp.get("description", "")
                })
            
            # Extract impact statements
            impact_verbs = ["increased", "decreased", "improved", "reduced", "achieved",
                          "delivered", "led", "managed", "created", "developed"]
            for verb in impact_verbs:
                if verb in description:
                    # Extract sentence with impact verb
                    sentences = re.split(r'[.!?]', description)
                    for sentence in sentences:
                        if verb in sentence.lower():
                            impact_statements.append(sentence.strip())
                            break
        
        # Extract from projects
        for project in projects:
            if isinstance(project, str):
                project_lower = project.lower()
                # Extract technical terms
                for keyword in ["python", "javascript", "react", "app", "system", "platform"]:
                    if keyword in project_lower:
                        hard_skills.add(keyword.title())
        
        # Extract tools from experience descriptions
        tools_keywords = ["excel", "word", "powerpoint", "photoshop", "figma", "jira",
                        "slack", "trello", "github", "git", "docker", "kubernetes"]
        for exp in experience:
            desc_lower = exp.get("description", "").lower()
            for tool in tools_keywords:
                if tool in desc_lower:
                    tools.add(tool.title())
        
        return {
            "hard_skills": sorted(list(hard_skills)),
            "soft_skills": sorted(list(soft_skills)),
            "tools": sorted(list(tools)),
            "achievements": achievements[:10],  # Top 10
            "impact_statements": impact_statements[:5],  # Top 5
            "hidden_achievements": self._identify_hidden_achievements(experience)
        }
    
    def tailor_cv_to_job(
        self,
        cv_data: Dict[str, Any],
        job_description: str,
        job_skills: List[str],
        job_title: str
    ) -> Dict[str, Any]:
        """
        Tailor CV to a specific job listing.
        
        Returns:
            Tailored CV with job-specific keywords and emphasized experiences
        """
        logger.info(f"Tailoring CV for job: {job_title}")
        
        # Extract keywords from job description
        job_keywords = self._extract_keywords_from_job(job_description, job_skills)
        
        # Create tailored CV
        tailored_cv = cv_data.copy()
        
        # Enhance summary with job keywords
        original_summary = tailored_cv.get("summary", "")
        tailored_summary = self._enhance_summary_with_keywords(original_summary, job_keywords, job_title)
        tailored_cv["summary"] = tailored_summary
        
        # Reorder and emphasize relevant experience
        experience = tailored_cv.get("work_experience", [])
        tailored_experience = self._prioritize_relevant_experience(experience, job_keywords, job_skills)
        tailored_cv["work_experience"] = tailored_experience
        
        # Enhance skills section with job-relevant skills first
        skills = tailored_cv.get("personal_skills", {})
        job_related_skills = skills.get("job_related_skills", [])
        prioritized_skills = self._prioritize_skills(job_related_skills, job_skills)
        tailored_cv["personal_skills"]["job_related_skills"] = prioritized_skills
        
        # Add job-specific recommendations
        tailored_cv["job_tailoring"] = {
            "target_job": job_title,
            "keywords_added": job_keywords[:10],
            "skills_emphasized": [s for s in job_skills if s.lower() in [sk.lower() for sk in job_related_skills]][:5],
            "recommendations": self._generate_job_specific_recommendations(cv_data, job_keywords, job_skills)
        }
        
        logger.info(f"CV tailored for {job_title}: {len(job_keywords)} keywords integrated")
        return tailored_cv
    
    def optimize_for_ats(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize CV for Applicant Tracking Systems (ATS) with full transparency.
        
        Returns:
            Dict with:
            - optimized_cv: The optimized CV data
            - changes: List of all changes made with before/after/reason
            - original_cv: Copy of original CV (never modified)
        """
        logger.info("Optimizing CV for ATS compatibility with full change tracking")
        
        # Store original CV - NEVER modify this
        original_cv = json.loads(json.dumps(cv_data))  # Deep copy
        optimized_cv = json.loads(json.dumps(cv_data))  # Deep copy for optimization
        
        changes = []  # Track all changes: [{section, change, before, after, reason}]
        
        # ===== CHANGE 1: Summary Optimization =====
        original_summary = optimized_cv.get("summary", "")
        if original_summary:
            # Remove special characters that ATS might not parse
            optimized_summary = re.sub(r'[^\w\s.,;:()\-]', '', original_summary)
            
            # Enhance with action verbs if missing
            if not any(verb in original_summary.lower() for verb in ["led", "delivered", "achieved", "created", "improved", "managed"]):
                # Add professional opening if missing
                if not original_summary[0].isupper() or len(original_summary.split()) < 20:
                    optimized_summary = f"Experienced professional with expertise in {original_summary[:50]}. " + optimized_summary
            
            if optimized_summary != original_summary:
                optimized_cv["summary"] = optimized_summary
                changes.append({
                    "section": "summary",
                    "change": "Professional summary optimized for ATS parsing",
                    "before": original_summary[:200] + ("..." if len(original_summary) > 200 else ""),
                    "after": optimized_summary[:200] + ("..." if len(optimized_summary) > 200 else ""),
                    "reason": "Removed special characters and enhanced with ATS-friendly formatting to improve keyword recognition"
                })
        
        # ===== CHANGE 2: Experience Descriptions Enhancement =====
        experience = optimized_cv.get("work_experience", optimized_cv.get("experience", []))
        if experience and isinstance(experience, list):
            for idx, exp in enumerate(experience):
                original_desc = exp.get("description", "")
                if original_desc:
                    # Check if needs action verbs
                    desc_lower = original_desc.lower()
                    has_action_verb = any(verb in desc_lower for verb in 
                        ["led", "delivered", "achieved", "created", "improved", "managed", "developed", "designed", "implemented"])
                    
                    # Check if has quantifiers
                    has_quantifier = bool(re.search(r'\d+', original_desc))
                    
                    optimized_desc = original_desc
                    change_made = False
                    
                    # Add action verb if missing
                    if not has_action_verb and original_desc.strip():
                        # Try to add action verb at start
                        first_word = original_desc.split()[0] if original_desc.split() else ""
                        if first_word and first_word.lower() not in ["worked", "responsible", "helped", "assisted"]:
                            optimized_desc = f"Led {original_desc.lower()}"
                            change_made = True
                    
                    # Suggest quantifiers if missing
                    if not has_quantifier and change_made:
                        optimized_desc += " (Add specific metrics for better impact)"
                    
                    if change_made and optimized_desc != original_desc:
                        exp["description"] = optimized_desc
                        changes.append({
                            "section": f"experience_{idx}",
                            "change": f"Enhanced experience description at {exp.get('company', 'Company')}",
                            "before": original_desc[:150] + ("..." if len(original_desc) > 150 else ""),
                            "after": optimized_desc[:150] + ("..." if len(optimized_desc) > 150 else ""),
                            "reason": "Added action verbs and suggested quantifiers to improve ATS keyword matching and impact"
                        })
        
        # ===== CHANGE 3: Skills Formatting =====
        skills = optimized_cv.get("personal_skills", optimized_cv.get("skills", {}))
        if isinstance(skills, dict):
            original_skills_format = json.dumps(skills)
            
            # Flatten skills for ATS compatibility
            all_skills = []
            if skills.get("job_related_skills"):
                all_skills.extend(skills["job_related_skills"])
            if skills.get("computer_skills"):
                all_skills.extend(skills["computer_skills"])
            if skills.get("technical"):
                all_skills.extend(skills["technical"])
            if skills.get("technical_skills"):
                all_skills.extend(skills["technical_skills"])
            
            # Remove duplicates and sort
            all_skills = sorted(list(set([str(s).strip() for s in all_skills if s])))
            
            if all_skills:
                optimized_cv["ats_skills"] = ", ".join(all_skills)
                changes.append({
                    "section": "skills",
                    "change": "Skills formatted for better ATS recognition",
                    "before": f"Skills stored in nested format ({len(all_skills)} skills)",
                    "after": f"Flattened to comma-separated list: {', '.join(all_skills[:5])}{'...' if len(all_skills) > 5 else ''}",
                    "reason": "ATS systems parse comma-separated skills better than nested objects. This improves keyword extraction."
                })
        
        # ===== CHANGE 4: Section Headers Standardization =====
        # Ensure standard section names (already handled in data structure, but document it)
        section_mapping = {
            "work_experience": "WORK EXPERIENCE",
            "experience": "WORK EXPERIENCE",
            "education": "EDUCATION",
            "skills": "SKILLS",
            "summary": "PROFESSIONAL SUMMARY"
        }
        
        # Document section standardization
        if "experience" in optimized_cv and "work_experience" not in optimized_cv:
            optimized_cv["work_experience"] = optimized_cv["experience"]
            changes.append({
                "section": "structure",
                "change": "Standardized section naming",
                "before": "Section named 'experience'",
                "after": "Section standardized to 'work_experience'",
                "reason": "ATS systems recognize 'work_experience' more reliably than 'experience'"
            })
        
        # ===== CHANGE 5: Keyword Enhancement =====
        # Identify missing common keywords and suggest additions
        cv_text = json.dumps(optimized_cv).lower()
        common_keywords = ["experience", "skills", "education", "achievement", "leadership", "project", "team", "results", "development", "management"]
        missing_keywords = [kw for kw in common_keywords if kw not in cv_text]
        
        if missing_keywords:
            # Add missing keywords to summary if possible
            summary = optimized_cv.get("summary", "")
            if summary and len(missing_keywords) > 0:
                suggested_keywords = missing_keywords[:3]  # Top 3 missing
                changes.append({
                    "section": "keywords",
                    "change": "Identified missing ATS keywords",
                    "before": f"CV missing keywords: {', '.join(suggested_keywords)}",
                    "after": f"Consider adding: {', '.join(suggested_keywords)} to improve keyword density",
                    "reason": f"These keywords ({', '.join(suggested_keywords)}) are commonly searched by ATS systems. Adding them increases match probability."
                })
        
        # Calculate optimization metadata
        keyword_density = self._calculate_keyword_density(optimized_cv)
        formatting_score = self._check_ats_formatting(optimized_cv)
        section_completeness = self._check_section_completeness(optimized_cv)
        
        # Add ATS optimization metadata (without modifying original)
        optimization_metadata = {
            "keyword_density": keyword_density,
            "section_completeness": section_completeness,
            "formatting_score": formatting_score,
            "recommendations": self._generate_ats_recommendations(optimized_cv),
            "changes_count": len(changes),
            "optimized_at": datetime.now().isoformat() if 'datetime' in globals() else None
        }
        
        optimized_cv["ats_optimization_metadata"] = optimization_metadata
        
        logger.info(f"ATS optimization complete: {len(changes)} changes made")
        
        return {
            "optimized_cv": optimized_cv,
            "original_cv": original_cv,  # Always return original, never modified
            "changes": changes,
            "optimization_metadata": optimization_metadata
        }
    
    def enhance_language(
        self, 
        text: str, 
        section: str = "experience",
        user_data: Optional[Dict[str, Any]] = None,
        experience: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Enhance text with powerful, professional language.
        
        CRITICAL: Never invents metrics, projects, leadership roles, or achievements.
        Only improves clarity, structure, and professionalism of user-provided content.
        
        Uses OpenAI API if available, otherwise falls back to rule-based enhancement.
        """
        if not text:
            return text
        
        # Import hallucination validator
        from app.services.hallucination_validator import HallucinationValidator
        validator = HallucinationValidator()
        
        user_data = user_data or {}
        experience = experience or []
        is_entry_level = validator.is_entry_level(user_data, experience)
        
        # Try Mistral AI API if key is available
        if self.mistral_key:
            try:
                from mistralai import Mistral
                client = Mistral(api_key=self.mistral_key)
                
                # Build strict prompt based on entry-level status
                entry_level_instructions = ""
                if is_entry_level:
                    entry_level_instructions = """
CRITICAL ENTRY-LEVEL RULES:
- Use entry-level verbs: "assisted", "participated", "contributed", "supported", "gained exposure", "learned"
- DO NOT use leadership verbs: "led", "spearheaded", "managed", "directed", "executed", "delivered"
- DO NOT invent metrics, percentages, or numbers
- DO NOT mention systems or tools unless user explicitly stated them
- Focus on learning, growth, and willingness to contribute
"""
                
                prompt = f"""Rewrite the following CV {section} description to be more professional and ATS-friendly.
{entry_level_instructions}

STRICT RULES (NON-NEGOTIABLE):
1. ONLY rewrite, expand, or refine information EXPLICITLY provided by the user
2. NEVER invent: metrics (%, numbers, revenue), projects, leadership roles, systems, or tools
3. If user didn't mention it, it does NOT exist - do NOT add it
4. Improve clarity, structure, and professionalism ONLY
5. Remove first-person pronouns (I, my, me) and make it concise
6. If user provided no metrics, output must contain NO metrics
7. If user provided no leadership claims, output must contain NO leadership verbs

Original text:
{text}

Enhanced version (only return the enhanced text, no explanations. DO NOT add anything the user didn't mention):"""
                
                response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional CV writing assistant. You ONLY improve clarity and structure. You NEVER invent metrics, projects, leadership roles, or achievements. If the user didn't mention it, it doesn't exist. Never use markdown formatting - return plain text only."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3  # Lower temperature for more conservative output
                )
                
                enhanced = response.choices[0].message.content.strip()
                # Strip markdown formatting
                import re
                enhanced = re.sub(r'\*\*(.*?)\*\*', r'\1', enhanced)  # Bold
                enhanced = re.sub(r'\*(.*?)\*', r'\1', enhanced)  # Italic
                enhanced = re.sub(r'`(.*?)`', r'\1', enhanced)  # Code
                enhanced = enhanced.strip()
                
                # VALIDATE: Check for hallucinations
                is_valid, violations = validator.validate_complete(
                    enhanced, text, user_data, experience, section
                )
                
                if not is_valid:
                    logger.warning(f"AI hallucination detected in {section}: {', '.join(violations)}. Sanitizing output.")
                    enhanced = validator.sanitize_output(enhanced, text, user_data, experience, section)
                
                if enhanced:
                    logger.info(f"AI-enhanced text for {section} section (Mistral AI, entry-level: {is_entry_level})")
                    return enhanced
            except ImportError:
                logger.warning("Mistral AI library not installed, using rule-based enhancement")
            except Exception as e:
                logger.error(f"Mistral AI API error: {str(e)}, falling back to rule-based enhancement")
        
        # Fallback to rule-based enhancement (SAFE - no invention)
        weak_verbs = {
            "worked": "contributed to" if is_entry_level else "executed",
            "helped": "assisted with" if is_entry_level else "collaborated to",
            "did": "participated in" if is_entry_level else "delivered",
            "made": "contributed to creating" if is_entry_level else "created",
            "got": "gained" if is_entry_level else "achieved",
            "did stuff": "participated in" if is_entry_level else "implemented",
            "was responsible for": "assisted with" if is_entry_level else "managed",
            "assisted": "assisted with",
            "worked on": "participated in" if is_entry_level else "contributed to",
            "helped with": "assisted with",
            "i did": "participated in" if is_entry_level else "delivered",
            "my job was": "key responsibilities included assisting with" if is_entry_level else "key responsibilities included"
        }
        
        enhanced = text
        for weak, strong in weak_verbs.items():
            enhanced = re.sub(rf'\b{re.escape(weak)}\b', strong, enhanced, flags=re.IGNORECASE)
        
        # CRITICAL: DO NOT add quantifiers if missing - this would be invention
        # Removed the code that adds "managed and optimized" or "led and delivered"
        
        # Ensure professional tone - remove first person
        enhanced = re.sub(r'\bI\s+', '', enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r'\bi\s+', '', enhanced)
        enhanced = enhanced.replace("my ", "the ").replace("My ", "The ")
        enhanced = enhanced.replace("me ", "").replace("Me ", "")
        
        return enhanced.strip()
    
    def highlight_strengths(
        self,
        cv_data: Dict[str, Any],
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Identify and highlight user's key strengths.
        
        Returns:
            CV with highlighted strengths and leadership moments
        """
        logger.info("Identifying and highlighting user strengths")
        
        highlighted_cv = cv_data.copy()
        strengths = {
            "leadership_moments": [],
            "teamwork_examples": [],
            "technical_competencies": [],
            "unique_achievements": []
        }
        
        # Analyze experience for strengths
        experience = cv_data.get("work_experience", [])
        for exp in experience:
            desc = exp.get("description", "").lower()
            title = exp.get("title", "").lower()
            
            # Leadership moments
            if any(word in desc for word in ["led", "managed", "supervised", "directed", "headed"]):
                strengths["leadership_moments"].append({
                    "role": exp.get("title", ""),
                    "example": exp.get("description", "")
                })
            
            # Teamwork examples
            if any(word in desc for word in ["collaborated", "team", "worked with", "coordinated"]):
                strengths["teamwork_examples"].append({
                    "role": exp.get("title", ""),
                    "example": exp.get("description", "")
                })
            
            # Technical competencies
            tech_keywords = ["python", "javascript", "react", "sql", "api", "system", "platform"]
            if any(keyword in desc for keyword in tech_keywords):
                strengths["technical_competencies"].append(exp.get("title", ""))
        
        # Analyze projects for unique achievements
        projects = cv_data.get("additional_info", {}).get("projects", [])
        for project in projects[:3]:  # Top 3 projects
            if isinstance(project, str) and len(project) > 20:
                strengths["unique_achievements"].append(project)
        
        # Add strengths section to CV
        highlighted_cv["strengths_analysis"] = strengths
        highlighted_cv["highlighted_summary"] = self._create_highlighted_summary(
            cv_data.get("summary", ""),
            strengths
        )
        
        logger.info(f"Identified {len(strengths['leadership_moments'])} leadership moments")
        return highlighted_cv
    
    def generate_cv(
        self,
        user_data: Dict[str, Any],
        certificates: list = None,  # Deprecated - use education list instead
        experience: list = None,
        education: list = None,
        skills: Dict[str, Any] = None,
        awards: list = None,
        publications: list = None,
        projects: list = None,
        memberships: list = None,
        job_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate a professional CV with AI enhancements.
        
        If job_id is provided, the CV will be tailored to that specific job.
        """
        logger.info(f"Generating AI-enhanced CV for user: {user_data.get('full_name')}")
        
        # Step 1: Extract skills and achievements
        extracted_data = self.extract_skills_and_achievements(experience, projects or [], education or [])
        
        # Step 2: Enhance experience descriptions with powerful language
        # CRITICAL: Pass user_data and experience to prevent hallucinations
        enhanced_experience = []
        for exp in experience:
            enhanced_exp = exp.copy()
            enhanced_exp["description"] = self.enhance_language(
                exp.get("description", ""), 
                "experience",
                user_data=user_data,
                experience=experience
            )
            enhanced_experience.append(enhanced_exp)
        
        # Step 3: Build base CV structure
        cv_data = {
            "personal_info": {
                "surname": user_data.get("surname", ""),
                "first_name": user_data.get("first_name", ""),
                "full_name": user_data.get("full_name", "") or f"{user_data.get('first_name', '')} {user_data.get('surname', '')}".strip(),
                "address": user_data.get("address", ""),
                "phone": user_data.get("phone", ""),
                "email": user_data.get("email", ""),
                "date_of_birth": user_data.get("date_of_birth", ""),
                "nationality": user_data.get("nationality", ""),
                "gender": user_data.get("gender", ""),
                "wallet_address": user_data.get("wallet_address", ""),
                "photo_url": user_data.get("photo_url")
            },
            "summary": self._generate_enhanced_summary(user_data, enhanced_experience, skills or {}, extracted_data),
            "education": self._format_education_europass(certificates or [], education or []),
            "work_experience": enhanced_experience,
            "personal_skills": self._format_skills_europass(skills or {}),
            "additional_info": {
                "awards": awards or [],
                "publications": publications or [],
                "projects": projects or [],
                "memberships": memberships or []
            },
            "blockchain_verification": {
                "verified_certificates": 0,  # Certificates removed - using education from CV
                "on_chain_proof": True
            },
            "extracted_data": extracted_data
        }
        
        # Step 4: Tailor to specific job if job_id provided
        if job_id and db:
            from app.db.models import Job
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                cv_data = self.tailor_cv_to_job(
                    cv_data,
                    job.description,
                    job.skills_required or [],
                    job.title
                )
        
        # Step 5: Optimize for ATS
        cv_data = self.optimize_for_ats(cv_data)
        
        # Step 6: Highlight strengths
        job_reqs = None
        if job_id and db:
            from app.db.models import Job
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job_reqs = {
                    "skills": job.skills_required or [],
                    "title": job.title
                }
        cv_data = self.highlight_strengths(cv_data, job_reqs)
        
        # Step 7: Calculate AI score
        cv_data["ai_score"] = self._calculate_cv_score(cv_data)
        
        logger.info(f"AI-enhanced CV generated with score: {cv_data['ai_score']}")
        return cv_data
    
    # Helper methods
    
    def _generate_market_recommendations(self, top_skills: List[tuple], industry_keywords: List[str]) -> List[str]:
        """Generate market-based recommendations."""
        recommendations = []
        
        if top_skills:
            top_3_skills = [skill for skill, _ in top_skills[:3]]
            recommendations.append(f"Emphasize these trending skills: {', '.join(top_3_skills)}")
        
        if industry_keywords:
            recommendations.append(f"Include industry keywords: {', '.join(industry_keywords[:5])}")
        
        recommendations.append("Quantify achievements with numbers and percentages")
        recommendations.append("Use action verbs: Led, Delivered, Achieved, Optimized")
        
        return recommendations
    
    def _extract_keywords_from_job(self, job_description: str, job_skills: List[str]) -> List[str]:
        """Extract keywords from job description."""
        keywords = set()
        
        # Add skills as keywords
        keywords.update([skill.lower() for skill in job_skills])
        
        # Extract important words from description (4+ characters)
        words = re.findall(r'\b[a-z]{4,}\b', job_description.lower())
        
        # Filter common words
        common_words = {"this", "that", "with", "from", "will", "have", "been", "work", "team"}
        important_words = [w for w in words if w not in common_words]
        
        # Count frequency and get top keywords
        word_freq = {}
        for word in important_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        keywords.update([word for word, _ in top_words])
        
        return list(keywords)
    
    def _enhance_summary_with_keywords(self, summary: str, keywords: List[str], job_title: str) -> str:
        """Enhance summary with job-specific keywords."""
        if not summary:
            return f"Results-driven professional seeking {job_title} position with expertise in {', '.join(keywords[:3])}."
        
        # Try to naturally incorporate keywords
        summary_lower = summary.lower()
        missing_keywords = [kw for kw in keywords[:5] if kw not in summary_lower]
        
        if missing_keywords:
            # Add missing keywords naturally
            summary += f" Proficient in {', '.join(missing_keywords[:3])}."
        
        return summary
    
    def _prioritize_relevant_experience(self, experience: list, keywords: List[str], job_skills: List[str]) -> list:
        """Reorder experience to prioritize most relevant roles."""
        def relevance_score(exp):
            score = 0
            desc_lower = exp.get("description", "").lower()
            title_lower = exp.get("title", "").lower()
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword in desc_lower or keyword in title_lower:
                    score += 2
            
            # Check for skill matches
            for skill in job_skills:
                if skill.lower() in desc_lower or skill.lower() in title_lower:
                    score += 3
            
            return score
        
        # Sort by relevance
        sorted_experience = sorted(experience, key=relevance_score, reverse=True)
        return sorted_experience
    
    def _prioritize_skills(self, user_skills: List[str], job_skills: List[str]) -> List[str]:
        """Reorder skills to prioritize job-relevant skills."""
        relevant_skills = []
        other_skills = []
        
        job_skills_lower = [s.lower() for s in job_skills]
        
        for skill in user_skills:
            if any(js in skill.lower() for js in job_skills_lower):
                relevant_skills.append(skill)
            else:
                other_skills.append(skill)
        
        return relevant_skills + other_skills
    
    def _generate_job_specific_recommendations(
        self,
        cv_data: Dict[str, Any],
        keywords: List[str],
        job_skills: List[str]
    ) -> List[str]:
        """Generate job-specific recommendations."""
        recommendations = []
        
        # Check if keywords are in CV
        cv_text = str(cv_data).lower()
        missing_keywords = [kw for kw in keywords[:10] if kw not in cv_text]
        
        if missing_keywords:
            recommendations.append(f"Add these keywords: {', '.join(missing_keywords[:5])}")
        
        # Check skills match
        user_skills = cv_data.get("personal_skills", {}).get("job_related_skills", [])
        user_skills_lower = [s.lower() for s in user_skills]
        missing_skills = [js for js in job_skills if js.lower() not in user_skills_lower]
        
        if missing_skills:
            recommendations.append(f"Consider adding these skills: {', '.join(missing_skills[:3])}")
        
        return recommendations
    
    def _calculate_keyword_density(self, cv_data: Dict[str, Any]) -> float:
        """Calculate keyword density for ATS optimization."""
        # Simple keyword density calculation
        cv_text = str(cv_data).lower()
        total_words = len(cv_text.split())
        if total_words == 0:
            return 0.0
        
        # Count technical keywords
        tech_keywords = ["management", "development", "analysis", "design", "implementation"]
        keyword_count = sum(1 for kw in tech_keywords if kw in cv_text)
        
        return round((keyword_count / total_words) * 100, 2) if total_words > 0 else 0.0
    
    def _check_section_completeness(self, cv_data: Dict[str, Any]) -> Dict[str, bool]:
        """Check if all ATS-required sections are present."""
        return {
            "summary": bool(cv_data.get("summary")),
            "experience": len(cv_data.get("work_experience", [])) > 0,
            "education": len(cv_data.get("education", [])) > 0,
            "skills": bool(cv_data.get("personal_skills", {}).get("job_related_skills"))
        }
    
    def _check_ats_formatting(self, cv_data: Dict[str, Any]) -> float:
        """Check ATS formatting compliance."""
        score = 100.0
        
        # Check for special characters that ATS might not parse
        cv_text = str(cv_data)
        if re.search(r'[^\w\s.,;:()\-\n]', cv_text):
            score -= 10  # Penalize special characters
        
        # Check section headers
        required_sections = ["summary", "experience", "education", "skills"]
        cv_text_lower = cv_text.lower()
        for section in required_sections:
            if section not in cv_text_lower:
                score -= 15
        
        return max(0, score)
    
    def _generate_ats_recommendations(self, cv_data: Dict[str, Any]) -> List[str]:
        """Generate ATS optimization recommendations."""
        recommendations = []
        
        completeness = self._check_section_completeness(cv_data)
        if not completeness.get("summary"):
            recommendations.append("Add a professional summary section")
        if not completeness.get("experience"):
            recommendations.append("Include work experience section")
        if not completeness.get("skills"):
            recommendations.append("List your skills clearly")
        
        formatting_score = self._check_ats_formatting(cv_data)
        if formatting_score < 90:
            recommendations.append("Remove special characters and use plain text formatting")
        
        return recommendations
    
    def _identify_hidden_achievements(self, experience: list) -> List[str]:
        """Identify achievements that user might not have highlighted."""
        hidden = []
        
        for exp in experience:
            desc = exp.get("description", "")
            # Look for quantifiable results
            if re.search(r'\d+', desc):
                hidden.append(f"{exp.get('title', 'Role')}: {desc[:100]}")
        
        return hidden[:5]
    
    def _create_highlighted_summary(self, original_summary: str, strengths: Dict[str, Any]) -> str:
        """Create a summary that highlights key strengths."""
        if not original_summary:
            return ""
        
        # Add strength highlights if not already present
        if strengths.get("leadership_moments") and "leadership" not in original_summary.lower():
            original_summary += " Proven leadership experience."
        
        if strengths.get("technical_competencies") and "technical" not in original_summary.lower():
            original_summary += " Strong technical background."
        
        return original_summary
    
    def _generate_enhanced_summary(
        self,
        user_data: Dict[str, Any],
        experience: list,
        skills: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> str:
        """
        Generate an enhanced professional summary.
        
        CRITICAL RULES:
        - Summary is GENERAL (who you are, what you studied, what skills you have)
        - NO project stories, NO metrics, NO timelines
        - Entry-level users get entry-level language
        - Never invent achievements or impact statements
        """
        from app.services.hallucination_validator import HallucinationValidator
        validator = HallucinationValidator()
        
        role = user_data.get("role", "professional").lower()
        years_exp = len(experience) if experience else 0
        is_entry_level = validator.is_entry_level(user_data, experience)
        
        # Use extracted skills (ONLY if user provided them)
        job_skills = skills.get("job_related_skills", []) or []
        hard_skills = extracted_data.get("hard_skills", [])[:3]
        top_skills = ", ".join(hard_skills) if hard_skills else ", ".join(job_skills[:3]) if job_skills else "various skills"
        
        # CRITICAL: Do NOT use impact statements in summary - they belong in Experience
        # Summary should be general, not story-like
        
        # Entry-level summaries
        if is_entry_level or "student" in role or "graduate" in role:
            if top_skills and top_skills != "various skills":
                return f"Motivated {role} with foundational knowledge in {top_skills}. Seeking opportunities to apply academic learning and contribute to real-world projects. Eager to learn and grow in a professional environment."
            else:
                return f"Motivated {role} seeking opportunities to apply academic knowledge and gain practical experience. Strong willingness to learn and contribute to team success."
        
        # Experienced summaries (but still NO metrics or stories)
        if "founder" in role:
            if years_exp > 0:
                return f"Entrepreneurial founder with experience in building and scaling startups. Expertise in {top_skills}. Verified credentials and commitment to innovation."
            else:
                return f"Entrepreneurial founder with expertise in {top_skills}. Verified credentials and commitment to innovation."
        
        if "investor" in role:
            return f"Experienced investor with expertise in {top_skills} and blockchain technology. Focused on supporting innovative startups."
        
        # Default professional summary (NO metrics, NO stories)
        if years_exp > 0:
            return f"Professional with experience in {top_skills}. Verified credentials and commitment to excellence."
        else:
            return f"Professional with expertise in {top_skills}. Seeking opportunities to contribute and grow."
    
    def _format_education_europass(self, certificates: list, additional_education: list) -> list:
        """Format education section in Europass format."""
        education = []
        
        for cert in certificates:
            is_verified = cert.get("verified") == "verified"
            education.append({
                "dates": str(cert.get("graduation_year", "")),
                "title": cert.get("major", "Degree"),
                "organization": cert.get("university", ""),
                "level": "Higher Education",
                "verified": is_verified,
                "blockchain_proof": cert.get("transaction_signature") if is_verified else None
            })
        
        for edu in additional_education:
            education.append({
                "dates": edu.get("dates", ""),
                "title": edu.get("title", ""),
                "organization": edu.get("institution", ""),
                "level": edu.get("level", ""),
                "verified": False
            })
        
        return sorted(education, key=lambda x: x.get("dates", ""), reverse=True)
    
    def _format_skills_europass(self, skills: Dict[str, Any]) -> Dict[str, Any]:
        """Format skills in Europass format."""
        return {
            "mother_tongue": skills.get("mother_tongue", ""),
            "other_languages": skills.get("other_languages", []),
            "social_skills": skills.get("social_skills", []),
            "organizational_skills": skills.get("organizational_skills", []),
            "job_related_skills": skills.get("job_related_skills", []),
            "computer_skills": skills.get("computer_skills", []),
            "driving_licence": skills.get("driving_licence", "")
        }
    
    def _calculate_cv_score(self, cv_data: Dict[str, Any]) -> float:
        """Calculate comprehensive CV quality score."""
        score = 0.0
        
        # Personal info (20 points)
        personal = cv_data.get("personal_info", {})
        if personal.get("full_name"):
            score += 5
        if personal.get("email"):
            score += 5
        if personal.get("wallet_address"):
            score += 5
        if personal.get("phone"):
            score += 5
        
        # Summary quality (20 points)
        summary = cv_data.get("summary", "")
        if summary and len(summary) > 50:
            score += 15
        if "results" in summary.lower() or "achieved" in summary.lower():
            score += 5
        
        # Education (20 points)
        education = cv_data.get("education", [])
        if education:
            score += min(20, len(education) * 7)
        
        # Experience with impact (25 points)
        experience = cv_data.get("work_experience", [])
        if experience:
            score += min(20, len(experience) * 7)
            # Bonus for quantified achievements
            exp_text = str(experience).lower()
            if re.search(r'\d+%?|\$\d+', exp_text):
                score += 5
        
        # Skills (10 points)
        skills = cv_data.get("personal_skills", {}).get("job_related_skills", [])
        if skills:
            score += min(10, len(skills) * 2)
        
        # Blockchain verification removed - no longer part of core solution
        
        # ATS optimization bonus (5 points)
        if cv_data.get("ats_optimized"):
            score += 5
        
        return round(min(100, score), 2)
    
    def suggest_powerful_language(self, section: str, content: str) -> List[str]:
        """Suggest powerful language alternatives."""
        suggestions = {
            "summary": [
                "Results-driven professional with proven track record",
                "Dynamic leader with expertise in",
                "Strategic thinker with demonstrated success in",
                "Innovative problem-solver specializing in",
            ],
            "experience": [
                "Led and executed projects that increased efficiency by 30%",
                "Spearheaded initiatives resulting in measurable business growth",
                "Delivered measurable results including",
                "Collaborated cross-functionally to achieve",
                "Optimized processes leading to cost savings",
            ],
            "skills": [
                "Proficient in",
                "Expert-level knowledge of",
                "Advanced skills in",
                "Certified in",
            ],
        }
        return suggestions.get(section, [])
    
    def get_formatting_tips(self, section: str) -> List[str]:
        """Get formatting tips for CV sections."""
        tips = {
            "summary": [
                "Keep it concise (2-3 sentences)",
                "Highlight your key strengths",
                "Mention years of experience if relevant",
                "Include your career objective",
            ],
            "experience": [
                "Use bullet points for clarity",
                "Start with action verbs (Led, Delivered, Achieved)",
                "Quantify achievements with numbers and percentages",
                "Focus on results, not just duties",
            ],
            "skills": [
                "Group related skills together",
                "List most relevant skills first",
                "Include both technical and soft skills",
                "Be specific (e.g., 'Python' not 'Programming')",
            ],
        }
        return tips.get(section, [])
    
    def get_realtime_suggestions(self, section: str, current_text: str, industry: str = None) -> Dict[str, Any]:
        """
        Provide real-time AI suggestions as user types.
        
        Uses Mistral AI API with quality validation and retry logic.
        """
        from app.services.suggestion_validator import SuggestionValidator
        
        suggestions = {
            "improvements": [],
            "examples": [],
            "recommendations": []
        }
        
        if not current_text or len(current_text) < 10:
            return suggestions
        
        validator = SuggestionValidator()
        
        # Try Mistral AI API if key is available and text is substantial
        if self.mistral_key and len(current_text) > 20:
            for attempt in range(validator.MAX_RETRIES):
                try:
                    from mistralai import Mistral
                    client = Mistral(api_key=self.mistral_key)
                    
                    # Enhanced prompt with explicit quality requirements
                    prompt = f"""You are an expert CV writer. Analyze this CV {section} text and provide detailed, professional suggestions.

Text to analyze: {current_text}
Industry context: {industry or "General"}

REQUIREMENTS (STRICT - FOLLOW ALL):
1. Each suggestion MUST be at least 2-3 COMPLETE sentences (80+ characters, 12+ words)
2. Use SPECIFIC examples and STRONG action verbs (Led, Delivered, Achieved, Created, Improved, Managed, Developed, Executed, Spearheaded, Implemented)
3. Be context-aware based on the role and industry - reference the actual text provided
4. NO spelling mistakes or grammar errors - proofread before responding
5. NO placeholder text, vague statements, or generic advice
6. Include quantifiable metrics where relevant (numbers, percentages, scale)
7. Be professional, ATS-optimized, and industry-appropriate
8. Write in complete sentences with proper punctuation
9. Make each suggestion actionable and specific to the CV text provided

EXAMPLE OF GOOD SUGGESTION (80+ characters, 12+ words):
"Led a cross-functional team of 5 developers to deliver a customer-facing web application that increased user engagement by 40% within 3 months. Implemented agile methodologies and CI/CD pipelines, reducing deployment time by 50%. Collaborated with product managers to define requirements and prioritize features based on user feedback and business metrics."

EXAMPLE OF BAD SUGGESTION (TOO SHORT):
"Worked on projects." ❌ TOO SHORT AND VAGUE

Provide suggestions in JSON format:
{{
    "improvements": [
        {{
            "weak": "phrase to replace",
            "strong": "detailed, professional alternative with specific examples (minimum 80 characters, 12+ words, 2-3 sentences)",
            "context": "explanation of why this is better (minimum 30 characters)"
        }}
    ],
    "recommendations": [
        "Detailed recommendation 1 with specific examples and actionable advice (minimum 80 characters, 12+ words, 2-3 sentences)",
        "Detailed recommendation 2 with specific examples and actionable advice (minimum 80 characters, 12+ words, 2-3 sentences)"
    ]
}}

CRITICAL: Each recommendation must be a complete, detailed statement (2-3 sentences minimum, 80+ characters, 12+ words). Never return short, vague suggestions. Proofread for spelling and grammar before responding."""
                    
                    response = client.chat.complete(
                        model="mistral-small-latest",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a professional CV writing expert. Provide detailed, context-aware, error-free suggestions in JSON format only. Each suggestion must be 2-3 complete sentences minimum (80+ characters, 12+ words). Use strong action verbs, specific examples, and quantifiable metrics. Never use markdown formatting - return pure JSON only. Proofread for spelling and grammar before responding. Never return short, vague, or generic suggestions."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2000,  # Increased for longer, detailed suggestions
                        temperature=0.4,  # Balanced for quality and consistency
                        timeout=5.0  # Increased timeout for better quality
                    )
                    
                    content = response.choices[0].message.content.strip()
                    
                    # Strip all markdown formatting
                    content = re.sub(r'```json\s*', '', content)
                    content = re.sub(r'```\s*', '', content)
                    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
                    content = re.sub(r'\*(.*?)\*', r'\1', content)  # Italic
                    content = re.sub(r'`(.*?)`', r'\1', content)  # Code
                    content = content.strip()
                    
                    # Try to extract JSON from response
                    try:
                        # If response is wrapped in markdown code blocks, extract it
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                        
                        # Try to find JSON object
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            content = json_match.group()
                        
                        ai_suggestions = json.loads(content)
                        
                        # Strip markdown from all text fields
                        def strip_markdown_from_dict(d):
                            if isinstance(d, dict):
                                return {k: strip_markdown_from_dict(v) for k, v in d.items()}
                            elif isinstance(d, list):
                                return [strip_markdown_from_dict(item) for item in d]
                            elif isinstance(d, str):
                                return re.sub(r'\*\*(.*?)\*\*', r'\1', re.sub(r'\*(.*?)\*', r'\1', re.sub(r'`(.*?)`', r'\1', d)))
                            return d
                        
                        ai_suggestions = strip_markdown_from_dict(ai_suggestions)
                        
                        # VALIDATE QUALITY: Check recommendations before accepting
                        recommendations = ai_suggestions.get("recommendations", [])
                        valid_recommendations = validator.filter_valid_suggestions(recommendations, field=section, min_valid=2)
                        
                        # VALIDATE QUALITY: Check improvements
                        improvements = ai_suggestions.get("improvements", [])
                        valid_improvements = []
                        for imp in improvements:
                            if isinstance(imp, dict):
                                strong_text = imp.get("strong", "")
                                is_valid, issues = validator.validate_suggestion(strong_text, section)
                                if is_valid:
                                    valid_improvements.append(imp)
                                else:
                                    logger.warning(f"Filtered invalid improvement: {', '.join(issues)}")
                        
                        # Only accept if we have valid suggestions
                        if len(valid_recommendations) >= 2 or len(valid_improvements) >= 1:
                            suggestions["improvements"] = valid_improvements
                            suggestions["recommendations"] = valid_recommendations
                            logger.info(f"AI-generated {len(valid_recommendations)} valid recommendations and {len(valid_improvements)} valid improvements for {section} section")
                            break  # Success - exit retry loop
                        else:
                            logger.warning(f"Attempt {attempt + 1}: AI suggestions failed quality validation. Retrying...")
                            if attempt < validator.MAX_RETRIES - 1:
                                continue  # Retry
                            else:
                                logger.error(f"All {validator.MAX_RETRIES} attempts failed quality validation. Using fallback.")
                                # Fall through to rule-based suggestions
                                
                    except json.JSONDecodeError as e:
                        logger.warning(f"Attempt {attempt + 1}: Failed to parse AI response as JSON: {content[:100]}")
                        if attempt < validator.MAX_RETRIES - 1:
                            continue  # Retry
                        else:
                            logger.error("All retry attempts failed JSON parsing. Using fallback.")
                            # Fall through to rule-based suggestions
                    except Exception as e:
                        logger.error(f"Attempt {attempt + 1}: Mistral AI API error: {str(e)}")
                        if attempt < validator.MAX_RETRIES - 1:
                            continue  # Retry
                        else:
                            logger.error("All retry attempts failed. Using fallback.")
                            # Fall through to rule-based suggestions
                except ImportError:
                    logger.warning("Mistral AI library not installed, using rule-based suggestions")
                    break  # Exit retry loop
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1}: Mistral AI API error: {str(e)}")
                    if attempt < validator.MAX_RETRIES - 1:
                        continue  # Retry
                    else:
                        logger.error("All retry attempts failed. Using fallback.")
                        # Fall through to rule-based suggestions
        
        # Fallback to rule-based analysis
        text_lower = current_text.lower()
        
        # Check for weak language
        weak_phrases = {
            "worked on": "Executed and delivered",
            "helped with": "Collaborated to achieve",
            "was responsible": "Spearheaded",
            "did some": "Implemented",
            "i did": "Delivered",
            "my job was": "Key responsibilities included",
            "worked": "Executed",
            "helped": "Collaborated",
            "made": "Created",
            "got": "Achieved"
        }
        
        for weak, strong in weak_phrases.items():
            if weak in text_lower and not any(imp.get("weak") == weak for imp in suggestions["improvements"]):
                suggestions["improvements"].append({
                    "weak": weak,
                    "strong": strong,
                    "context": f"Replace '{weak}' with '{strong}' for more impact"
                })
        
        # Check for missing quantifiers
        if section == "experience" and not re.search(r'\d+', current_text):
            if not any("quantify" in rec.lower() for rec in suggestions["recommendations"]):
                suggestions["recommendations"].append("Add numbers or percentages to quantify your achievements (e.g., 'increased sales by 30%', 'managed team of 5')")
        
        # Check for action verbs
        action_verbs = ["led", "delivered", "achieved", "created", "improved", "managed", "developed", "executed", "spearheaded"]
        has_action_verb = any(verb in text_lower for verb in action_verbs)
        if not has_action_verb and section == "experience":
            if not any("action verb" in rec.lower() for rec in suggestions["recommendations"]):
                suggestions["recommendations"].append("Start with an action verb (e.g., 'Led', 'Delivered', 'Achieved', 'Developed')")
        
        # Check for first person
        if re.search(r'\b(I|my|me)\b', current_text, re.IGNORECASE):
            suggestions["recommendations"].append("Remove first-person pronouns (I, my, me) for a more professional tone")
        
        # Industry-specific suggestions
        if industry:
            industry_examples = self._get_industry_examples(section, industry)
            suggestions["examples"].extend(industry_examples)
        
        return suggestions
    
    def _get_industry_examples(self, section: str, industry: str) -> List[str]:
        """Get industry-specific examples for a section."""
        examples = {
            "Technology": {
                "experience": [
                    "Developed scalable web applications using React and Node.js, serving 10,000+ daily users",
                    "Led a team of 5 developers to deliver a mobile app that increased user engagement by 40%",
                    "Optimized database queries reducing response time by 60%"
                ],
                "summary": [
                    "Software engineer with 3+ years of experience in full-stack development, specializing in React, Node.js, and cloud technologies",
                    "Results-driven developer with expertise in building scalable applications and leading cross-functional teams"
                ]
            },
            "Healthcare": {
                "experience": [
                    "Managed patient care for 50+ patients daily, ensuring compliance with medical protocols",
                    "Collaborated with multidisciplinary team to improve patient outcomes by 25%",
                    "Maintained accurate medical records using electronic health systems"
                ],
                "summary": [
                    "Dedicated healthcare professional with expertise in patient care and medical administration",
                    "Compassionate nurse with proven track record in improving patient satisfaction scores"
                ]
            },
            "Education": {
                "experience": [
                    "Developed and implemented curriculum for 120+ students, improving test scores by 30%",
                    "Led after-school programs that increased student participation by 50%",
                    "Collaborated with parents and administrators to enhance learning outcomes"
                ],
                "summary": [
                    "Passionate educator with expertise in curriculum development and student engagement",
                    "Dedicated teacher with proven ability to improve student performance and foster learning"
                ]
            }
        }
        
        return examples.get(industry, {}).get(section, [])
    
    def get_university_prompts(self) -> Dict[str, List[str]]:
        """Get prompts to help translate university experience into professional language."""
        return {
            "projects": [
                "What projects did you complete during your studies?",
                "Describe a major project or thesis you worked on",
                "What technical skills did you use in your projects?",
                "What problems did your projects solve?"
            ],
            "coursework": [
                "How did your coursework prepare you for this role?",
                "What relevant courses did you take?",
                "What practical skills did you gain from your courses?",
                "How does your academic background relate to this position?"
            ],
            "skills": [
                "What skills did you gain from your degree?",
                "What technical tools did you learn in university?",
                "What soft skills did you develop through group projects?",
                "What certifications or training did you complete?"
            ],
            "achievements": [
                "Did you receive any academic awards or honors?",
                "Were you part of any student organizations?",
                "Did you participate in any competitions or hackathons?",
                "What leadership roles did you have in university?"
            ]
        }
    
    def calculate_ats_score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive ATS compatibility score.
        
        Returns:
            Score (0-100), issues, and specific fixes
        """
        score = 100
        issues = []
        fixes = []
        
        # Check section completeness (20 points)
        required_sections = ["summary", "work_experience", "education", "personal_skills"]
        missing_sections = [s for s in required_sections if not cv_data.get(s)]
        if missing_sections:
            score -= len(missing_sections) * 5
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            fixes.append(f"Add the following sections: {', '.join(missing_sections)}")
        
        # Check formatting (30 points)
        formatting_score = self._check_ats_formatting(cv_data)
        if formatting_score < 90:
            score -= (90 - formatting_score) * 0.3
            issues.append("Formatting issues detected")
            fixes.append("Remove special characters, use plain text formatting")
        
        # Check keywords (25 points)
        keyword_density = self._calculate_keyword_density(cv_data)
        if keyword_density < 2.0:
            score -= 10
            issues.append("Low keyword density")
            fixes.append("Add more industry-relevant keywords to your CV")
        
        # Check action verbs (15 points)
        experience = cv_data.get("work_experience", [])
        has_action_verbs = False
        for exp in experience:
            desc = exp.get("description", "").lower()
            if any(verb in desc for verb in ["led", "delivered", "achieved", "created", "improved"]):
                has_action_verbs = True
                break
        if not has_action_verbs and experience:
            score -= 15
            issues.append("Missing action verbs in experience descriptions")
            fixes.append("Start each bullet point with an action verb (Led, Delivered, Achieved)")
        
        # Check quantifiers (10 points)
        has_numbers = False
        for exp in experience:
            if re.search(r'\d+', exp.get("description", "")):
                has_numbers = True
                break
        if not has_numbers and experience:
            score -= 10
            issues.append("Missing quantifiable achievements")
            fixes.append("Add numbers, percentages, or metrics to your achievements")
        
        # Calculate section-level scores and feedback
        section_scores = {}
        section_feedback = {}
        
        # Summary section
        summary = cv_data.get("summary", "")
        if summary:
            summary_score = min(20, len(summary.split()) / 5)  # 20 points for good summary
            section_scores["summary"] = summary_score
            if len(summary.split()) < 50:
                section_feedback["summary"] = "Summary is too short. Aim for 50-100 words."
            else:
                section_feedback["summary"] = "Summary length is good."
        else:
            section_scores["summary"] = 0
            section_feedback["summary"] = "Missing professional summary."
        
        # Experience section
        experience = cv_data.get("work_experience", cv_data.get("experience", []))
        if experience and len(experience) > 0:
            exp_score = min(25, len(experience) * 5)  # 25 points for experience
            # Check for action verbs and quantifiers
            action_verb_count = sum(1 for exp in experience if any(v in exp.get("description", "").lower() 
                for v in ["led", "delivered", "achieved", "created", "improved", "managed", "developed"]))
            quantifier_count = sum(1 for exp in experience if re.search(r'\d+', exp.get("description", "")))
            section_scores["experience"] = exp_score
            section_feedback["experience"] = f"{len(experience)} positions found. {action_verb_count} with action verbs, {quantifier_count} with quantifiers."
        else:
            section_scores["experience"] = 0
            section_feedback["experience"] = "No work experience found."
        
        # Education section
        education = cv_data.get("education", [])
        if education and len(education) > 0:
            edu_score = min(15, len(education) * 7)  # 15 points for education
            section_scores["education"] = edu_score
            section_feedback["education"] = f"{len(education)} education entries found."
        else:
            section_scores["education"] = 0
            section_feedback["education"] = "No education entries found."
        
        # Skills section
        skills = cv_data.get("personal_skills", cv_data.get("skills", {}))
        if isinstance(skills, dict):
            tech_skills = skills.get("technical", skills.get("job_related_skills", skills.get("technical_skills", [])))
            soft_skills = skills.get("soft", skills.get("social_skills", []))
            total_skills = len(tech_skills) + len(soft_skills)
            skills_score = min(20, total_skills * 2)  # 20 points for skills
            section_scores["skills"] = skills_score
            section_feedback["skills"] = f"{len(tech_skills)} technical skills, {len(soft_skills)} soft skills found."
        else:
            section_scores["skills"] = 0
            section_feedback["skills"] = "No skills found."
        
        # Extract keywords found and missing
        common_keywords = ["experience", "skills", "education", "achievement", "leadership", "project", "team", "results"]
        cv_text = json.dumps(cv_data).lower()
        found_keywords = [kw for kw in common_keywords if kw in cv_text]
        missing_keywords = [kw for kw in common_keywords if kw not in cv_text]
        
        return {
            "score": max(0, min(100, int(score))),
            "issues": issues,
            "fixes": fixes,
            "formatting_score": formatting_score,
            "keyword_density": keyword_density,
            "recommendations": self._generate_ats_recommendations(cv_data),
            "section_scores": section_scores,
            "section_feedback": section_feedback,
            "keywords_found": found_keywords,
            "keywords_missing": missing_keywords,
            "section_completeness": {
                "summary": bool(summary),
                "experience": len(experience) > 0,
                "education": len(education) > 0,
                "skills": total_skills > 0 if isinstance(skills, dict) else False
            }
        }
    
    def get_industry_template(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific CV template structure."""
        templates = {
            "Technology": {
                "sections_order": ["summary", "technical_skills", "work_experience", "education", "projects", "certifications"],
                "emphasis": ["technical_skills", "projects"],
                "keywords": ["software development", "agile", "cloud computing", "api", "devops", "full-stack"]
            },
            "Healthcare": {
                "sections_order": ["summary", "work_experience", "education", "certifications", "skills"],
                "emphasis": ["work_experience", "certifications"],
                "keywords": ["patient care", "medical records", "HIPAA", "clinical", "healthcare systems"]
            },
            "Education": {
                "sections_order": ["summary", "education", "work_experience", "certifications", "skills"],
                "emphasis": ["education", "certifications"],
                "keywords": ["curriculum development", "pedagogy", "student engagement", "assessment"]
            },
            "Finance": {
                "sections_order": ["summary", "work_experience", "education", "certifications", "skills"],
                "emphasis": ["work_experience", "certifications"],
                "keywords": ["financial analysis", "risk management", "compliance", "accounting"]
            },
            "Agriculture": {
                "sections_order": ["summary", "work_experience", "education", "skills", "projects"],
                "emphasis": ["work_experience", "projects"],
                "keywords": ["sustainable farming", "crop management", "agribusiness", "rural development"]
            }
        }
        
        return templates.get(industry, templates["Technology"])
    
    def parse_and_structure_cv(self, cv_text: str, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Parse raw CV text and structure it into our CV format.
        
        Uses pattern matching and AI-like logic to extract:
        - Personal information
        - Work experience
        - Education
        - Skills
        - Awards, projects, etc.
        """
        logger.info(f"Parsing CV text for user {user_id}")
        
        # Initialize structured data
        structured = {
            "personal_info": {
                "surname": "",
                "first_name": "",
                "address": "",
                "phone": "",
                "email": "",
                "nationality": "",
                "date_of_birth": "",
                "gender": "",
            },
            "experience": [],
            "education": [],
            "skills": {
                "mother_tongue": "",
                "other_languages": [],
                "social_skills": [],
                "organizational_skills": [],
                "job_related_skills": [],
                "computer_skills": [],
                "driving_licence": "",
            },
            "awards": [],
            "publications": [],
            "projects": [],
            "memberships": [],
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, cv_text)
        if emails:
            structured["personal_info"]["email"] = emails[0]
        
        # Extract phone
        phone_patterns = [
            r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\+232\s?\d{2}\s?\d{3}\s?\d{4}',  # Sierra Leone format
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, cv_text)
            if phones:
                structured["personal_info"]["phone"] = phones[0]
                break
        
        # Extract name (usually at the top)
        lines = cv_text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line and not any(char.isdigit() for char in line):
                name_parts = line.split()
                if len(name_parts) >= 2:
                    structured["personal_info"]["first_name"] = name_parts[0]
                    structured["personal_info"]["surname"] = " ".join(name_parts[1:])
                    break
        
        # Extract experience (look for common patterns)
        experience_section = self._extract_section(cv_text, ["experience", "work experience", "employment", "career"])
        if experience_section:
            structured["experience"] = self._parse_experience(experience_section)
        
        # Extract education
        education_section = self._extract_section(cv_text, ["education", "qualifications", "academic"])
        if education_section:
            structured["education"] = self._parse_education(education_section)
        
        # Extract skills
        skills_section = self._extract_section(cv_text, ["skills", "competencies", "abilities"])
        if skills_section:
            structured["skills"] = self._parse_skills(skills_section)
        
        # Extract projects
        projects_section = self._extract_section(cv_text, ["projects", "project"])
        if projects_section:
            structured["projects"] = self._parse_list_items(projects_section)
        
        # Extract awards
        awards_section = self._extract_section(cv_text, ["awards", "achievements", "honors"])
        if awards_section:
            structured["awards"] = self._parse_list_items(awards_section)
        
        logger.info(f"Parsed CV: {len(structured['experience'])} experiences, {len(structured['education'])} education entries")
        return structured
    
    def _extract_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract a section from CV text based on keywords."""
        text_lower = text.lower()
        for keyword in keywords:
            pattern = rf'\b{keyword}\b'
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Get text from this section to next section or end
                start_idx = match.end()
                # Find next section header (all caps or bold patterns)
                next_section = re.search(r'\n[A-Z][A-Z\s]{3,}\n', text[start_idx:])
                if next_section:
                    return text[start_idx:start_idx + next_section.start()].strip()
                return text[start_idx:].strip()
        return None
    
    def _parse_experience(self, text: str) -> List[Dict[str, Any]]:
        """Parse work experience from text."""
        experiences = []
        # Look for job titles and companies
        lines = text.split('\n')
        current_exp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a job title/company line
            if re.match(r'^[A-Z][a-zA-Z\s&]+$', line) and len(line) < 50:
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    "title": line,
                    "company": "",
                    "duration": "",
                    "description": ""
                }
            elif current_exp:
                # Check for date patterns (duration)
                if re.search(r'\d{4}|\d{1,2}[/-]\d{4}', line):
                    current_exp["duration"] = line
                elif not current_exp["company"] and len(line) < 50:
                    current_exp["company"] = line
                else:
                    current_exp["description"] += line + " "
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences[:10]  # Limit to 10 experiences
    
    def _parse_education(self, text: str) -> List[Dict[str, Any]]:
        """Parse education from text."""
        education = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree patterns
            degree_patterns = [r'\b(BSc|BA|MSc|MA|PhD|Bachelor|Master|Doctorate)\b', r'\b(University|College|Institute)\b']
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns):
                education.append({
                    "title": line,
                    "institution": "",
                    "year": ""
                })
        
        return education[:10]
    
    def _parse_skills(self, text: str) -> Dict[str, Any]:
        """Parse skills from text."""
        skills = {
            "job_related_skills": [],
            "computer_skills": [],
            "other_languages": []
        }
        
        # Common skill keywords
        tech_skills = ["python", "javascript", "java", "react", "node", "sql", "html", "css", "git", "docker", "aws", "linux"]
        languages = ["english", "french", "spanish", "arabic", "krio", "temne", "mende"]
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        for word in words:
            if word in tech_skills:
                skills["computer_skills"].append(word.title())
            elif word in languages:
                skills["other_languages"].append(word.title())
            elif len(word) > 3:
                skills["job_related_skills"].append(word.title())
        
        # Remove duplicates
        skills["job_related_skills"] = list(set(skills["job_related_skills"]))[:20]
        skills["computer_skills"] = list(set(skills["computer_skills"]))[:15]
        skills["other_languages"] = list(set(skills["other_languages"]))[:10]
        
        return skills
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items (projects, awards, etc.) from text."""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove bullet points and numbering
            line = re.sub(r'^[•\-\*\d+\.\)]\s*', '', line)
            if line and len(line) > 10:
                items.append(line)
        
        return items[:10]
    
    def tailor_parsed_cv(self, parsed_cv: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Enhance parsed CV with AI improvements.
        - Enhance language in experience descriptions
        - Optimize for ATS
        - Add missing quantifiers
        - Improve formatting
        """
        logger.info("Tailoring parsed CV with AI enhancements")
        
        tailored = parsed_cv.copy()
        
        # Enhance experience descriptions
        # CRITICAL: Extract user_data and experience from parsed_cv to prevent hallucinations
        user_data_from_cv = {
            "role": tailored.get("personal_info", {}).get("role", "professional"),
            "full_name": tailored.get("personal_info", {}).get("full_name", ""),
        }
        experience_from_cv = tailored.get("experience", [])
        
        for exp in experience_from_cv:
            if exp.get("description"):
                enhanced = self.enhance_language(
                    exp["description"], 
                    "experience",
                    user_data=user_data_from_cv,
                    experience=experience_from_cv
                )
                exp["description"] = enhanced
        
        # Enhance skills formatting
        if tailored.get("skills"):
            # Ensure skills are properly categorized
            all_skills = []
            for category in ["job_related_skills", "computer_skills"]:
                all_skills.extend(tailored["skills"].get(category, []))
            
            # Remove duplicates and standardize
            tailored["skills"]["job_related_skills"] = list(set(all_skills[:15]))
        
        # Add recommendations
        tailored["ai_recommendations"] = self._generate_parsing_recommendations(tailored)
        
        return tailored
    
    def _generate_parsing_recommendations(self, cv_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the parsed CV."""
        recommendations = []
        
        if not cv_data.get("experience"):
            recommendations.append("Add work experience with quantifiable achievements")
        
        if not cv_data.get("education"):
            recommendations.append("Include your educational qualifications")
        
        if not cv_data.get("skills", {}).get("job_related_skills"):
            recommendations.append("List your key skills and competencies")
        
        # Check for quantifiers in experience
        has_numbers = False
        for exp in cv_data.get("experience", []):
            if re.search(r'\d+', exp.get("description", "")):
                has_numbers = True
                break
        
        if not has_numbers:
            recommendations.append("Add numbers and percentages to quantify your achievements")
        
        return recommendations
