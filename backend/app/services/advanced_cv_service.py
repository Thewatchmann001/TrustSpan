"""
Advanced CV Service with comprehensive AI features
Includes guided CV creation, job matching, cover letters, ATS optimization, and more
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.utils.logger import logger
from app.core.config import settings
import json
import re
from datetime import datetime


class AdvancedCVService:
    """Advanced CV service with AI-powered features."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY  # Backward compatibility
    
    def generate_cv_from_questions(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate CV from guided questionnaire answers.
        
        Args:
            answers: Dictionary with user responses to guided questions
            
        Returns:
            Generated CV in structured format
        """
        logger.info("Generating CV from questionnaire answers")
        
        if not self.mistral_key:
            return self._generate_cv_fallback(answers)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = self._build_cv_generation_prompt(answers)
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert CV writer and ATS optimization specialist. 
                        Generate a professional, ATS-friendly CV in JSON format. 
                        Include quantifiable achievements, action verbs, and industry keywords.
                        Format: {
                            "summary": "professional summary",
                            "personal_info": {...},
                            "experience": [...],
                            "education": [...],
                            "skills": {...},
                            "achievements": [...],
                            "certifications": [...]
                        }"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            cv_data = self._extract_json(content)
            
            return {
                "success": True,
                "cv_data": cv_data,
                "text_version": self._format_cv_text(cv_data),
                "ats_score": self._calculate_ats_score(cv_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            return self._generate_cv_fallback(answers)
    
    def match_job_compatibility(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Compute compatibility score between CV and job description.
        
        Returns:
            Compatibility analysis with score, missing skills, recommendations
        """
        logger.info("Computing job compatibility")
        
        if not self.mistral_key:
            return self._match_job_fallback(cv_data, job_description)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            cv_summary = json.dumps(cv_data, indent=2)
            
            prompt = f"""Analyze the compatibility between this CV and job description.

CV Data:
{cv_summary}

Job Description:
{job_description}

Provide analysis in JSON format:
{{
    "compatibility_score": 0-100,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "matched_experience": "years of relevant experience",
    "missing_qualifications": ["qualification1"],
    "recommendations": [
        "specific bullet point to add",
        "skill to highlight",
        "experience to emphasize"
    ],
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}}"""
            
            # Apply 15-second timeout to AI call
            from cv.timeout_utils import safe_execute_with_timeout
            
            def _make_ai_call():
                return client.chat.complete(
                    model="mistral-medium-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a recruitment expert. Analyze CV-job compatibility objectively."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
            
            response = safe_execute_with_timeout(
                _make_ai_call,
                timeout_seconds=15,
                fallback=None
            )
            
            if response is None:
                logger.warning("AI call timed out - using fallback")
                return self._match_job_fallback(cv_data, job_description)
            
            content = response.choices[0].message.content.strip()
            analysis = self._extract_json(content)
            
            return {
                "success": True,
                "analysis": analysis,
                "score": analysis.get("compatibility_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error matching job: {e}")
            return self._match_job_fallback(cv_data, job_description)
    
    def generate_job_optimized_cv(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Generate a job-optimized version of the CV"""
        logger.info("Generating job-optimized CV")
        
        compatibility = self.match_job_compatibility(cv_data, job_description)
        recommendations = compatibility.get("analysis", {}).get("recommendations", [])
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Optimize this CV for the specific job description.

Original CV:
{json.dumps(cv_data, indent=2)}

Job Description:
{job_description}

Optimization Recommendations:
{json.dumps(recommendations, indent=2)}

Create an optimized version that:
1. Incorporates missing keywords from job description
2. Highlights relevant experience more prominently
3. Adds recommended skills/qualifications
4. Rewrites bullets to match job requirements
5. Maintains authenticity and truthfulness

Return optimized CV in same JSON format."""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CV optimization expert. Create job-tailored CVs that are truthful and effective."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            optimized_cv = self._extract_json(content)
            
            return {
                "success": True,
                "optimized_cv": optimized_cv,
                "changes_made": recommendations,
                "original_score": compatibility.get("score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing CV: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_cover_letter(self, cv_data: Dict[str, Any], job_description: str, company_name: str = "") -> Dict[str, Any]:
        """Generate personalized cover letter"""
        logger.info("Generating cover letter")
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Write a professional, personalized cover letter.

CV Information:
{json.dumps(cv_data, indent=2)}

Job Description:
{job_description}

Company: {company_name}

Requirements:
1. Professional tone, 3-4 paragraphs
2. Highlight relevant experience from CV
3. Show enthusiasm for the role
4. Connect skills to job requirements
5. Include specific examples
6. Professional closing

Generate the cover letter text."""
            
            # Use mistral-small-latest to avoid rate limits (429 errors)
            # Fallback to mistral-medium if small fails
            # Apply 15-second timeout
            from cv.timeout_utils import safe_execute_with_timeout
            
            def _make_cover_letter_call(model_name):
                return client.chat.complete(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional cover letter writer. Create compelling, personalized cover letters. Never use markdown formatting - return plain text only."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
            
            try:
                response = safe_execute_with_timeout(
                    lambda: _make_cover_letter_call("mistral-small-latest"),
                    timeout_seconds=15,
                    fallback=None
                )
                if response is None:
                    raise Exception("Timeout on mistral-small-latest")
            except Exception as small_error:
                logger.warning(f"mistral-small-latest failed, trying mistral-medium-latest: {str(small_error)}")
                # Retry with medium model
                import time
                time.sleep(2)  # Wait 2 seconds before retry
                response = safe_execute_with_timeout(
                    lambda: _make_cover_letter_call("mistral-medium-latest"),
                    timeout_seconds=15,
                    fallback=None
                )
                if response is None:
                    logger.error("Cover letter generation timed out - returning fallback")
                    return {"success": False, "message": "Cover letter generation timed out. Please try again."}
            
            cover_letter = response.choices[0].message.content.strip()
            
            # Strip markdown formatting
            import re
            cover_letter = re.sub(r'\*\*(.*?)\*\*', r'\1', cover_letter)  # Bold
            cover_letter = re.sub(r'\*(.*?)\*', r'\1', cover_letter)  # Italic
            cover_letter = re.sub(r'`(.*?)`', r'\1', cover_letter)  # Code
            cover_letter = re.sub(r'#{1,6}\s+', '', cover_letter)  # Headers
            cover_letter = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cover_letter)  # Links
            cover_letter = cover_letter.strip()
            
            return {
                "success": True,
                "cover_letter": cover_letter,
                "word_count": len(cover_letter.split())
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_skills_from_cv(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize skills from CV"""
        skills = {
            "hard_skills": [],
            "soft_skills": [],
            "tools": [],
            "languages": [],
            "certifications": []
        }
        
        # Extract from skills section
        if "skills" in cv_data:
            skills_data = cv_data["skills"]
            skills["hard_skills"].extend(skills_data.get("technical", []))
            skills["soft_skills"].extend(skills_data.get("soft", []))
            skills["tools"].extend(skills_data.get("tools", []))
            skills["languages"].extend(skills_data.get("languages", []))
        
        # Extract from experience
        if "experience" in cv_data:
            for exp in cv_data["experience"]:
                description = exp.get("description", "").lower()
                # Simple keyword extraction
                tech_keywords = ["python", "javascript", "react", "node", "sql", "aws", "docker"]
                for keyword in tech_keywords:
                    if keyword in description and keyword not in skills["hard_skills"]:
                        skills["hard_skills"].append(keyword)
        
        return skills
    
    def generate_interview_questions(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Generate interview questions based on CV and job description"""
        logger.info("Generating interview questions")
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            # OPTIMIZE: Extract only relevant CV data to reduce prompt size
            # Don't send entire CV JSON - only send what's needed for questions
            summary = cv_data.get("summary", "")[:300]  # Limit summary length
            personal_info = cv_data.get("personal_info", {})
            name = personal_info.get("full_name", personal_info.get("first_name", "Candidate"))
            
            # Extract key experience (titles and companies only, not full descriptions)
            experience_summary = []
            for exp in cv_data.get("experience", [])[:5]:  # Limit to 5 most recent
                exp_summary = {
                    "title": exp.get("job_title", exp.get("title", "")),
                    "company": exp.get("company", ""),
                    "duration": f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
                }
                experience_summary.append(exp_summary)
            
            # Extract skills
            skills_data = cv_data.get("personal_skills", cv_data.get("skills", {}))
            technical_skills = skills_data.get("job_related_skills", [])[:10]  # Top 10 skills
            if not technical_skills:
                technical_skills = skills_data.get("technical", [])[:10]
            
            # Build optimized prompt (much smaller)
            prompt = f"""Generate interview questions for this candidate and role.

Candidate: {name}
Summary: {summary}
Key Experience: {json.dumps(experience_summary, indent=2)}
Skills: {', '.join(technical_skills) if technical_skills else 'Various skills'}

Job Description:
{job_description[:1000]}

Generate:
1. 5 behavioral questions (STAR method)
2. 5 technical questions (if applicable)
3. 3 situational questions
4. Model answers for each (2-3 sentences per answer)

Format as JSON ONLY (no markdown, no code blocks):
{{
    "behavioral": [
        {{"question": "...", "model_answer": "...", "key_points": ["point1", "point2"]}}
    ],
    "technical": [
        {{"question": "...", "model_answer": "...", "key_points": ["point1", "point2"]}}
    ],
    "situational": [
        {{"question": "...", "model_answer": "...", "key_points": ["point1", "point2"]}}
    ]
}}"""
            
            # Use mistral-small-latest to avoid rate limits (429 errors)
            # Fallback to mistral-medium if small fails
            # Increased timeout to 25 seconds for better reliability
            from cv.timeout_utils import safe_execute_with_timeout
            
            def _make_interview_call(model_name):
                return client.chat.complete(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an interview preparation expert. Generate relevant questions and model answers. Return ONLY valid JSON, no markdown, no code blocks, no explanations. Each model answer should be 2-3 sentences."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,  # Slightly lower for more consistent output
                    max_tokens=3000  # Reduced from 4000 - still enough for all questions
                )
            
            try:
                response = safe_execute_with_timeout(
                    lambda: _make_interview_call("mistral-small-latest"),
                    timeout_seconds=25,  # Increased from 15 to 25 seconds
                    fallback=None
                )
                if response is None:
                    raise Exception("Timeout on mistral-small-latest")
            except Exception as small_error:
                logger.warning(f"mistral-small-latest failed, trying mistral-medium-latest: {str(small_error)}")
                # Retry with medium model
                import time
                time.sleep(2)  # Wait 2 seconds before retry
                response = safe_execute_with_timeout(
                    lambda: _make_interview_call("mistral-medium-latest"),
                    timeout_seconds=25,  # Increased from 15 to 25 seconds
                    fallback=None
                )
                if response is None:
                    logger.error("Interview question generation timed out - returning fallback")
                    return {"success": False, "error": "Interview question generation timed out. Please try again."}
            
            content = response.choices[0].message.content.strip()
            questions = self._extract_json(content)
            
            # Check if extraction failed or returned error
            if not questions or (isinstance(questions, dict) and "error" in questions):
                logger.error(f"Failed to extract questions from AI response. Content preview: {content[:200]}")
                return {"success": False, "error": "Failed to generate questions. Please try again with a different job description."}
            
            # Validate questions structure
            if not isinstance(questions, dict):
                logger.error(f"Invalid questions format: {type(questions)}")
                return {"success": False, "error": "Invalid questions format received from AI"}
            
            # Remove any error keys
            if "error" in questions:
                del questions["error"]
            
            # Ensure all required categories exist and are arrays
            if "behavioral" not in questions or not isinstance(questions.get("behavioral"), list):
                questions["behavioral"] = []
            if "technical" not in questions or not isinstance(questions.get("technical"), list):
                questions["technical"] = []
            if "situational" not in questions or not isinstance(questions.get("situational"), list):
                questions["situational"] = []
            
            # Ensure all other categories are also arrays if they exist
            for key in list(questions.keys()):
                if key != "error" and not isinstance(questions[key], list):
                    logger.warning(f"Question category '{key}' is not a list, converting to empty list")
                    questions[key] = []
            
            # Check if we actually got any questions
            total_questions = len(questions.get('behavioral', [])) + len(questions.get('technical', [])) + len(questions.get('situational', []))
            if total_questions == 0:
                logger.error(f"No questions generated. AI response: {content[:500]}")
                return {"success": False, "error": "No questions were generated. Please try again with a more detailed job description."}
            
            logger.info(f"Generated {len(questions.get('behavioral', []))} behavioral, {len(questions.get('technical', []))} technical, {len(questions.get('situational', []))} situational questions")
            
            return {
                "success": True,
                "questions": questions
            }
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            error_msg = str(e)
            # Provide user-friendly error messages
            if "429" in error_msg or "capacity exceeded" in error_msg.lower():
                error_msg = "API rate limit exceeded. Please wait a moment and try again."
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                error_msg = "API authentication failed. Please contact support."
            return {"success": False, "error": error_msg}
    
    def optimize_ats(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive ATS optimization analysis"""
        score = 0
        issues = []
        suggestions = []
        
        # Check formatting
        if not cv_data.get("summary"):
            issues.append("Missing professional summary")
            score -= 10
        else:
            score += 10
        
        # Check keywords
        cv_text = json.dumps(cv_data).lower()
        common_keywords = ["experience", "skills", "education", "achievement"]
        keyword_count = sum(1 for kw in common_keywords if kw in cv_text)
        score += min(keyword_count * 5, 20)
        
        # Check quantifiable achievements
        experience = cv_data.get("experience", [])
        has_metrics = False
        for exp in experience:
            desc = exp.get("description", "").lower()
            if any(char.isdigit() for char in desc):
                has_metrics = True
                break
        
        if has_metrics:
            score += 15
        else:
            issues.append("Missing quantifiable achievements")
            suggestions.append("Add numbers, percentages, or metrics to experience descriptions")
        
        # Check structure
        required_sections = ["personal_info", "experience", "education", "skills"]
        missing_sections = [s for s in required_sections if s not in cv_data]
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            score -= len(missing_sections) * 10
        
        # Final score (0-100)
        score = max(0, min(100, score))
        
        return {
            "ats_score": score,
            "issues": issues,
            "suggestions": suggestions,
            "grade": self._get_ats_grade(score)
        }
    
    def generate_career_recommendations(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate career path recommendations"""
        skills = self.extract_skills_from_cv(cv_data)
        
        # Simple career mapping (can be enhanced with LLM)
        career_paths = []
        
        if any("python" in s.lower() or "javascript" in s.lower() for s in skills["hard_skills"]):
            career_paths.append({
                "title": "Software Developer",
                "match_score": 85,
                "required_skills": ["Python", "JavaScript", "Git"],
                "salary_range": "$60k - $120k",
                "next_steps": ["Learn React", "Build portfolio projects", "Get certifications"]
            })
        
        return {
            "career_paths": career_paths,
            "skill_gaps": [],
            "learning_resources": []
        }
    
    # Helper methods
    def _build_cv_generation_prompt(self, answers: Dict[str, Any]) -> str:
        """Build prompt for CV generation from questionnaire"""
        prompt = f"""Create a professional CV based on these answers:

Role/Industry: {answers.get('role', 'Not specified')}
Experience Level: {answers.get('experience_level', 'Not specified')}
Years of Experience: {answers.get('years_experience', 'Not specified')}
Key Achievements: {answers.get('achievements', 'None')}
Skills: {', '.join(answers.get('skills', []))}
Education: {answers.get('education', 'Not specified')}
Location: {answers.get('location', 'Not specified')}
Desired Salary: {answers.get('desired_salary', 'Not specified')}
Portfolio Links: {answers.get('portfolio_links', 'None')}

Generate a complete, ATS-optimized CV in JSON format."""
        return prompt
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response with robust error handling"""
        original_text = text
        
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                parsed = json.loads(json_str)
                # Check if it's an error object
                if isinstance(parsed, dict) and "error" in parsed:
                    logger.error(f"AI returned error: {parsed.get('error')}")
                    return {}
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing error: {e}. Attempting to fix truncated JSON...")
                # Try to fix common JSON truncation issues
                fixed_json = self._fix_truncated_json(json_str)
                if fixed_json:
                    try:
                        parsed = json.loads(fixed_json)
                        if isinstance(parsed, dict) and "error" not in parsed:
                            logger.info("Successfully fixed truncated JSON")
                            return parsed
                    except:
                        pass
        
        # Fallback: try parsing entire text
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "error" in parsed:
                logger.error(f"AI returned error: {parsed.get('error')}")
                return {}
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Could not parse JSON response: {e}")
            logger.debug(f"Response text (first 1000 chars): {original_text[:1000]}")
            # Try to extract partial JSON if possible
            fixed_json = self._fix_truncated_json(text)
            if fixed_json:
                try:
                    return json.loads(fixed_json)
                except:
                    pass
            return {}
    
    def _fix_truncated_json(self, json_str: str) -> Optional[str]:
        """Attempt to fix truncated or malformed JSON"""
        if not json_str or not json_str.strip().startswith('{'):
            return None
        
        try:
            # Count braces to see if JSON is incomplete
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            # If we have unclosed braces, try to close them
            if open_braces > close_braces:
                # Find the last complete object/array and close it
                fixed = json_str.rstrip()
                
                # Remove incomplete string at the end
                # Find last complete quote pair
                last_quote_idx = fixed.rfind('"')
                if last_quote_idx > 0:
                    # Check if it's an incomplete string
                    before_quote = fixed[:last_quote_idx]
                    if before_quote.count('"') % 2 == 1:  # Odd number means incomplete string
                        # Find the start of this incomplete string
                        incomplete_start = before_quote.rfind('"')
                        if incomplete_start >= 0:
                            # Remove the incomplete string
                            fixed = fixed[:incomplete_start] + '"'
                
                # Close arrays
                open_arrays = fixed.count('[') - fixed.count(']')
                fixed += ']' * open_arrays
                
                # Close objects
                open_objects = fixed.count('{') - fixed.count('}')
                fixed += '}' * open_objects
                
                return fixed
            
            return json_str
        except Exception as e:
            logger.debug(f"Error fixing JSON: {e}")
            return None
    
    def _format_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """Format CV data as readable text"""
        lines = []
        
        # Personal Info
        if "personal_info" in cv_data:
            info = cv_data["personal_info"]
            lines.append(f"{info.get('full_name', '')}")
            lines.append(f"{info.get('email', '')} | {info.get('phone', '')}")
            lines.append("")
        
        # Summary
        if "summary" in cv_data:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append(cv_data["summary"])
            lines.append("")
        
        # Experience
        if "experience" in cv_data:
            lines.append("EXPERIENCE")
            for exp in cv_data["experience"]:
                lines.append(f"{exp.get('job_title', '')} at {exp.get('company', '')}")
                lines.append(exp.get("description", ""))
                lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_ats_score(self, cv_data: Dict[str, Any]) -> int:
        """Calculate basic ATS score"""
        return self.optimize_ats(cv_data)["ats_score"]
    
    def _get_ats_grade(self, score: int) -> str:
        """Get letter grade for ATS score"""
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
    
    def _generate_cv_fallback(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback CV generation without OpenAI"""
        return {
            "success": True,
            "cv_data": {
                "summary": f"Experienced {answers.get('role', 'professional')}",
                "personal_info": {
                    "full_name": answers.get("full_name", ""),
                    "email": answers.get("email", ""),
                    "location": answers.get("location", "")
                },
                "experience": [],
                "education": [],
                "skills": {"technical": answers.get("skills", [])}
            },
            "text_version": "Basic CV generated",
            "ats_score": 60
        }
    
    def get_field_suggestions(self, field: str, current_value: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get 10+ AI suggestions for a specific CV field.
        
        Args:
            field: Field name (e.g., "summary", "experience.0.description")
            current_value: Current value user has typed
            context: Additional context (step, section, etc.)
            
        Returns:
            List of 10+ suggestions
        """
        logger.info(f"Getting suggestions for field: {field}")
        
        if not self.mistral_key:
            return {
                "success": False,
                "suggestions": self._get_fallback_suggestions(field, current_value)
            }
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            # Build context-aware prompt (include industry to diversify suggestions)
            context_str = ""
            if context:
                if context.get("job_title"):
                    context_str += f"Job Title: {context['job_title']}\n"
                if context.get("company"):
                    context_str += f"Company: {context['company']}\n"
                if context.get("experience"):
                    context_str += f"Years of Experience: {context['experience']}\n"
                if context.get("industry"):
                    context_str += f"Industry: {context['industry']}\n"
            
            # Handle empty values for proactive suggestions
            value_context = f"Current Value: {current_value}" if current_value else "Field is currently empty - provide initial suggestions"
            is_proactive = context.get("proactive", False) or not current_value
            
            from app.services.suggestion_validator import SuggestionValidator
            validator = SuggestionValidator()
            
            # Enhanced prompt with explicit quality requirements
            prompt = f"""You are an expert CV writer. Provide 15+ professional, detailed suggestions for this CV field.

Field: {field}
{value_context}
Context: {context_str}
{"Note: This is a proactive suggestion request - provide initial examples to help the user get started." if is_proactive else ""}

CRITICAL QUALITY REQUIREMENTS (STRICT - FOLLOW ALL):
1. Each suggestion MUST be 3-4 COMPLETE sentences minimum (150+ characters, 25+ words) - NO EXCEPTIONS
2. Use SPECIFIC action verbs (Led, Delivered, Achieved, Created, Improved, Managed, Developed, Executed, Spearheaded, Implemented)
3. Include quantifiable metrics where relevant (numbers, percentages, timeframes, scale, team sizes, budgets)
4. Be context-aware based on the field and industry - reference the actual context provided
5. NO spelling mistakes or grammar errors - proofread before responding
6. NO placeholder text, vague statements, or generic phrases like "Results-driven professional" or "Experienced expert"
7. Be professional, ATS-optimized, and industry-relevant
8. Write in complete sentences with proper punctuation
9. Vary the style and approach across suggestions
10. Each suggestion must tell a complete story with specific details
{"11. Since the field is empty, provide diverse examples covering different experience levels and industries" if is_proactive else ""}

EXAMPLE OF GOOD SUGGESTION (3-4 sentences, 150+ characters):
"Led a cross-functional team of 5 developers to deliver a customer-facing web application that increased user engagement by 40% within 3 months. Implemented agile methodologies and CI/CD pipelines, reducing deployment time by 50%. Collaborated with product managers and designers to ensure seamless user experience across all platforms. The project resulted in a 25% increase in customer satisfaction scores and generated $500K in additional revenue."

EXAMPLE OF BAD SUGGESTION (TOO SHORT - DO NOT GENERATE):
"Results-driven professional with proven track record." ❌ TOO SHORT, VAGUE, NO DETAILS
"Experienced expert specializing in delivering results." ❌ TOO SHORT, NO SPECIFICS

Return ONLY a JSON array of strings, no other text:
["Detailed suggestion 1 with specific examples and actionable advice (minimum 80 characters, 12+ words, 2-3 sentences)", "Detailed suggestion 2 with specific examples and actionable advice (minimum 80 characters, 12+ words, 2-3 sentences)", ...]"""
            
            # Retry logic for quality
            from cv.timeout_utils import safe_execute_with_timeout
            for attempt in range(validator.MAX_RETRIES):
                try:
                    response = safe_execute_with_timeout(
                        lambda: client.chat.complete(
                            model="mistral-small-latest",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a professional CV writing expert. Provide 15+ high-quality, detailed suggestions in JSON array format only. Each suggestion MUST be 3-4 complete sentences minimum (150+ characters, 25+ words) - NO EXCEPTIONS. Use strong action verbs, specific examples, quantifiable metrics (numbers, percentages, timeframes, team sizes). Never use markdown formatting - return pure JSON array only. Proofread for spelling and grammar before responding. NEVER return short, vague, or generic suggestions like 'Results-driven professional' or 'Experienced expert'. Each suggestion must tell a complete story with specific details and measurable impact."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.4,
                            max_tokens=4000
                        ),
                        timeout_seconds=12,
                        fallback=None
                    )
                    if response is None:
                        logger.warning(f"Attempt {attempt + 1}: AI call timed out, retrying")
                        if attempt < validator.MAX_RETRIES - 1:
                            continue
                        return {
                            "success": True,
                            "suggestions": self._get_fallback_suggestions(field, current_value)
                        }
            
                    content = response.choices[0].message.content.strip()
                    
                    # Strip all markdown formatting
                    import re
                    content = re.sub(r'```json\s*', '', content)
                    content = re.sub(r'```\s*', '', content)
                    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
                    content = re.sub(r'\*(.*?)\*', r'\1', content)  # Italic
                    content = re.sub(r'`(.*?)`', r'\1', content)  # Code
                    content = content.strip()
                    
                    # Extract JSON array
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        suggestions = json.loads(json_match.group())
                        # Strip markdown from each suggestion
                        suggestions = [re.sub(r'\*\*(.*?)\*\*', r'\1', re.sub(r'\*(.*?)\*', r'\1', re.sub(r'`(.*?)`', r'\1', str(s)))) for s in suggestions]
                        
                        # VALIDATE QUALITY: Filter invalid suggestions
                        valid_suggestions = validator.filter_valid_suggestions(suggestions, field=field, min_valid=5)  # Reduced min to 5 for better UX
                        # De-duplicate to avoid repeating the same text
                        deduped = []
                        seen = set()
                        for s in valid_suggestions:
                            if s not in seen:
                                seen.add(s)
                                deduped.append(s)
                        
                        if len(deduped) >= 5:
                            logger.info(f"Generated {len(deduped)} valid suggestions for field {field} (attempt {attempt + 1})")
                            return {
                                "success": True,
                                "suggestions": deduped[:20]  # Return up to 20
                            }
                        else:
                            logger.warning(f"Attempt {attempt + 1}: Only {len(deduped)} valid suggestions (minimum 5 required). Retrying...")
                            logger.warning(f"Invalid suggestions were: {[s[:50] + '...' if len(s) > 50 else s for s in suggestions[:3]]}")
                            if attempt < validator.MAX_RETRIES - 1:
                                continue  # Retry
                            else:
                                # If we have some valid suggestions, use them (even if less than 5)
                                if len(deduped) > 0:
                                    logger.info(f"Using {len(deduped)} valid suggestions (less than minimum but better than fallback)")
                                    return {
                                        "success": True,
                                        "suggestions": deduped[:20]
                                    }
                                # Only use fallback if we have NO valid suggestions
                                logger.error(f"All {validator.MAX_RETRIES} attempts failed validation. Using fallback (this should be rare).")
                                fallback_suggestions = self._get_fallback_suggestions(field, current_value)
                                return {
                                    "success": True,
                                    "suggestions": fallback_suggestions[:20]
                                }
                    else:
                        logger.warning(f"Attempt {attempt + 1}: Failed to extract JSON array. Retrying...")
                        if attempt < validator.MAX_RETRIES - 1:
                            continue  # Retry
                        else:
                            # Fallback if JSON parsing fails
                            return {
                                "success": True,
                                "suggestions": self._get_fallback_suggestions(field, current_value)
                            }
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1}: Error in field suggestions: {e}")
                    if attempt < validator.MAX_RETRIES - 1:
                        continue  # Retry
                    else:
                        return {
                            "success": True,
                            "suggestions": self._get_fallback_suggestions(field, current_value)
                        }
                
        except Exception as e:
            logger.error(f"Error getting field suggestions: {e}")
            return {
                "success": True,
                "suggestions": self._get_fallback_suggestions(field, current_value)
            }
    
    def _get_fallback_suggestions(self, field: str, current_value: str) -> List[str]:
        """Fallback suggestions when AI is not available - MUST be 3-4 sentences (150+ characters)"""
        suggestions = []
        
        if "summary" in field.lower():
            suggestions = [
                "Led cross-functional teams of 5-10 members to deliver complex software projects that increased user engagement by 40% within 3 months. Implemented agile methodologies and CI/CD pipelines, reducing deployment time by 50% and improving code quality. Collaborated with product managers and designers to ensure seamless user experience across all platforms. The projects resulted in a 25% increase in customer satisfaction scores and generated $500K in additional revenue.",
                "Developed and implemented scalable web applications using modern technologies like React, Node.js, and PostgreSQL, serving over 10,000 active users daily. Optimized database queries and implemented caching strategies that reduced page load times by 60%. Led code reviews and mentored junior developers, improving team productivity by 30%. Achieved 99.9% uptime through robust monitoring and automated deployment pipelines.",
                "Managed full-stack development projects from conception to deployment, working with budgets exceeding $500K and teams of 8-12 developers. Spearheaded the migration of legacy systems to cloud infrastructure, reducing operational costs by 35% and improving scalability. Implemented automated testing frameworks that increased code coverage from 60% to 90%. Delivered projects on time and within budget, resulting in 100% client satisfaction.",
                "Designed and developed RESTful APIs and microservices architecture that processed over 1 million requests per day with 99.9% reliability. Collaborated with cross-functional teams including DevOps, QA, and product management to ensure seamless integration. Implemented security best practices and compliance measures that passed all security audits. Reduced API response times by 40% through performance optimization and caching strategies.",
                "Created data-driven solutions using Python, SQL, and machine learning algorithms that improved business decision-making by 45%. Analyzed large datasets with over 10 million records to identify trends and patterns. Built automated reporting dashboards that reduced manual reporting time by 70%. Presented findings to executive leadership, leading to strategic initiatives that increased revenue by $2M annually.",
            ]
        elif "experience" in field.lower() or "description" in field.lower():
            suggestions = [
                "Led a team of 5 developers to build a customer-facing web application that increased user engagement by 40% within 3 months. Implemented agile methodologies and CI/CD pipelines, reducing deployment time from 2 hours to 15 minutes. Collaborated with product managers to define requirements and prioritize features based on user feedback. The project resulted in a 25% increase in customer satisfaction scores and generated $500K in additional revenue.",
                "Developed and maintained scalable backend services using Node.js and PostgreSQL, handling over 10,000 concurrent users with 99.9% uptime. Optimized database queries and implemented Redis caching, reducing API response times by 60%. Designed and implemented RESTful APIs following industry best practices and security standards. Reduced server costs by 30% through efficient resource utilization and auto-scaling configurations.",
                "Managed the full lifecycle of software projects from requirements gathering to deployment, working with budgets exceeding $500K. Coordinated with stakeholders across engineering, design, and product teams to ensure timely delivery. Implemented automated testing and code review processes that improved code quality by 40%. Delivered 12 projects on time and within budget, resulting in 100% client satisfaction.",
                "Built responsive web applications using React, TypeScript, and Tailwind CSS that improved user experience scores by 35%. Implemented state management solutions using Redux and Context API for complex data flows. Collaborated with UX designers to create intuitive interfaces that reduced user task completion time by 50%. Achieved 95+ Lighthouse performance scores through optimization and best practices.",
                "Designed and implemented machine learning models using Python and scikit-learn that improved prediction accuracy by 30%. Processed and analyzed datasets with over 5 million records to identify patterns and trends. Built automated pipelines for data preprocessing and model training that reduced manual work by 70%. Deployed models to production using Docker and Kubernetes, serving predictions in real-time with 99.5% accuracy.",
            ]
        else:
            # Generic suggestions for other fields
            suggestions = [
                "Demonstrated strong leadership skills by managing cross-functional teams of 5-10 members to deliver complex projects on time and within budget. Implemented agile methodologies that improved team productivity by 30% and reduced project delivery time by 25%. Collaborated with stakeholders to define requirements and ensure alignment with business objectives. Achieved 100% client satisfaction through effective communication and proactive problem-solving.",
                "Leveraged technical expertise in modern web technologies to build scalable applications serving over 10,000 active users daily. Optimized performance through code refactoring and infrastructure improvements, reducing load times by 60%. Implemented automated testing and CI/CD pipelines that improved code quality and deployment frequency. Contributed to open-source projects and shared knowledge through technical blog posts and team presentations.",
            ]
        
        return suggestions[:15]
    
    def _match_job_fallback(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Fallback job matching without OpenAI"""
        # Simple keyword matching
        cv_text = json.dumps(cv_data).lower()
        job_lower = job_description.lower()
        
        # Count matching keywords
        job_words = set(re.findall(r'\b\w{4,}\b', job_lower))
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_text))
        matches = job_words.intersection(cv_words)
        
        score = min(100, len(matches) * 5)
        
        return {
            "success": True,
            "analysis": {
                "compatibility_score": score,
                "matched_skills": list(matches)[:10],
                "missing_skills": [],
                "recommendations": ["Add more relevant keywords from job description"]
            },
            "score": score
        }

