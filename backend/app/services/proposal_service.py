"""
Freelancing Proposal Writing Service
Generates customized proposals for freelancing jobs using AI.
"""
from typing import Dict, Any, Optional, List
from app.utils.logger import logger
from app.core.config import settings
import json
import re


class ProposalService:
    """Service to generate customized freelancing proposals."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY
    
    def generate_proposal(
        self,
        job_description: str,
        client_requirements: str,
        user_skills: List[str],
        user_experience: List[Dict[str, Any]],
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a customized freelancing proposal.
        
        Args:
            job_description: Full job description from the platform
            client_requirements: Specific requirements mentioned by the client
            user_skills: List of user's skills
            user_experience: List of user's work experience entries
            tone: Proposal tone ("professional", "friendly", "confident")
            
        Returns:
            Dictionary with proposal content and metadata
        """
        logger.info(f"Generating proposal with tone: {tone}")
        
        if not self.mistral_key:
            return self._generate_proposal_fallback(
                job_description, client_requirements, user_skills, user_experience, tone
            )
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            # Prepare user experience summary
            experience_summary = self._format_experience(user_experience)
            
            prompt = self._build_proposal_prompt(
                job_description,
                client_requirements,
                user_skills,
                experience_summary,
                tone
            )
            
            response = client.chat.complete(
                model="mistral-small-latest",  # Faster model for quicker generation
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert freelancing proposal writer. 
                        Create compelling, customized proposals that:
                        - Show genuine understanding of the client's needs
                        - Highlight relevant skills and experience
                        - Demonstrate value proposition clearly
                        - Include a clear call-to-action
                        - Match the requested tone (professional, friendly, or confident)
                        
                        IMPORTANT: Write in plain text only. Do NOT use markdown formatting:
                        - NO asterisks (*) for bold or italic
                        - NO hash symbols (#) for headers
                        - NO markdown syntax at all
                        - Use plain text with line breaks only
                        
                        Structure proposals with:
                        1. Personalized greeting
                        2. Understanding of the job (show you read it)
                        3. Relevant experience and skills
                        4. Value proposition (what you'll deliver)
                        5. Clear call-to-action
                        
                        Keep proposals concise (300-500 words), engaging, and tailored to the specific job.
                        Output ONLY plain text, no formatting."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000  # Reduced for faster generation
            )
            
            proposal_text = response.choices[0].message.content.strip()
            
            # CRITICAL: Strip all markdown formatting from proposal
            proposal_text = self._strip_markdown(proposal_text)
            
            # Parse and structure the proposal
            structured_proposal = self._parse_proposal(proposal_text)
            
            return {
                "success": True,
                "proposal": structured_proposal.get("full_text", proposal_text),
                "sections": structured_proposal.get("sections", {}),
                "word_count": len(proposal_text.split()),
                "tone": tone,
                "metadata": {
                    "skills_highlighted": self._extract_highlighted_skills(proposal_text, user_skills),
                    "experience_mentioned": self._extract_experience_mentions(proposal_text, user_experience)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return self._generate_proposal_fallback(
                job_description, client_requirements, user_skills, user_experience, tone
            )
    
    def _build_proposal_prompt(
        self,
        job_description: str,
        client_requirements: str,
        user_skills: List[str],
        experience_summary: str,
        tone: str
    ) -> str:
        """Build the AI prompt for proposal generation."""
        
        tone_guidance = {
            "professional": "Use a formal, respectful tone. Focus on competence and reliability.",
            "friendly": "Use a warm, approachable tone. Build rapport while maintaining professionalism.",
            "confident": "Use an assertive, results-oriented tone. Emphasize achievements and capabilities."
        }
        
        return f"""Write a customized freelancing proposal for this job:

JOB DESCRIPTION:
{job_description}

CLIENT REQUIREMENTS:
{client_requirements}

MY SKILLS:
{', '.join(user_skills[:10])}

MY RELEVANT EXPERIENCE:
{experience_summary}

TONE: {tone}
{tone_guidance.get(tone, tone_guidance['professional'])}

REQUIREMENTS:
1. Start with a personalized greeting that shows you read the job description
2. Demonstrate understanding of the client's needs (reference specific requirements)
3. Highlight your most relevant skills and experience (match them to job requirements)
4. Explain your value proposition (what specific results you'll deliver)
5. Include a clear call-to-action (next steps, availability, how to proceed)
6. Keep it between 300-500 words
7. Make it specific to THIS job (not generic)
8. Use the {tone} tone throughout

Generate the complete proposal now:"""
    
    def _format_experience(self, experience: List[Dict[str, Any]]) -> str:
        """Format user experience for the prompt."""
        if not experience:
            return "Entry-level professional, eager to learn and contribute."
        
        formatted = []
        for exp in experience[:3]:  # Top 3 most relevant
            title = exp.get("job_title", "") or exp.get("position", "")
            company = exp.get("company", "") or exp.get("employer", "")
            description = exp.get("description", "")[:200]  # First 200 chars
            
            exp_str = f"- {title}"
            if company:
                exp_str += f" at {company}"
            if description:
                exp_str += f": {description}"
            
            formatted.append(exp_str)
        
        return "\n".join(formatted) if formatted else "Experienced professional with relevant background."
    
    def _parse_proposal(self, proposal_text: str) -> Dict[str, Any]:
        """Parse proposal into structured sections."""
        sections = {
            "greeting": "",
            "understanding": "",
            "value_proposition": "",
            "call_to_action": "",
            "full_text": proposal_text
        }
        
        # Try to identify sections (basic parsing)
        lines = proposal_text.split('\n')
        current_section = "greeting"
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(word in line_lower for word in ["hello", "hi", "dear", "greetings"]):
                sections["greeting"] += line + "\n"
            elif any(word in line_lower for word in ["understand", "see", "notice", "requirements"]):
                sections["understanding"] += line + "\n"
            elif any(word in line_lower for word in ["deliver", "provide", "offer", "bring", "value"]):
                sections["value_proposition"] += line + "\n"
            elif any(word in line_lower for word in ["contact", "available", "next step", "let's", "ready"]):
                sections["call_to_action"] += line + "\n"
        
        return sections
    
    def _extract_highlighted_skills(self, proposal_text: str, user_skills: List[str]) -> List[str]:
        """Extract which skills were highlighted in the proposal."""
        highlighted = []
        proposal_lower = proposal_text.lower()
        
        for skill in user_skills:
            if skill.lower() in proposal_lower:
                highlighted.append(skill)
        
        return highlighted[:5]  # Top 5
    
    def _extract_experience_mentions(self, proposal_text: str, experience: List[Dict[str, Any]]) -> List[str]:
        """Extract which experience entries were mentioned."""
        mentioned = []
        proposal_lower = proposal_text.lower()
        
        for exp in experience:
            title = (exp.get("job_title", "") or exp.get("position", "")).lower()
            company = (exp.get("company", "") or exp.get("employer", "")).lower()
            
            if title and title in proposal_lower:
                mentioned.append(exp.get("job_title", "") or exp.get("position", ""))
            elif company and company in proposal_lower:
                mentioned.append(exp.get("company", "") or exp.get("employer", ""))
        
        return mentioned[:3]  # Top 3
    
    def _strip_markdown(self, text: str) -> str:
        """Strip all markdown formatting from text."""
        if not text:
            return ""
        
        # Remove markdown headers (# ## ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove code blocks (`code` or ```code```)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove links [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove list markers (- * +)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Remove numbered lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _generate_proposal_fallback(
        self,
        job_description: str,
        client_requirements: str,
        user_skills: List[str],
        user_experience: List[Dict[str, Any]],
        tone: str
    ) -> Dict[str, Any]:
        """Fallback proposal generation without AI."""
        logger.info("Using fallback proposal generation")
        
        # Extract key requirements
        requirements = client_requirements or job_description[:200]
        
        # Build basic proposal
        greeting = "Hello,\n\n"
        if tone == "friendly":
            greeting = "Hi there,\n\n"
        elif tone == "confident":
            greeting = "Dear Client,\n\n"
        
        understanding = f"I've reviewed your project requirements and understand you need: {requirements[:100]}...\n\n"
        
        skills_section = f"I bring expertise in {', '.join(user_skills[:5])} to this project.\n\n"
        
        experience_section = ""
        if user_experience:
            top_exp = user_experience[0]
            title = top_exp.get("job_title", "") or top_exp.get("position", "Professional")
            experience_section = f"In my role as {title}, I've successfully delivered similar projects.\n\n"
        
        value_prop = "I'm committed to delivering high-quality results on time and within budget. I'll keep you updated throughout the project and ensure your satisfaction.\n\n"
        
        cta = "I'm available to start immediately and would love to discuss how I can help bring your project to life. Please let me know if you'd like to schedule a call.\n\nBest regards"
        
        full_proposal = greeting + understanding + skills_section + experience_section + value_prop + cta
        
        # Strip any markdown that might have been added
        full_proposal = self._strip_markdown(full_proposal)
        
        return {
            "success": True,
            "proposal": full_proposal,
            "sections": {
                "greeting": greeting,
                "understanding": understanding,
                "value_proposition": value_prop,
                "call_to_action": cta,
                "full_text": full_proposal
            },
            "word_count": len(full_proposal.split()),
            "tone": tone,
            "metadata": {
                "skills_highlighted": user_skills[:5],
                "experience_mentioned": [exp.get("job_title", "") for exp in user_experience[:1]]
            }
        }
