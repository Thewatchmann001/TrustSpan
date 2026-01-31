"""
Learning Resources Service
Generates curated learning resources (YouTube, Udemy, free courses) for missing skills.
"""
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from app.core.config import settings
import re


class LearningResourcesService:
    """Service to generate learning resources for skill gaps."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY
    
    def generate_learning_resources(
        self,
        skill: str,
        skill_category: Optional[str] = None,
        user_level: str = "beginner"
    ) -> List[Dict[str, Any]]:
        """
        Generate learning resources for a specific skill.
        
        Args:
            skill: The skill name to find resources for
            skill_category: Optional category (e.g., "programming", "design", "marketing")
            user_level: User's current level ("beginner", "intermediate", "advanced")
            
        Returns:
            List of learning resources with platform, title, URL, and description
        """
        logger.info(f"Generating learning resources for skill: {skill}")
        
        # First, try to get AI-generated resources
        if self.mistral_key:
            try:
                ai_resources = self._generate_ai_resources(skill, skill_category, user_level)
                if ai_resources:
                    return ai_resources
            except Exception as e:
                logger.warning(f"AI resource generation failed: {e}, using fallback")
        
        # Fallback to curated resources
        return self._get_fallback_resources(skill, skill_category)
    
    def _generate_ai_resources(
        self,
        skill: str,
        skill_category: Optional[str],
        user_level: str
    ) -> List[Dict[str, Any]]:
        """Generate learning resources using AI."""
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Generate 3-5 free or affordable learning resources for learning "{skill}".

Skill Category: {skill_category or "General"}
User Level: {user_level}

For each resource, provide:
1. Platform name (YouTube, Udemy, Coursera, freeCodeCamp, Khan Academy, etc.)
2. Resource title/course name
3. A specific URL or search query
4. Brief description (1-2 sentences)
5. Why it's good for beginners
6. Estimated time to complete (if applicable)

Prioritize:
- Free resources (YouTube, freeCodeCamp, Khan Academy)
- Beginner-friendly content
- Well-known, reputable sources
- Practical, hands-on learning

Return ONLY a JSON array in this exact format:
[
  {{
    "platform": "YouTube",
    "title": "Complete Beginner's Guide to [Skill]",
    "url": "https://www.youtube.com/results?search_query=beginner+[skill]+tutorial",
    "description": "Comprehensive tutorial series covering fundamentals",
    "difficulty": "beginner",
    "duration": "2-3 hours",
    "free": true
  }},
  ...
]

IMPORTANT: 
- Use actual, searchable URLs or specific course URLs
- Focus on free resources first
- Make titles specific and actionable
- Ensure URLs are valid or provide search queries"""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content curator. Generate specific, actionable learning resources with real URLs or search queries."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                import json
                resources = json.loads(json_match.group())
                
                # Validate and format resources
                formatted_resources = []
                for resource in resources:
                    if isinstance(resource, dict):
                        formatted_resources.append({
                            "platform": resource.get("platform", "Unknown"),
                            "title": resource.get("title", f"Learn {skill}"),
                            "url": resource.get("url", self._generate_search_url(skill, resource.get("platform", "YouTube"))),
                            "description": resource.get("description", f"Learn {skill} from scratch"),
                            "difficulty": resource.get("difficulty", "beginner"),
                            "duration": resource.get("duration", "Varies"),
                            "free": resource.get("free", True)
                        })
                
                return formatted_resources[:5]  # Limit to 5 resources
            
        except Exception as e:
            logger.error(f"Error generating AI resources: {e}")
            return []
    
    def _get_fallback_resources(
        self,
        skill: str,
        skill_category: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fallback curated resources for common skills."""
        skill_lower = skill.lower()
        
        # Programming/Technical skills
        if any(term in skill_lower for term in ["python", "javascript", "java", "react", "node", "programming", "coding", "developer"]):
            return [
                {
                    "platform": "freeCodeCamp",
                    "title": f"freeCodeCamp - {skill} Tutorial",
                    "url": f"https://www.freecodecamp.org/search?query={skill.replace(' ', '+')}",
                    "description": "Free, comprehensive programming tutorials with hands-on projects",
                    "difficulty": "beginner",
                    "duration": "Self-paced",
                    "free": True
                },
                {
                    "platform": "YouTube",
                    "title": f"Complete {skill} Course for Beginners",
                    "url": f"https://www.youtube.com/results?search_query=beginner+{skill.replace(' ', '+')}+tutorial",
                    "description": "Free video tutorials from expert instructors",
                    "difficulty": "beginner",
                    "duration": "Varies",
                    "free": True
                },
                {
                    "platform": "MDN Web Docs",
                    "title": f"MDN - {skill} Documentation",
                    "url": f"https://developer.mozilla.org/en-US/search?q={skill.replace(' ', '+')}",
                    "description": "Official documentation and guides",
                    "difficulty": "beginner",
                    "duration": "Self-paced",
                    "free": True
                }
            ]
        
        # Design skills
        if any(term in skill_lower for term in ["design", "ui", "ux", "figma", "photoshop", "illustrator"]):
            return [
                {
                    "platform": "YouTube",
                    "title": f"{skill} Design Tutorial for Beginners",
                    "url": f"https://www.youtube.com/results?search_query=beginner+{skill.replace(' ', '+')}+design+tutorial",
                    "description": "Free design tutorials and walkthroughs",
                    "difficulty": "beginner",
                    "duration": "Varies",
                    "free": True
                },
                {
                    "platform": "Coursera",
                    "title": f"Introduction to {skill}",
                    "url": f"https://www.coursera.org/search?query={skill.replace(' ', '+')}",
                    "description": "Structured courses with free audit option",
                    "difficulty": "beginner",
                    "duration": "4-6 weeks",
                    "free": True
                }
            ]
        
        # Marketing/Business skills
        if any(term in skill_lower for term in ["marketing", "seo", "social media", "analytics", "business"]):
            return [
                {
                    "platform": "Google Digital Garage",
                    "title": f"Digital Marketing Fundamentals",
                    "url": "https://learndigital.withgoogle.com/digitalgarage",
                    "description": "Free Google-certified digital marketing course",
                    "difficulty": "beginner",
                    "duration": "40 hours",
                    "free": True
                },
                {
                    "platform": "HubSpot Academy",
                    "title": f"HubSpot {skill} Course",
                    "url": "https://academy.hubspot.com/",
                    "description": "Free marketing and sales certifications",
                    "difficulty": "beginner",
                    "duration": "Varies",
                    "free": True
                }
            ]
        
        # General fallback
        return [
            {
                "platform": "YouTube",
                "title": f"Learn {skill} - Beginner Tutorial",
                "url": f"https://www.youtube.com/results?search_query=learn+{skill.replace(' ', '+')}+beginner",
                "description": "Free video tutorials to get started",
                "difficulty": "beginner",
                "duration": "Varies",
                "free": True
            },
            {
                "platform": "Coursera",
                "title": f"{skill} Courses",
                "url": f"https://www.coursera.org/search?query={skill.replace(' ', '+')}",
                "description": "Free courses with audit option",
                "difficulty": "beginner",
                "duration": "4-6 weeks",
                "free": True
            },
            {
                "platform": "Khan Academy",
                "title": f"{skill} Lessons",
                "url": f"https://www.khanacademy.org/search?page_search_query={skill.replace(' ', '+')}",
                "description": "Free educational content",
                "difficulty": "beginner",
                "duration": "Self-paced",
                "free": True
            }
        ]
    
    def _generate_search_url(self, skill: str, platform: str) -> str:
        """Generate a search URL for a skill on a platform."""
        skill_encoded = skill.replace(" ", "+")
        
        platform_urls = {
            "YouTube": f"https://www.youtube.com/results?search_query=beginner+{skill_encoded}+tutorial",
            "Udemy": f"https://www.udemy.com/courses/search/?q={skill_encoded}&src=ukw",
            "Coursera": f"https://www.coursera.org/search?query={skill_encoded}",
            "freeCodeCamp": f"https://www.freecodecamp.org/search?query={skill_encoded}",
            "Khan Academy": f"https://www.khanacademy.org/search?page_search_query={skill_encoded}",
        }
        
        return platform_urls.get(platform, f"https://www.google.com/search?q=learn+{skill_encoded}")
