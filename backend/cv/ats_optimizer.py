"""
ATS Optimizer Module
Optimizes CVs for Applicant Tracking Systems with keyword matching and formatting.

NOTE: Uses ATSEngine for deterministic, consistent scoring across all endpoints.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from cv.ats_engine import ATSEngine
from app.utils.logger import logger


class ATSOptimizer:
    """ATS optimization service."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.ats_engine = ATSEngine()  # Use deterministic engine for consistent scoring
    
    def calculate_ats_score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate ATS compatibility score with detailed feedback.
        
        Uses ATSEngine for deterministic, consistent scoring.
        
        Returns:
            {
                "score": float (0-100),
                "grade": str (A+, A, B, C, D),
                "keyword_density": float,
                "section_completeness": dict,
                "formatting_score": float,
                "recommendations": List[str],
                "ats_score": float (same as score, for compatibility)
            }
        """
        logger.info("Calculating ATS score using ATSEngine (deterministic)")
        
        # Use ATSEngine for deterministic scoring (same as job search and other endpoints)
        ats_result = self.ats_engine.calculate_ats_score(cv_data)
        
        score = ats_result.get("ats_score", 0)
        grade = ats_result.get("ats_grade", "D")
        component_scores = ats_result.get("component_scores", {})
        
        return {
            "ats_score": score,
            "score": score,  # For compatibility
            "grade": grade,
            "keyword_density": ats_result.get("keyword_density", 0),
            "section_completeness": component_scores.get("section_completeness", {}),
            "formatting_score": component_scores.get("formatting_readability", 0) * 6.67,  # Scale 0-15 to 0-100
            "recommendations": ats_result.get("ats_recommendations", []),
            "issues": ats_result.get("ats_issues", []),
            "fixes": ats_result.get("ats_recommendations", []),
            "component_scores": component_scores,
            "component_feedback": ats_result.get("component_feedback", {})
        }
    
    def optimize_for_job(self, cv_data: Dict[str, Any], job_description: str, job_skills: List[str], job_title: str) -> Dict[str, Any]:
        """
        Optimize CV for a specific job posting.
        
        Returns:
            Optimized CV with job-specific keywords and formatting
        """
        logger.info(f"Optimizing CV for job: {job_title}")
        
        tailored_cv = self.ai_service.tailor_cv_to_job(
            cv_data,
            job_description,
            job_skills,
            job_title
        )
        
        # Further optimize for ATS
        optimized_cv = self.ai_service.optimize_for_ats(tailored_cv)
        
        return optimized_cv
    
    def get_suggestions(self, section: str, content: str, industry: str = None, db: Session = None) -> Dict[str, Any]:
        """
        Get real-time suggestions for improving CV content.
        FIRST analyzes job market to understand trending skills and keywords,
        THEN provides suggestions based on market analysis.
        
        Returns:
            {
                "improvements": List[Dict],
                "examples": List[str],
                "recommendations": List[str],
                "market_analysis": Dict (trending skills, keywords, etc.)
            }
        """
        logger.info(f"Getting suggestions for section: {section} with market analysis")
        
        # STEP 1: Analyze job market FIRST
        market_analysis = {}
        if db and industry:
            try:
                market_analysis = self.ai_service.analyze_job_market(db, sector=industry)
                logger.info(f"Market analysis complete: {len(market_analysis.get('trending_skills', []))} trending skills found")
            except Exception as e:
                logger.warning(f"Market analysis failed: {str(e)}, continuing without it")
        
        # STEP 2: Get AI suggestions (now informed by market analysis)
        suggestions = self.ai_service.get_realtime_suggestions(section, content, industry)
        
        # STEP 3: Enhance suggestions with market insights
        if market_analysis:
            trending_skills = [s.get("skill") for s in market_analysis.get("trending_skills", [])[:5]]
            trending_keywords = [k.get("keyword") for k in market_analysis.get("trending_keywords", [])[:5]]
            
            # Add market-based recommendations
            market_recommendations = market_analysis.get("recommendations", [])
            if market_recommendations:
                suggestions["recommendations"] = suggestions.get("recommendations", []) + market_recommendations
            
            # Add trending skills to recommendations if not already present
            if trending_skills:
                skills_rec = f"Consider highlighting these trending skills: {', '.join(trending_skills)}"
                if skills_rec not in suggestions.get("recommendations", []):
                    suggestions["recommendations"].append(skills_rec)
        
        # Add market analysis to response
        suggestions["market_analysis"] = market_analysis
        
        return suggestions

