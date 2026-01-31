"""
PDF Parser Service for LinkedIn CV Upload
Extracts text from PDF and uses Mistral AI to parse structured CV data
"""
from typing import Dict, Any, Optional
import io
import re
from fastapi import UploadFile
from app.utils.logger import logger
from app.core.config import settings

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    logger.warning("PDF libraries not installed. PDF upload feature will not work.")
    PyPDF2 = None
    pdfplumber = None


class PDFParserService:
    """Service for parsing LinkedIn CV PDFs using AI"""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        """
        Extract text from PDF file using multiple methods for best results.
        
        Args:
            file: Uploaded PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Read file content
            content = await file.read()
            
            # Try pdfplumber first (better for formatted PDFs like LinkedIn)
            if pdfplumber:
                try:
                    pdf_file = io.BytesIO(content)
                    text = ""
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    
                    if text.strip():
                        logger.info(f"Extracted {len(text)} characters using pdfplumber")
                        return text.strip()
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
            
            # Fallback to PyPDF2
            if PyPDF2:
                try:
                    pdf_file = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                    if text.strip():
                        logger.info(f"Extracted {len(text)} characters using PyPDF2")
                        return text.strip()
                except Exception as e:
                    logger.error(f"PyPDF2 extraction failed: {e}")
            
            raise Exception("Could not extract text from PDF")
            
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            raise
    
    async def parse_linkedin_cv(self, pdf_text: str) -> Dict[str, Any]:
        """
        Use Mistral AI to parse LinkedIn CV text into structured data.
        
        Args:
            pdf_text: Raw text extracted from PDF
            
        Returns:
            Structured CV data
        """
        if not self.mistral_key:
            logger.warning("Mistral API key not configured, using fallback parser")
            return self._fallback_parse(pdf_text)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""You are an expert CV parser. Extract ALL structured information from this LinkedIn CV text.

CV Text:
{pdf_text[:8000]}

IMPORTANT: Extract EVERYTHING you can find. Be thorough and comprehensive.

Return ONLY valid JSON in this exact format (no markdown, no code blocks, no explanations):
{{
  "personal_info": {{
    "first_name": "",
    "surname": "",
    "full_name": "",
    "email": "",
    "phone": "",
    "address": "",
    "location": "",
    "linkedin": "",
    "nationality": ""
  }},
  "summary": "",
  "experience": [
    {{
      "job_title": "",
      "position": "",
      "company": "",
      "employer": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "description": "",
      "responsibilities": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "qualification": "",
      "institution": "",
      "school": "",
      "university": "",
      "field_of_study": "",
      "major": "",
      "start_date": "",
      "end_date": "",
      "graduation_year": "",
      "grade": "",
      "gpa": ""
    }}
  ],
  "skills": {{
    "technical": [],
    "job_related_skills": [],
    "computer_skills": [],
    "programming_skills": [],
    "soft": [],
    "social_skills": [],
    "languages": []
  }},
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "date": "",
      "expiry_date": ""
    }}
  ],
  "projects": [],
  "awards": [],
  "publications": []
}}

CRITICAL INSTRUCTIONS:
1. Extract ALL experience entries - look for job titles, companies, dates, descriptions
2. Extract ALL education entries - look for degrees, institutions, fields of study, dates
3. Extract ALL skills - look for technical skills, programming languages, tools, soft skills, languages
4. Extract the professional summary if present
5. Be comprehensive - don't skip any information
6. If you see multiple formats (e.g., "job_title" vs "position"), include both
7. Return valid JSON only - no markdown, no code blocks"""
            
            # Try mistral-small-latest first to avoid rate limits, fallback to medium
            try:
                response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a CV parsing expert. Extract ALL structured data comprehensively. Return ONLY valid JSON, no markdown formatting, no explanations."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent parsing
                    max_tokens=4000
                )
            except Exception as small_error:
                logger.warning(f"mistral-small-latest failed for CV parsing, trying mistral-medium-latest: {str(small_error)}")
                import time
                time.sleep(2)
                response = client.chat.complete(
                    model="mistral-medium-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a CV parsing expert. Extract ALL structured data comprehensively. Return ONLY valid JSON, no markdown formatting, no explanations."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            cv_data = json.loads(content)
            
            # Log extraction results
            exp_count = len(cv_data.get("experience", []))
            edu_count = len(cv_data.get("education", []))
            skills_data = cv_data.get("skills", {})
            tech_skills_count = len(skills_data.get("technical", [])) if isinstance(skills_data, dict) else 0
            logger.info(f"CV Parsed: {exp_count} experience, {edu_count} education, {tech_skills_count} technical skills")
            
            return cv_data
            
        except Exception as e:
            logger.error(f"Mistral AI parsing error: {e}, using fallback")
            return self._fallback_parse(pdf_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """
        Fallback parser using regex and heuristics when AI is not available.
        
        Args:
            text: Raw CV text
            
        Returns:
            Basic structured CV data
        """
        logger.info("Using fallback parser")
        
        cv_data = {
            "personal_info": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": {"technical": [], "soft": [], "languages": []},
            "certifications": [],
            "projects": [],
            "awards": []
        }
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            cv_data["personal_info"]["email"] = email_match.group()
        
        # Extract phone
        phone_match = re.search(r'\+?[\d\s\-\(\)]{10,}', text)
        if phone_match:
            cv_data["personal_info"]["phone"] = phone_match.group().strip()
        
        # Extract LinkedIn URL
        linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text)
        if linkedin_match:
            cv_data["personal_info"]["linkedin"] = linkedin_match.group()
        
        # Try to extract name (first line often contains name)
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line.split()) <= 4 and len(first_line) < 50:
                name_parts = first_line.split()
                if len(name_parts) >= 2:
                    cv_data["personal_info"]["first_name"] = name_parts[0]
                    cv_data["personal_info"]["surname"] = " ".join(name_parts[1:])
        
        # Extract summary (look for common summary keywords)
        summary_keywords = ["summary", "profile", "about", "objective"]
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next few lines as summary
                summary_lines = []
                for j in range(i+1, min(i+6, len(lines))):
                    if lines[j].strip() and not any(k in lines[j].lower() for k in ["experience", "education", "skills"]):
                        summary_lines.append(lines[j].strip())
                cv_data["summary"] = " ".join(summary_lines)
                break
        
        return cv_data
    
    def validate_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted CV data.
        Normalizes data structure to ensure consistent format.
        
        Args:
            cv_data: Extracted CV data
            
        Returns:
            Validated and cleaned CV data with normalized structure
        """
        # Ensure required fields exist
        if "personal_info" not in cv_data:
            cv_data["personal_info"] = {}
        
        # Normalize experience - ensure both 'experience' and 'work_experience' point to same data
        experience = cv_data.get("experience", cv_data.get("work_experience", []))
        if not isinstance(experience, list):
            experience = []
        cv_data["experience"] = experience
        cv_data["work_experience"] = experience  # Also set work_experience for compatibility
        
        # Normalize education
        if "education" not in cv_data:
            cv_data["education"] = []
        if not isinstance(cv_data["education"], list):
            cv_data["education"] = []
        
        # Normalize skills - handle multiple formats (strings, lists, nested dicts)
        skills = cv_data.get("skills", cv_data.get("personal_skills", {}))
        if not isinstance(skills, dict):
            skills = {}
        
        # Helper function to convert string skills to list
        def normalize_skill_list(skill_data):
            """Convert skill data (string or list) to a proper list."""
            if isinstance(skill_data, list):
                return [s.strip() for s in skill_data if isinstance(s, str) and s.strip()]
            elif isinstance(skill_data, str) and skill_data.strip():
                # Split by comma, pipe, or semicolon
                return [s.strip() for s in re.split(r'[,|;]', skill_data) if s.strip()]
            else:
                return []
        
        # Ensure skills has standard structure - convert all to lists
        normalized_skills = {
            "technical": normalize_skill_list(skills.get("technical") or skills.get("job_related_skills") or skills.get("technical_skills") or []),
            "soft": normalize_skill_list(skills.get("soft") or skills.get("social_skills") or []),
            "languages": normalize_skill_list(skills.get("languages") or []),
            "computer_skills": normalize_skill_list(skills.get("computer_skills") or skills.get("programming_skills") or []),
            # Also keep Europass format for compatibility
            "job_related_skills": normalize_skill_list(skills.get("job_related_skills") or skills.get("technical") or []),
            "social_skills": normalize_skill_list(skills.get("social_skills") or skills.get("soft") or []),
            # Also add any additional skill categories from the original data
            "tools": normalize_skill_list(skills.get("tools") or []),
            "blockchain": normalize_skill_list(skills.get("blockchain") or []),
            "databases": normalize_skill_list(skills.get("databases") or []),
            "frameworks": normalize_skill_list(skills.get("frameworks") or []),
        }
        cv_data["skills"] = normalized_skills
        cv_data["personal_skills"] = normalized_skills  # Also set personal_skills for compatibility
        
        # Clean email
        if cv_data["personal_info"].get("email"):
            email = cv_data["personal_info"]["email"].strip().lower()
            if "@" in email:
                cv_data["personal_info"]["email"] = email
        
        # Clean phone
        if cv_data["personal_info"].get("phone"):
            phone = re.sub(r'[^\d\+\-\(\)\s]', '', cv_data["personal_info"]["phone"])
            cv_data["personal_info"]["phone"] = phone.strip()
        
        # Ensure full_name is set
        if not cv_data["personal_info"].get("full_name"):
            first = cv_data["personal_info"].get("first_name", "")
            surname = cv_data["personal_info"].get("surname", "")
            if first or surname:
                cv_data["personal_info"]["full_name"] = f"{first} {surname}".strip()
        
        logger.info(f"Validated CV data: {len(experience)} experience, {len(cv_data['education'])} education, {len(normalized_skills.get('technical', []))} technical skills")
        
        return cv_data
