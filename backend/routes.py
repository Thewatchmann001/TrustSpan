"""
Main API Routes
Exposes endpoints for CV Builder and Investment Platform.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import re
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import get_db
from app.db.models import User, Startup, Investment, Employee
from app.core.config import settings
from app.utils.logger import logger
from sqlalchemy import func, or_, String

from cv.cv_generator import CVGenerator
from cv.ats_optimizer import ATSOptimizer
from cv.ats_engine import get_ats_engine
from cv.job_matcher import JobMatcher
from cv.global_job_api import GlobalJobAPI
from cv.job_aggregator import JobAggregator
from cv.job_keyword_extractor import JobKeywordExtractor
from investments.startup_verification import StartupVerification
from investments.usdc_transactions import USDCTransactions
from investments.investor_portfolio import InvestorPortfolio
from investments.receipt_generator import ReceiptGenerator
from app.services.advanced_cv_service import AdvancedCVService
from app.services.qr_service import QRCodeService
from app.services.credibility_service import CredibilityService
from app.blockchain.startup_client import StartupClient
from app.services.attestation import AttestationService
from app.services.proposal_service import ProposalService
from app.db.models import Attestation

router = APIRouter()

# Initialize services
cv_generator = CVGenerator()
ats_optimizer = ATSOptimizer()
job_matcher = JobMatcher()
global_job_api = GlobalJobAPI()
job_aggregator = JobAggregator()
startup_verification = StartupVerification()
usdc_transactions = USDCTransactions()
investor_portfolio = InvestorPortfolio()
receipt_generator = ReceiptGenerator()
advanced_cv_service = AdvancedCVService()
attestation_service = AttestationService()
proposal_service = ProposalService()


# ==================== CV BUILDER ENDPOINTS ====================

class CVGenerateRequest(BaseModel):
    user_id: int
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: Dict[str, Any]
    awards: Optional[List[Dict[str, Any]]] = None
    publications: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    memberships: Optional[List[Dict[str, Any]]] = None
    job_id: Optional[int] = None


@router.post("/api/cv/generate")
async def generate_cv_endpoint(
    user_id: int = Form(...),
    personal_info: str = Form("{}"),
    experience: str = Form("[]"),
    education: str = Form("[]"),
    skills: str = Form("{}"),
    awards: str = Form("[]"),
    publications: str = Form("[]"),
    projects: str = Form("[]"),
    memberships: str = Form("[]"),
    job_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Generate a professional CV with AI enhancements."""
    try:
        # Parse JSON strings
        personal_info_dict = json.loads(personal_info) if personal_info else {}
        experience_list = json.loads(experience) if experience else []
        education_list = json.loads(education) if education else []
        skills_dict = json.loads(skills) if skills else {}
        awards_list = json.loads(awards) if awards else []
        publications_list = json.loads(publications) if publications else []
        projects_list = json.loads(projects) if projects else []
        memberships_list = json.loads(memberships) if memberships else []
        
        # Handle photo upload
        photo_url = None
        if photo:
            # Save photo
            import shutil
            import uuid
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_ext = Path(photo.filename).suffix
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
            file_path = upload_dir / unique_filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            photo_url = f"/static/uploads/{unique_filename}"
        
        # Generate CV (async for better performance)
        # Return immediate response to user, then process in background
        import asyncio
        from fastapi import BackgroundTasks
        
        # Generate CV synchronously (will be optimized later)
        # TODO: Make this fully async with background tasks
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=personal_info_dict,
            experience=experience_list,
            education=education_list,
            skills=skills_dict,
            awards=awards_list,
            publications=publications_list,
            projects=projects_list,
            memberships=memberships_list,
            job_id=job_id,
            photo_url=photo_url,
            db=db
        )
        
        # CRITICAL: Generate jobs for CV Builder (same as Quick Upload)
        # If CV was created via CV Builder and has no stored jobs, generate them now
        from app.db.models import CV
        saved_cv = db.query(CV).filter(CV.id == result.get("id")).first()
        if saved_cv and saved_cv.json_content:
            stored_jobs = saved_cv.json_content.get("stored_job_matches")
            if not stored_jobs or len(stored_jobs) == 0:
                logger.info(f"[CV GENERATE ENDPOINT] No stored jobs found - generating jobs for CV {saved_cv.id}")
                try:
                    # Build CV data for job matching
                    cv_data = {
                        "personal_info": personal_info_dict,
                        "experience": experience_list,
                        "education": education_list,
                        "skills": skills_dict,
                        "summary": personal_info_dict.get("summary", ""),
                    }
                    
                    # Extract keywords and search jobs (same logic as Quick Upload)
                    from cv.job_keyword_extractor import JobKeywordExtractor
                    from cv.job_aggregator import JobAggregator
                    from cv.timeout_utils import safe_execute_with_timeout
                    
                    keyword_extractor = JobKeywordExtractor()
                    tiers = keyword_extractor.extract_keywords(cv_data)
                    primary_keywords = tiers.get("primary_search", [])
                    platform_keywords = {
                        "remoteok": keyword_extractor.get_platform_keywords(cv_data, "remoteok"),
                        "arbeitnow": keyword_extractor.get_platform_keywords(cv_data, "arbeitnow"),
                        "freelancer": keyword_extractor.get_platform_keywords(cv_data, "freelancer"),
                        "adzuna": keyword_extractor.get_platform_keywords(cv_data, "adzuna"),
                    }
                    
                    aggregator = JobAggregator()
                    
                    # Normalize CV data for domain filtering
                    from app.services.pdf_parser_service import PDFParserService
                    pdf_parser = PDFParserService()
                    normalized_cv_for_filtering = pdf_parser.validate_cv_data(cv_data.copy())
                    
                    # Search jobs with timeout
                    job_matches = safe_execute_with_timeout(
                        aggregator.search_jobs,
                        timeout_seconds=15,
                        fallback=[],
                        keywords=primary_keywords,
                        limit=100,
                        platform_keywords=platform_keywords,
                        cv_data=normalized_cv_for_filtering
                    )
                    
                    # Remove duplicates
                    seen = set()
                    unique_jobs = []
                    for job in job_matches:
                        title = job.get("title", "").strip().lower()
                        company = job.get("company", job.get("company_name", "")).strip().lower()
                        source = job.get("source", "Unknown")
                        key = (title, company, source)
                        if key not in seen and title and company:
                            seen.add(key)
                            unique_jobs.append(job)
                    
                    # Interleave jobs from different sources
                    from collections import defaultdict
                    jobs_by_source = defaultdict(list)
                    for job in unique_jobs:
                        source = job.get("source", "Unknown")
                        jobs_by_source[source].append(job)
                    
                    interleaved = []
                    max_per_source = max(len(jobs) for jobs in jobs_by_source.values()) if jobs_by_source else 0
                    interleave_limit = min(100, len(unique_jobs))
                    
                    for i in range(max_per_source):
                        if len(interleaved) >= interleave_limit:
                            break
                        for source_name, source_jobs in jobs_by_source.items():
                            if len(interleaved) >= interleave_limit:
                                break
                            if i < len(source_jobs):
                                job = source_jobs[i]
                                job_key = (job.get("title", "").strip().lower(), 
                                         job.get("company", job.get("company_name", "")).strip().lower(), 
                                         job.get("source", "Unknown"))
                                if job_key[0] and job_key[1]:
                                    interleaved.append(job)
                    
                    # Store jobs in CV
                    saved_cv.json_content["stored_job_matches"] = interleaved
                    
                    # Extract and store CV domain
                    try:
                        from cv.domain_extractor import DomainExtractor
                        domain_extractor = DomainExtractor()
                        cv_domains = safe_execute_with_timeout(
                            domain_extractor.extract_domains,
                            timeout_seconds=15,
                            fallback=set(),
                            cv_data=normalized_cv_for_filtering
                        )
                        parsed_skills = domain_extractor._extract_skills(normalized_cv_for_filtering)
                        saved_cv.json_content["cv_domain"] = list(cv_domains) if cv_domains else []
                        saved_cv.json_content["parsed_skills"] = parsed_skills
                    except Exception as e:
                        logger.error(f"[CV GENERATE ENDPOINT] Failed to extract domain: {str(e)}")
                        saved_cv.json_content["cv_domain"] = []
                        saved_cv.json_content["parsed_skills"] = []
                    
                    # Store job search context
                    saved_cv.json_content["job_search"] = {
                        "keywords_tiers": tiers,
                        "primary_keywords": primary_keywords,
                        "platform_keywords": platform_keywords,
                        "last_results_count": len(interleaved),
                        "cv_domain": saved_cv.json_content.get("cv_domain", []),
                        "parsed_skills": saved_cv.json_content.get("parsed_skills", []),
                    }
                    saved_cv.json_content["job_match_keywords"] = primary_keywords
                    
                    # Flag as modified and commit
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(saved_cv, "json_content")
                    db.commit()
                    db.refresh(saved_cv)
                    
                    logger.info(f"[CV GENERATE ENDPOINT] Generated {len(interleaved)} jobs for CV {saved_cv.id}")
                    
                    # Update result with new job count
                    if result.get("json_content"):
                        result["json_content"]["stored_job_matches"] = interleaved
                except Exception as e:
                    logger.error(f"[CV GENERATE ENDPOINT] Error generating jobs: {str(e)}", exc_info=True)
                    # Don't fail the request if job generation fails
            else:
                logger.info(f"[CV GENERATE ENDPOINT] stored_job_matches preserved: {len(stored_jobs) if isinstance(stored_jobs, list) else 'N/A'} jobs")
        
        return result
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CV: {str(e)}"
        )


@router.get("/api/cv/{user_id}")
async def get_cv_endpoint(user_id: int, db: Session = Depends(get_db)):
    """Get the latest CV for a user."""
    cv = cv_generator.get_cv(user_id, db)
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CV not found for user {user_id}"
        )
    return cv


@router.delete("/api/cv/{user_id}")
async def delete_cv_endpoint(user_id: int, db: Session = Depends(get_db)):
    """Delete all CVs for a user and related credentials."""
    try:
        from app.db.models import CV, Credential
        
        # Get all CVs for this user
        cvs = db.query(CV).filter(CV.user_id == user_id).all()
        cv_count = len(cvs)
        
        # Delete all CVs if they exist
        for cv in cvs:
            db.delete(cv)
        
        # Also delete all related credentials (education, employment, startup roles)
        # This is done regardless of whether CV records exist, because credentials
        # can exist independently and the get_cv() method reconstructs CVs from them
        credentials = db.query(Credential).filter(Credential.user_id == user_id).all()
        credential_count = len(credentials)
        for credential in credentials:
            db.delete(credential)
        
        # Only return error if there's nothing to delete
        if cv_count == 0 and credential_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No CV or credentials found for user {user_id}"
            )
        
        db.commit()
        
        logger.info(f"Deleted {cv_count} CV(s) and {credential_count} credential(s) for user {user_id}")
        return {
            "success": True,
            "message": f"Successfully deleted {cv_count} CV(s) and {credential_count} credential(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting CV: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete CV: {str(e)}"
        )


@router.post("/api/cv/upload-photo")
async def upload_photo_endpoint(
    photo: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload CV photo."""
    try:
        import shutil
        import uuid
        
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(photo.filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        photo_url = f"/static/uploads/{unique_filename}"
        
        return {
            "success": True,
            "photo_url": photo_url
        }
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}"
        )


@router.post("/api/cv/save")
async def save_cv_endpoint(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Save CV to database (accepts JSON)."""
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
        
        # Prepare CV data
        personal_info = request.get("personal_info", {})
        experience = request.get("experience", [])
        education = request.get("education", [])
        skills = request.get("skills", {})
        awards = request.get("awards", [])
        publications = request.get("publications", [])
        projects = request.get("projects", [])
        memberships = request.get("memberships", [])
        photo_url = request.get("photo_url")
        
        # Generate and save CV
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=personal_info,
            experience=experience,
            education=education,
            skills=skills,
            awards=awards,
            publications=publications,
            projects=projects,
            memberships=memberships,
            job_id=None,
            photo_url=photo_url,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Error saving CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save CV: {str(e)}"
        )


@router.post("/api/cv/suggestions")
async def get_cv_suggestions(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI-powered suggestions for CV content with market analysis.
    
    CRITICAL: Now uses the improved AIService with validation and retry logic.
    """
    try:
        section = request.get("section", "")
        content = request.get("content", "")
        industry = request.get("industry")
        
        # CRITICAL FIX: Use AIService directly (with validation) instead of ATSOptimizer
        # ATSOptimizer.get_suggestions doesn't use the improved validation logic
        from app.services.ai_service import AIService
        ai_service = AIService()
        suggestions = ai_service.get_realtime_suggestions(section, content, industry)
        return suggestions
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/api/cv/ats-score")
async def calculate_ats_score_endpoint(request: Dict[str, Any]):
    """
    Calculate deterministic ATS compatibility score with detailed breakdown.
    
    Uses new ATSEngine for consistent, transparent scoring across all endpoints.
    Returns both new format (ats_score, component_scores) and legacy format (overall_score, score_breakdown)
    for backward compatibility with frontend.
    """
    try:
        cv_data = request.get("cv_data", {})
        stored_hash = request.get("stored_cv_hash")
        
        # Debug: log what we received
        if not cv_data or (isinstance(cv_data, dict) and len(cv_data) == 0):
            logger.warning(
                f"ATS endpoint received empty CV data. Request keys: {list(request.keys())}. "
                f"cv_data type: {type(cv_data)}, value: {cv_data}"
            )
        
        # Don't fail on empty - just score it (scoring engine handles empty gracefully)
        # if not cv_data:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="CV data is required"
        #     )
        
        # CRITICAL: Normalize and validate CV data before scoring
        # This ensures we have complete data (experience, education, skills) regardless of what frontend sends
        from app.services.pdf_parser_service import PDFParserService
        pdf_parser = PDFParserService()
        cv_data = pdf_parser.validate_cv_data(cv_data)
        
        # Log data completeness for debugging
        experience_count = len(cv_data.get("experience", []) or cv_data.get("work_experience", []))
        education_count = len(cv_data.get("education", []))
        skills_count = len(cv_data.get("skills", {}).get("job_related_skills", [])) if isinstance(cv_data.get("skills"), dict) else 0
        logger.info(f"ATS scoring with: {experience_count} experiences, {education_count} educations, {skills_count} skills")
        
        # FIX 3: Check if we should use cached score
        force_recompute = request.get("force_recompute", False)  # Default to False - respect cache
        
        # Use new deterministic ATSEngine
        ats_engine = get_ats_engine()
        score_data = ats_engine.calculate_ats_score(cv_data, stored_hash, force_recompute)
        
        # If reused from cache, return minimal response indicating caller should use stored values
        if score_data.get("reused_from_cache"):
            logger.info("ATS score reused from cache - returning cached structure")
            return {
                "ats_score": None,
                "overall_score": None,
                "grade": None,
                "reused_from_cache": True,
                "cv_hash": score_data.get("cv_hash"),
                "message": "CV content unchanged - use stored ATS score from database"
            }
        
        logger.info(
            f"ATS Analysis: {score_data.get('ats_score', 0)}/100 ({score_data.get('ats_grade', 'D')}) "
            f"hash={score_data.get('cv_hash', 'unknown')[:16]}... "
            f"reused={score_data.get('reused_from_cache', False)}"
        )
        
        # Build backward-compatible response for frontend
        component_scores = score_data.get("component_scores", {})
        
        # Map new component names to legacy category names
        score_breakdown = {
            "keyword_match": {
                "score": component_scores.get("keyword_match", 0),
                "max": 100,
                "details": score_data.get("component_details", {}).get("keyword_match", {}).get("matched_keywords", [])
            },
            "experience_quality": {
                "score": component_scores.get("experience_quality", 0),
                "max": 100,
                "details": [score_data.get("component_details", {}).get("experience_quality", {}).get("rationale", "")]
            },
            "formatting_compatibility": {
                "score": component_scores.get("formatting", 0),
                "max": 100,
                "details": []
            },
            "completeness": {
                "score": component_scores.get("completeness", 0),
                "max": 100,
                "details": [score_data.get("component_details", {}).get("completeness", {}).get("rationale", "")]
            }
        }
        
        return {
            # New format
            "ats_score": score_data.get("ats_score", 0),
            "ats_grade": score_data.get("ats_grade", "D"),
            "cv_hash": score_data.get("cv_hash"),
            "component_scores": component_scores,
            "ats_issues": score_data.get("ats_issues", []),
            "ats_recommendations": score_data.get("ats_recommendations", []),
            
            # Legacy format for frontend compatibility
            "overall_score": score_data.get("ats_score", 0),
            "grade": score_data.get("ats_grade", "D"),
            "score_breakdown": score_breakdown,
            "issues": score_data.get("ats_issues", []),
            "recommendations": {
                "critical": [],
                "high": score_data.get("ats_recommendations", []),
                "medium": [],
                "low": []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ATS score: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate ATS score: {str(e)}"
        )


@router.post("/api/cv/generate-ats-optimized")
async def generate_ats_optimized_cv(request: Dict[str, Any]):
    """
    Generate ATS-optimized CV version with FULL TRANSPARENCY.
    
    This endpoint:
    1. Keeps original CV untouched
    2. Creates a separate optimized version
    3. Lists every change with before/after/reason
    4. Never invents experience or skills
    
    Returns:
    {
        "original_cv": {...},  # Original, unmodified
        "optimized_cv": {...},  # Separate optimized version
        "analysis": {
            "overall_score": 0-100,
            "grade": "A+",
            "score_breakdown": {...},
            "issues": [...],
            "recommendations": {...}
        },
        "changes": [
            {
                "field": "experience[0].description",
                "before": "Worked on databases",
                "after": "Designed and optimized PostgreSQL databases",
                "reason": "Improves keyword recognition and specificity"
            },
            ...
        ]
    }
    """
    try:
        cv_data = request.get("cv_data", {})
        
        if not cv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV data is required"
            )
        
        from cv.ats_analyzer import ATSAnalyzer
        import copy
        
        # 1. Analyze the CV
        analyzer = ATSAnalyzer()
        analysis = analyzer.analyze_ats_compatibility(cv_data)
        
        # 2. Generate suggested optimizations
        changes = analyzer.generate_optimizations(cv_data, analysis)
        
        # 3. Create optimized version (deep copy to keep original untouched)
        optimized_cv = copy.deepcopy(cv_data)
        
        # 4. Apply only suggested changes (never invent data)
        for change in changes:
            field_path = change["field"]
            # Parse field path like "experience[0].description"
            # and apply change safely
            apply_change_to_cv(optimized_cv, field_path, change["after"])
        
        # 5. Re-analyze optimized CV to show improvement
        optimized_analysis = analyzer.analyze_ats_compatibility(optimized_cv)
        
        logger.info(f"Generated ATS-optimized CV: {analysis['overall_score']} → {optimized_analysis['overall_score']}")
        
        return {
            "original_cv": cv_data,  # Never modified
            "optimized_cv": optimized_cv,  # Separate version
            "original_analysis": analysis,
            "optimized_analysis": optimized_analysis,
            "changes": changes,
            "score_improvement": optimized_analysis["overall_score"] - analysis["overall_score"],
            "transparency_note": "All changes shown above with before/after/reason. Original CV never modified."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ATS-optimized CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimized CV: {str(e)}"
        )


# DISABLED: Learning resources feature removed to prevent background processing delays
# def _add_learning_resources_to_job(job: Dict[str, Any], missing_skills: List[str], normalized_cv: Dict[str, Any]) -> None:
#     """Helper function to add learning resources for missing skills to a job."""
#     pass


def apply_change_to_cv(cv: Dict[str, Any], field_path: str, new_value: str) -> None:
    """Safely apply a change to CV data using field path like 'experience[0].description'."""
    import re
    
    # Parse field path
    pattern = r'(\w+)(?:\[(\d+)\])?\.?(\w+)?'
    match = re.match(pattern, field_path)
    
    if not match:
        return
    
    section, index, sub_field = match.groups()
    
    if index is not None:
        index = int(index)
        if section in cv and isinstance(cv[section], list) and index < len(cv[section]):
            if sub_field:
                cv[section][index][sub_field] = new_value
            else:
                cv[section][index] = new_value
    else:
        if section in cv:
            cv[section] = new_value


# ==================== ADVANCED CV FEATURES ====================

@router.post("/api/cv/generate-from-questions")
async def generate_cv_from_questions(request: Dict[str, Any]):
    """Generate CV from guided questionnaire answers."""
    try:
        result = advanced_cv_service.generate_cv_from_questions(request)
        return result
    except Exception as e:
        logger.error(f"Error generating CV from questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CV: {str(e)}"
        )


@router.post("/api/cv/match-job")
async def match_job_compatibility(request: Dict[str, Any]):
    """Match CV to job description and compute compatibility score."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.match_job_compatibility(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match job: {str(e)}"
        )


@router.post("/api/cv/optimize-for-job")
async def optimize_cv_for_job(request: Dict[str, Any]):
    """Generate job-optimized version of CV."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_job_optimized_cv(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing CV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize CV: {str(e)}"
        )


@router.post("/api/cv/generate-cover-letter")
async def generate_cover_letter(request: Dict[str, Any]):
    """Generate personalized cover letter."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        company_name = request.get("company_name", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_cover_letter(cv_data, job_description, company_name)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter: {str(e)}"
        )


@router.post("/api/cv/extract-skills")
async def extract_skills_from_cv(request: Dict[str, Any]):
    """Extract and categorize skills from CV."""
    try:
        cv_data = request.get("cv_data", {})
        result = advanced_cv_service.extract_skills_from_cv(cv_data)
        return result
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract skills: {str(e)}"
        )


@router.post("/api/cv/generate-interview-questions")
async def generate_interview_questions(request: Dict[str, Any]):
    """Generate interview questions based on CV and job description."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_interview_questions(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post("/api/cv/optimize-ats")
async def optimize_ats_endpoint(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Comprehensive ATS optimization analysis.
    
    CRITICAL FIX: Fetches CV from database if user_id provided to ensure same data as job search.
    This ensures same CV → same hash → same score across all endpoints.
    """
    try:
        # CRITICAL: Try to get CV from database first (same source as job search)
        user_id = request.get("user_id")
        cv_data = request.get("cv_data", {})
        stored_hash = None
        
        if user_id:
            try:
                from app.db.models import CV
                cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content:
                    # Use ORIGINAL CV data (same as job search) - not optimized_cv
                    if isinstance(cv.json_content, dict):
                        if cv.json_content.get("original_cv_data"):
                            cv_data = cv.json_content.get("original_cv_data")
                            logger.info(f"Using original_cv_data from database for user {user_id}")
                        else:
                            # Strip ATS metadata to get canonical content
                            cv_data = {k: v for k, v in cv.json_content.items() 
                                      if k not in ["ats_score", "ats_grade", "ats_metadata", "ats_analysis",
                                                  "ats_issues", "ats_recommendations", "ats_optimized_content",
                                                  "ats_changes", "optimized_cv", "is_optimized"]}
                            logger.info(f"Using json_content (stripped) from database for user {user_id}")
                        stored_hash = cv.json_content.get("cv_hash")
                        logger.info(f"Using CV from database for user {user_id}, hash={stored_hash[:16] if stored_hash else 'None'}...")
                    else:
                        logger.warning(f"CV json_content is not a dict for user {user_id}")
                else:
                    logger.warning(f"No CV found in database for user {user_id}, using request data")
            except Exception as e:
                logger.warning(f"Could not fetch CV from database: {e}, using request data", exc_info=True)
        
        # FIX 2 & 3: Lock ATS input contract - normalize CV data, respect caching
        from cv.ats_engine import ATSEngine
        from app.services.pdf_parser_service import PDFParserService
        
        ats_engine = ATSEngine()
        pdf_parser = PDFParserService()
        
        # Remove old ATS metadata to get canonical CV content
        fresh_cv_data = {k: v for k, v in cv_data.items() 
                        if k not in ["ats_score", "ats_grade", "ats_metadata", "ats_analysis", 
                                    "ats_issues", "ats_recommendations", "ats_optimized_content",
                                    "ats_changes", "created_at", "updated_at", "ats_optimized_at"]}
        
        # CRITICAL FIX: Check if CV data is nested under 'original_cv' key
        # This happens when CV comes from optimization results
        if fresh_cv_data.get("original_cv") and isinstance(fresh_cv_data.get("original_cv"), dict):
            logger.info("optimize-ats: Found 'original_cv' key, using that instead")
            original_cv = fresh_cv_data.get("original_cv")
            # Merge original_cv with top-level data (original_cv takes precedence)
            fresh_cv_data = {**fresh_cv_data, **original_cv}
            # Remove the nested original_cv key
            fresh_cv_data.pop("original_cv", None)
        
        # DEBUG: Log before validation
        logger.info(f"optimize-ats: Before validation - experience count: {len(fresh_cv_data.get('experience', []) or fresh_cv_data.get('work_experience', []) or [])}")
        logger.info(f"optimize-ats: Before validation - skills keys: {list(fresh_cv_data.get('skills', {}).keys()) if isinstance(fresh_cv_data.get('skills'), dict) else 'NOT A DICT'}")
        
        # FIX 2: Normalize CV data to ensure consistent input contract (same as job search)
        normalized_cv_data = pdf_parser.validate_cv_data(fresh_cv_data)
        
        # DEBUG: Log normalized data to diagnose issues
        logger.info(f"optimize-ats: Normalized CV data keys: {list(normalized_cv_data.keys()) if isinstance(normalized_cv_data, dict) else 'NOT A DICT'}")
        logger.info(f"optimize-ats: Has experience: {bool(normalized_cv_data.get('experience') or normalized_cv_data.get('work_experience'))}")
        logger.info(f"optimize-ats: Has skills: {bool(normalized_cv_data.get('skills') or normalized_cv_data.get('personal_skills'))}")
        logger.info(f"optimize-ats: Experience count: {len(normalized_cv_data.get('experience', []) or normalized_cv_data.get('work_experience', []) or [])}")
        
        # Use stored_hash from database if available, otherwise from request
        if not stored_hash:
            stored_hash = cv_data.get("cv_hash") or cv_data.get("ats_metadata", {}).get("cv_hash")
        
        force_recompute = request.get("force_recompute", True)  # Default to True for explicit analyze
        
        logger.info(f"Calculating ATS score: force_recompute={force_recompute}, stored_hash={stored_hash[:16] if stored_hash else 'None'}...")
        result = ats_engine.calculate_ats_score(normalized_cv_data, stored_hash, force_recompute)
        
        # DEBUG: Log the result score
        logger.info(f"optimize-ats: ATS score result: {result.get('ats_score', 'N/A')}, grade: {result.get('ats_grade', 'N/A')}")
        
        # If reused from cache, return indication that caller should use stored values
        if result.get("reused_from_cache"):
            logger.info("ATS score reused from cache (CV content unchanged)")
            # Return the cached result structure but indicate it should use stored values
            return {
                "ats_score": None,
                "score": None,
                "grade": None,
                "reused_from_cache": True,
                "cv_hash": result.get("cv_hash"),
                "message": "CV content unchanged - use stored ATS score from database"
            }
        
        # Get score from result
        score = result.get("ats_score", result.get("score", 0))
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        else:
            grade = "D"
        
        # Format result to match expected structure with all detailed fields from ATSEngine
        # Include ALL analysis details for transparency
        component_scores = result.get("component_scores", {})
        component_details = result.get("component_details", {})
        analysis_details = result.get("analysis_details", {})
        
        return {
            "ats_score": score,
            "score": score,
            "grade": result.get("ats_grade", grade),
            "cv_hash": result.get("cv_hash"),
            
            # Component scores breakdown
            "component_scores": component_scores,
            "section_scores": component_scores,  # Alias for compatibility
            "component_details": component_details,  # Full component details
            
            # Analysis and feedback
            "section_feedback": result.get("component_feedback", {}),
            "analysis_details": analysis_details,
            
            # Keywords analysis
            "keyword_density": analysis_details.get("keyword_density", component_details.get("keyword_match", {}).get("keyword_count", 0)),
            "keywords_found": component_details.get("keyword_match", {}).get("matched_keywords", []) or result.get("keywords_found", []),
            "keywords_missing": result.get("keywords_missing", []),
            
            # Formatting and completeness
            "formatting_score": component_scores.get("formatting", 0),
            "section_completeness": analysis_details.get("section_completeness", {}),
            
            # Issues and recommendations
            "issues": result.get("ats_issues", []),
            "recommendations": result.get("ats_recommendations", []),
            "suggestions": result.get("ats_recommendations", []),  # Alias for compatibility
            
            # Score breakdown explanation
            "score_breakdown": {
                "keyword_match": {
                    "score": component_scores.get("keyword_match", 0),
                    "weight": "30%",
                    "details": component_details.get("keyword_match", {})
                },
                "experience_quality": {
                    "score": component_scores.get("experience_quality", 0),
                    "weight": "20%",
                    "details": component_details.get("experience_quality", {})
                },
                "formatting": {
                    "score": component_scores.get("formatting", 0),
                    "weight": "15%",
                    "details": component_details.get("formatting", {})
                },
                "completeness": {
                    "score": component_scores.get("completeness", 0),
                    "weight": "10%",
                    "details": component_details.get("completeness", {})
                },
                "quantification": {
                    "score": component_scores.get("quantification", 0),
                    "weight": "10%",
                    "details": component_details.get("quantification", {})
                },
                "role_consistency": {
                    "score": component_scores.get("role_consistency", 0),
                    "weight": "10%",
                    "details": component_details.get("role_consistency", {})
                },
                "red_flags_penalty": {
                    "penalty": component_scores.get("red_flags_penalty", 0),
                    "max_penalty": 5,
                    "details": component_details.get("red_flags_penalty", {})
                }
            },
            
            # How the score was calculated
            "score_explanation": f"Your CV scored {score}/100 based on: Keyword Match ({component_scores.get('keyword_match', 0)}/100 × 30%), Experience Quality ({component_scores.get('experience_quality', 0)}/100 × 20%), Formatting ({component_scores.get('formatting', 0)}/100 × 15%), Completeness ({component_scores.get('completeness', 0)}/100 × 10%), Quantification ({component_scores.get('quantification', 0)}/100 × 10%), Role Consistency ({component_scores.get('role_consistency', 0)}/100 × 10%)"
        }
    except Exception as e:
        logger.error(f"Error optimizing ATS: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize ATS: {str(e)}"
        )


@router.post("/api/cv/get-optimized")
async def get_optimized_cv_endpoint(request: Dict[str, Any]):
    """Get the optimized version of the CV with FULL transparency of all changes."""
    try:
        cv_data = request.get("cv_data", {})
        
        if not cv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV data is required"
            )
        
        # Optimize the CV for ATS (returns optimized_cv, original_cv, changes)
        from app.services.ai_service import AIService
        ai_service = AIService()
        optimization_result = ai_service.optimize_for_ats(cv_data)
        
        # Extract results
        optimized_cv = optimization_result.get("optimized_cv", {})
        original_cv = optimization_result.get("original_cv", cv_data)  # Always preserve original
        changes = optimization_result.get("changes", [])
        optimization_metadata = optimization_result.get("optimization_metadata", {})
        
        # Calculate ATS scores for both original and optimized
        from app.services.ai_service import AIService as AIServiceForScore
        ai_service_score = AIServiceForScore()
        original_score_data = ai_service_score.calculate_ats_score(original_cv)
        optimized_score_data = ai_service_score.calculate_ats_score(optimized_cv)
        
        original_score = original_score_data.get("score", 0)
        optimized_score = optimized_score_data.get("score", 0)
        score_increase = optimized_score - original_score
        
        # Extract keywords that were added/emphasized from changes
        keywords_added = []
        for change in changes:
            if "keyword" in change.get("reason", "").lower():
                # Try to extract keywords from the change
                after_text = change.get("after", "")
                # Simple extraction - look for capitalized words
                keywords = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', after_text)
                keywords_added.extend(keywords[:2])  # Limit per change
        
        # Generate improvements list from changes
        improvements = []
        for change in changes:
            improvements.append(change.get("change", ""))
        
        return {
            "optimized_cv": optimized_cv,
            "original_cv": original_cv,  # Always return original, never modified
            "optimization_details": {
                "changes": changes,  # Full list with before/after/reason
                "keywords_added": list(set(keywords_added))[:15],  # Unique keywords
                "improvements": improvements,
                "original_score": original_score,
                "optimized_score": optimized_score,
                "score_increase": score_increase,
                "keyword_density": optimization_metadata.get("keyword_density", 0),
                "formatting_score": optimization_metadata.get("formatting_score", 0),
                "section_completeness": optimization_metadata.get("section_completeness", {}),
                "changes_count": len(changes),
                "optimized_at": optimization_metadata.get("optimized_at")
            }
        }
    except Exception as e:
        logger.error(f"Error getting optimized CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimized CV: {str(e)}"
        )


@router.post("/api/cv/export-pdf")
async def export_cv_pdf_endpoint(request: Dict[str, Any]):
    """Export CV to PDF format."""
    try:
        cv_data = request.get("cv_data", {})
        
        if not cv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV data is required"
            )
        
        # DEBUG: Log the structure being sent
        logger.info(f"[PDF EXPORT] cv_data keys: {list(cv_data.keys())}")
        logger.info(f"[PDF EXPORT] has json_content: {bool(cv_data.get('json_content'))}")
        if cv_data.get("json_content"):
            logger.info(f"[PDF EXPORT] json_content keys: {list(cv_data['json_content'].keys())}")
            logger.info(f"[PDF EXPORT] json_content.experience: {len(cv_data['json_content'].get('experience', []))} items")
            logger.info(f"[PDF EXPORT] json_content.education: {len(cv_data['json_content'].get('education', []))} items")
        
        # Export to PDF using CVGenerator
        pdf_bytes = cv_generator.export_to_pdf(cv_data)
        
        # Get name for filename
        personal_info = cv_data.get("personal_info", {})
        if not personal_info:
            personal_info = cv_data.get("json_content", {}).get("personal_info", {})
        name = personal_info.get("full_name", "CV") or f"{personal_info.get('first_name', '')} {personal_info.get('surname', '')}".strip() or "CV"
        filename = f"CV-{name.replace(' ', '-')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Error exporting CV to PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CV to PDF: {str(e)}"
        )


@router.post("/api/cv/export-docx")
async def export_cv_docx_endpoint(request: Dict[str, Any]):
    """Export CV to DOCX format."""
    try:
        cv_data = request.get("cv_data", {})
        
        if not cv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV data is required"
            )
        
        logger.info(f"[DOCX EXPORT] Exporting CV to DOCX format")
        
        # Export to DOCX using CVGenerator
        docx_bytes = cv_generator.export_to_docx(cv_data)
        
        # Get name for filename
        personal_info = cv_data.get("personal_info", {})
        if not personal_info:
            personal_info = cv_data.get("json_content", {}).get("personal_info", {})
        name = personal_info.get("full_name", "CV") or f"{personal_info.get('first_name', '')} {personal_info.get('surname', '')}".strip() or "CV"
        filename = f"CV-{name.replace(' ', '-')}.docx"
        
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Error exporting CV to DOCX: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CV to DOCX: {str(e)}"
        )


@router.post("/api/proposals/generate")
async def generate_proposal_endpoint(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Generate a customized freelancing proposal."""
    try:
        job_description = request.get("job_description", "")
        client_requirements = request.get("client_requirements", "")
        user_id = request.get("user_id")
        tone = request.get("tone", "professional")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        # Get user's CV data if user_id provided
        user_skills = []
        user_experience = []
        
        if user_id:
            from app.db.models import CV
            cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
            if cv and cv.json_content:
                # Extract skills
                skills_data = cv.json_content.get("personal_skills", {}) or cv.json_content.get("skills", {})
                if isinstance(skills_data, dict):
                    user_skills = (
                        skills_data.get("job_related_skills", []) +
                        skills_data.get("technical_skills", []) +
                        skills_data.get("computer_skills", [])
                    )
                elif isinstance(skills_data, list):
                    user_skills = skills_data
                
                # Extract experience
                user_experience = (
                    cv.json_content.get("work_experience", []) or
                    cv.json_content.get("experience", [])
                )
        
        # If no user data, use provided skills/experience from request
        if not user_skills:
            user_skills = request.get("user_skills", [])
        if not user_experience:
            user_experience = request.get("user_experience", [])
        
        # Generate proposal
        result = proposal_service.generate_proposal(
            job_description=job_description,
            client_requirements=client_requirements,
            user_skills=user_skills,
            user_experience=user_experience,
            tone=tone
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proposal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposal: {str(e)}"
        )


@router.post("/api/cv/career-recommendations")
async def get_career_recommendations(request: Dict[str, Any]):
    """Get career path recommendations based on CV."""
    try:
        cv_data = request.get("cv_data", {})
        result = advanced_cv_service.generate_career_recommendations(cv_data)
        return result
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/api/cv/field-suggestions")
async def get_field_suggestions(request: Dict[str, Any]):
    """Get 10+ AI suggestions for a specific CV field."""
    try:
        field = request.get("field", "")
        current_value = request.get("current_value", "")
        context = request.get("context", {})
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field is required"
            )
        
        result = advanced_cv_service.get_field_suggestions(field, current_value, context)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/api/cv/upload-linkedin-pdf")
async def upload_linkedin_pdf(
    pdf_file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload LinkedIn CV PDF and automatically extract information using AI.
    Returns structured CV data ready for job matching.
    """
    try:
        # Validate file type
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Validate file size (10MB max)
        content = await pdf_file.read()
        await pdf_file.seek(0)  # Reset file pointer
        
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum of 10MB"
            )
        
        # Save the original PDF file for preview
        import shutil
        import uuid
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{user_id}_cv_{uuid.uuid4().hex}.pdf"
        pdf_file_path = upload_dir / unique_filename
        
        # Save PDF file
        with open(pdf_file_path, "wb") as buffer:
            buffer.write(content)
        
        pdf_url = f"/static/uploads/{unique_filename}"
        logger.info(f"Saved PDF file: {pdf_url}")
        
        # Reset file pointer for parsing
        await pdf_file.seek(0)
        
        # Import PDF parser service
        from app.services.pdf_parser_service import PDFParserService
        pdf_parser = PDFParserService()
        
        # Extract text from PDF
        logger.info(f"Extracting text from PDF for user {user_id}")
        pdf_text = await pdf_parser.extract_text_from_pdf(pdf_file)
        
        if not pdf_text or len(pdf_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from PDF. Please ensure the PDF is not scanned or encrypted."
            )
        
        
        # Parse with Mistral AI
        logger.info("Parsing CV with Mistral AI")
        cv_data = await pdf_parser.parse_linkedin_cv(pdf_text)
        cv_data = pdf_parser.validate_cv_data(cv_data)
        
        # Store original CV for comparison
        import copy
        original_cv_data = copy.deepcopy(cv_data)

        # Quick upload: skip ATS scoring and optimization; keep original content
        improved_cv_data = cv_data
        ats_score = None
        ats_grade = None
        improved_cv_hash = None
        original_cv_hash = None
        optimization_changes = []
        optimization_metadata = {}
        logger.info("Quick upload: skipping ATS scoring; ATS shown only in optimizer flow")
        
        # CRITICAL: Store original CV separately - NEVER overwrite
        improved_cv_data["original_cv_data"] = original_cv_data  # Store original for comparison
        improved_cv_data["is_optimized"] = False  # Not optimized in quick upload
        
        # Store PDF URL in improved_cv_data for later retrieval (before saving)
        improved_cv_data["pdf_url"] = pdf_url
        improved_cv_data["original_pdf_url"] = pdf_url  # Explicitly mark as original
        
        # CRITICAL: Create credentials from parsed CV data (single source of truth)
        # Do this BEFORE calling generate_cv to ensure credentials exist even if CV save fails
        from app.services.trust_service import CredentialService
        from app.db.models import CredentialType, CredentialSource, Credential
        from datetime import datetime
        
        credential_service = CredentialService()
        credentials_created_from_pdf = []
        
        # Create education credentials from parsed data
        education_list = improved_cv_data.get("education", [])
        for edu in education_list:
            if not isinstance(edu, dict):
                continue
            degree = edu.get("degree") or edu.get("qualification") or ""
            institution = edu.get("institution") or edu.get("school") or ""
            
            if not degree:
                continue
            
            try:
                # Check if credential already exists
                existing = (
                    db.query(Credential)
                    .filter(
                        Credential.user_id == user_id,
                        Credential.type == CredentialType.EDUCATION,
                        Credential.title == degree,
                        Credential.organization == institution,
                    )
                    .first()
                )
                
                if not existing:
                    start_date = None
                    if edu.get("start_date"):
                        try:
                            if isinstance(edu["start_date"], str):
                                start_date = datetime.fromisoformat(edu["start_date"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    end_date = None
                    if edu.get("graduation_year"):
                        try:
                            end_date = datetime(int(edu["graduation_year"]), 1, 1)
                        except:
                            pass
                    elif edu.get("end_date"):
                        try:
                            if isinstance(edu["end_date"], str):
                                end_date = datetime.fromisoformat(edu["end_date"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    credential = credential_service.create_credential(
                        db=db,
                        user_id=user_id,
                        credential_type=CredentialType.EDUCATION,
                        title=degree,
                        organization=institution,
                        start_date=start_date,
                        end_date=end_date,
                        description=edu.get("field_of_study", ""),
                        source=CredentialSource.SYSTEM_GENERATED,  # From PDF parsing
                    )
                    credentials_created_from_pdf.append(credential.id)
            except Exception as e:
                logger.error(f"Error creating education credential from PDF: {e}")
                continue
        
        # Create employment credentials from parsed data
        experience_list = improved_cv_data.get("experience", []) or improved_cv_data.get("work_experience", [])
        for exp in experience_list:
            if not isinstance(exp, dict):
                continue
            job_title = exp.get("job_title") or exp.get("position") or ""
            company = exp.get("company") or exp.get("employer") or ""
            
            if not job_title and not company:
                continue
            
            try:
                # Check if credential already exists
                existing = (
                    db.query(Credential)
                    .filter(
                        Credential.user_id == user_id,
                        Credential.type == CredentialType.EMPLOYMENT,
                        Credential.title == job_title,
                        Credential.organization == company,
                    )
                    .first()
                )
                
                if not existing:
                    start_date = None
                    if exp.get("start_date"):
                        try:
                            if isinstance(exp["start_date"], str):
                                start_date = datetime.fromisoformat(exp["start_date"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    end_date = None
                    if exp.get("end_date") and exp.get("end_date") != "Present":
                        try:
                            if isinstance(exp["end_date"], str):
                                end_date = datetime.fromisoformat(exp["end_date"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    credential = credential_service.create_credential(
                        db=db,
                        user_id=user_id,
                        credential_type=CredentialType.EMPLOYMENT,
                        title=job_title or "Employee",
                        organization=company,
                        start_date=start_date,
                        end_date=end_date,
                        description=exp.get("description", ""),
                        source=CredentialSource.SYSTEM_GENERATED,  # From PDF parsing
                    )
                    credentials_created_from_pdf.append(credential.id)
            except Exception as e:
                logger.error(f"Error creating employment credential from PDF: {e}")
                continue
        
        logger.info(f"Created {len(credentials_created_from_pdf)} credentials from PDF upload for user {user_id}")
        
        # Save improved CV to database with ATS score included
        # Note: generate_cv() will also create credentials, but we've already created them above
        # This ensures credentials exist even if CV save fails
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=improved_cv_data.get("personal_info", {}),
            experience=improved_cv_data.get("experience", []),
            education=improved_cv_data.get("education", []),
            skills=improved_cv_data.get("skills", {}),
            awards=improved_cv_data.get("awards", []),
            publications=improved_cv_data.get("publications", []),
            projects=improved_cv_data.get("projects", []),
            memberships=[],
            job_id=None,
            photo_url=None,
            original_file_url=pdf_url,
            original_file_name=unique_filename,
            db=db
        )
        
        # STEP 3: Match jobs based on improved CV (BEFORE updating database) using unified extractor
        job_matches = []
        try:
            keyword_extractor = JobKeywordExtractor()
            tiers = keyword_extractor.extract_keywords(improved_cv_data)
            primary_keywords = tiers.get("primary_search", [])
            platform_keywords = {
                "remoteok": keyword_extractor.get_platform_keywords(improved_cv_data, "remoteok"),
                "arbeitnow": keyword_extractor.get_platform_keywords(improved_cv_data, "arbeitnow"),
                "freelancer": keyword_extractor.get_platform_keywords(improved_cv_data, "freelancer"),
                "adzuna": keyword_extractor.get_platform_keywords(improved_cv_data, "adzuna"),
            }
            
            aggregator = JobAggregator()
            
            # CRITICAL: Normalize CV data BEFORE domain filtering
            # Domain extractor expects education, experience, skills at top level
            # improved_cv_data may have nested original_cv_data or other structures
            from app.services.pdf_parser_service import PDFParserService
            pdf_parser = PDFParserService()
            normalized_cv_for_filtering = pdf_parser.validate_cv_data(improved_cv_data.copy())
            logger.info(f"[QUICK UPLOAD] Normalized CV data for domain filtering - has education: {bool(normalized_cv_for_filtering.get('education'))}, has experience: {bool(normalized_cv_for_filtering.get('experience') or normalized_cv_for_filtering.get('work_experience'))}, has skills: {bool(normalized_cv_for_filtering.get('skills') or normalized_cv_for_filtering.get('personal_skills'))}")
            
            # Apply timeout and domain filtering
            from cv.timeout_utils import safe_execute_with_timeout
            job_matches = safe_execute_with_timeout(
                aggregator.search_jobs,
                timeout_seconds=15,
                fallback=[],
                keywords=primary_keywords,
                limit=100,  # Increased from 30 to 100 for more job variety
                platform_keywords=platform_keywords,
                cv_data=normalized_cv_for_filtering  # Use normalized CV data for domain filtering
            )
            
            # Remove duplicates based on title, company, AND source
            seen = set()
            unique_jobs = []
            for job in job_matches:
                title = job.get("title", "").strip().lower()
                company = job.get("company", job.get("company_name", "")).strip().lower()
                source = job.get("source", "Unknown")
                key = (title, company, source)
                if key not in seen and title and company:
                    seen.add(key)
                    unique_jobs.append(job)
            
            from collections import defaultdict
            jobs_by_source = defaultdict(list)
            for job in unique_jobs:
                source = job.get("source", "Unknown")
                jobs_by_source[source].append(job)
            logger.info(f"Jobs grouped by source: {dict((k, len(v)) for k, v in jobs_by_source.items())}")
            
            # Interleave jobs from different sources for variety
            interleaved = []
            max_per_source = max(len(jobs) for jobs in jobs_by_source.values()) if jobs_by_source else 0

            # Track which jobs we've added to avoid duplicates
            added_job_keys = set()

            logger.info(f"Job aggregation: {dict((k, len(v)) for k, v in jobs_by_source.items())}")
            logger.info(f"Max jobs per source: {max_per_source}, Total unique jobs before interleaving: {len(unique_jobs)}")

            # Increased limit to match new job search limit (100)
            interleave_limit = min(100, len(unique_jobs))  # Use actual limit or available jobs

            # Interleave jobs round-robin style from each source
            for i in range(max_per_source):
                if len(interleaved) >= interleave_limit:
                    break
                for source_name, source_jobs in jobs_by_source.items():
                    if len(interleaved) >= interleave_limit:
                        break
                    if i < len(source_jobs):
                        job = source_jobs[i]
                        # Create unique key for this job
                        job_key = (job.get("title", "").strip().lower(), 
                                 job.get("company", job.get("company_name", "")).strip().lower(), 
                                 job.get("source", "Unknown"))
                        # Only add if not already added
                        if job_key not in added_job_keys and job_key[0] and job_key[1]:
                            interleaved.append(job)
                            added_job_keys.add(job_key)

            # If we still have space and more jobs, add remaining from all sources
            # Increased limit to match new job search limit (100)
            if len(interleaved) < interleave_limit:
                for job in unique_jobs:
                    if len(interleaved) >= interleave_limit:
                        break
                    job_key = (job.get("title", "").strip().lower(), 
                             job.get("company", job.get("company_name", "")).strip().lower(), 
                             job.get("source", "Unknown"))
                    if job_key not in added_job_keys and job_key[0] and job_key[1]:
                        interleaved.append(job)
                        added_job_keys.add(job_key)

            job_matches = interleaved  # Return all interleaved jobs (up to 100)
            logger.info(f"Final job matches after interleaving: {len(job_matches)} jobs from {len(jobs_by_source)} sources")

            # Log source breakdown for debugging
            final_sources = {}
            for job in job_matches:
                source = job.get("source", "Unknown")
                final_sources[source] = final_sources.get(source, 0) + 1
            logger.info(f"Final job distribution by source: {final_sources}")
        except Exception as e:
            logger.error(f"Job matching error: {e}")
            # Ensure job_matches is always defined even if error occurs
            if not job_matches:
                job_matches = []
        
        # STEP 4: Update CV in database with job matches and PDF URL (ATS omitted on quick upload)
        from app.db.models import CV
        saved_cv = db.query(CV).filter(CV.id == result.get("id")).first()
        if saved_cv and saved_cv.json_content:
            # Remove ATS fields on quick upload to avoid confusing early scores
            for key in ["ats_score", "ats_grade", "ats_metadata", "cv_hash", "original_cv_hash"]:
                saved_cv.json_content.pop(key, None)
            # Store job search context for consistency across flows
            # CRITICAL: Ensure job_matches is a list (not None)
            if job_matches is None:
                job_matches = []
                logger.warning(f"[QUICK UPLOAD] job_matches was None - converting to empty list for CV {saved_cv.id}")
            
            saved_cv.json_content["stored_job_matches"] = job_matches
            logger.info(f"[QUICK UPLOAD] Setting stored_job_matches for CV {saved_cv.id} with {len(job_matches)} jobs")
            
            # Extract and store CV domain and parsed skills (REQUIRED for deterministic matching)
            try:
                from cv.domain_extractor import DomainExtractor
                from cv.timeout_utils import safe_execute_with_timeout
                
                domain_extractor = DomainExtractor()
                # Extract CV domain with timeout
                cv_domains = safe_execute_with_timeout(
                    domain_extractor.extract_domains,
                    timeout_seconds=15,
                    fallback=set(),
                    cv_data=normalized_cv_for_filtering
                )
                
                # Extract parsed skills
                parsed_skills = domain_extractor._extract_skills(normalized_cv_for_filtering)
                
                # Store domain as list (JSON serializable)
                saved_cv.json_content["cv_domain"] = list(cv_domains) if cv_domains else []
                saved_cv.json_content["parsed_skills"] = parsed_skills
                
                logger.info(f"[QUICK UPLOAD] Stored CV domain: {list(cv_domains)}, parsed_skills count: {len(parsed_skills)}")
            except Exception as e:
                logger.error(f"[QUICK UPLOAD] Failed to extract/store CV domain and skills: {str(e)}", exc_info=True)
                saved_cv.json_content["cv_domain"] = []
                saved_cv.json_content["parsed_skills"] = []
            
            # Persist unified keyword tiers and platform-specific keywords
            try:
                keyword_extractor = JobKeywordExtractor()
                tiers = keyword_extractor.extract_keywords(improved_cv_data)
                primary_keywords = tiers.get("primary_search", [])
                platform_kw = {
                    "remoteok": keyword_extractor.get_platform_keywords(improved_cv_data, "remoteok"),
                    "arbeitnow": keyword_extractor.get_platform_keywords(improved_cv_data, "arbeitnow"),
                    "freelancer": keyword_extractor.get_platform_keywords(improved_cv_data, "freelancer"),
                    "adzuna": keyword_extractor.get_platform_keywords(improved_cv_data, "adzuna"),
                }
                saved_cv.json_content["job_search"] = {
                    "keywords_tiers": tiers,
                    "primary_keywords": primary_keywords,
                    "platform_keywords": platform_kw,
                    "last_results_count": len(job_matches),
                    "cv_domain": saved_cv.json_content.get("cv_domain", []),  # Include domain in job_search context
                    "parsed_skills": saved_cv.json_content.get("parsed_skills", []),  # Include skills in job_search context
                }
                # For backward compatibility
                saved_cv.json_content["job_match_keywords"] = primary_keywords
            except Exception:
                # If extractor fails, ensure we still set basic keywords
                saved_cv.json_content["job_match_keywords"] = []
            # Store PDF URL for preview
            saved_cv.json_content["pdf_url"] = pdf_url
            # Do not set ai_score on quick upload
            
            # CRITICAL: Flag json_content as modified so SQLAlchemy detects the change
            # This is required for JSON/JSONB columns when modifying dict in-place
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(saved_cv, "json_content")
            
            db.commit()
            db.refresh(saved_cv)
            logger.info(f"[QUICK UPLOAD] Updated CV {saved_cv.id} with {len(job_matches)} job matches, stored_job_matches key exists: {'stored_job_matches' in saved_cv.json_content}, PDF: {pdf_url}")
        
        # Ensure improved_cv_data has normalized structure for frontend
        # Normalize experience
        if "work_experience" in improved_cv_data and "experience" not in improved_cv_data:
            improved_cv_data["experience"] = improved_cv_data["work_experience"]
        elif "experience" in improved_cv_data and "work_experience" not in improved_cv_data:
            improved_cv_data["work_experience"] = improved_cv_data["experience"]
        
        # Normalize skills
        if "personal_skills" in improved_cv_data and "skills" not in improved_cv_data:
            improved_cv_data["skills"] = improved_cv_data["personal_skills"]
        elif "skills" in improved_cv_data and "personal_skills" not in improved_cv_data:
            improved_cv_data["personal_skills"] = improved_cv_data["skills"]
        
        return {
            "success": True,
            "message": "CV processed and improved successfully",
            "cv_data": improved_cv_data,
            "cv_id": result.get("id"),
            "job_matches": job_matches,
            "match_count": len(job_matches),
            # ATS score intentionally omitted on quick upload; shown only in optimizer flow
            "ats_score": None,
            "ats_grade": None,
            "pdf_url": pdf_url,  # Include PDF URL in response
            "improvements": {
                "ats_optimized": False,
                "keyword_density": None,
                "formatting_score": None,
                "section_completeness": {},
                "recommendations": [],
                "issues": [],
                "fixes": []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading LinkedIn PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


# ==================== GLOBAL JOB MATCHING ENDPOINTS ====================

@router.get("/api/jobs/search-global")
async def search_global_jobs(
    query: str,
    location: Optional[str] = None,
    limit: int = 20
):
    """Search global job market across multiple APIs."""
    try:
        jobs = global_job_api.search_global_jobs(query, location, limit)
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error searching global jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search jobs: {str(e)}"
        )


@router.get("/api/jobs/debug-sources")
async def debug_job_sources(
    keywords: str = "python developer",
    limit: int = 5
):
    """Debug endpoint to test individual job sources."""
    from cv.job_aggregator import JobAggregator
    from app.core.config import settings
    
    aggregator = JobAggregator()
    keywords_list = keywords.split() if keywords else []
    
    results = {
        "config": {
            "rapidapi_key": "SET" if aggregator.rapidapi_key else "NOT SET",
            "adzuna_app_id": getattr(settings, 'ADZUNA_APP_ID', None),
            "adzuna_api_key": "SET" if getattr(settings, 'ADZUNA_API_KEY', None) else "NOT SET",
        },
        "sources": {}
    }
    
    # Test Y-Combinator
    try:
        yc_jobs = aggregator._search_rapidapi_yc(keywords_list, limit)
        results["sources"]["y_combinator"] = {
            "status": "success",
            "count": len(yc_jobs),
            "jobs": yc_jobs[:3]  # First 3 for preview
        }
    except Exception as e:
        results["sources"]["y_combinator"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test Internships
    try:
        internship_jobs = aggregator._search_rapidapi_internships(keywords_list, limit)
        results["sources"]["internships"] = {
            "status": "success",
            "count": len(internship_jobs),
            "jobs": internship_jobs[:3]  # First 3 for preview
        }
    except Exception as e:
        results["sources"]["internships"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test Adzuna
    try:
        adzuna_jobs = aggregator._search_adzuna(keywords_list, None, limit)
        results["sources"]["adzuna"] = {
            "status": "success",
            "count": len(adzuna_jobs),
            "jobs": adzuna_jobs[:3]  # First 3 for preview
        }
    except Exception as e:
        results["sources"]["adzuna"] = {
            "status": "error",
            "error": str(e)
        }
    
    return results


@router.post("/api/jobs/match")
async def match_jobs_endpoint(
    user_id: int,
    limit: int = 10,
    category: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Match user to relevant job opportunities from integrations (RemoteOK, Freelancer.com) only."""
    try:
        # Get user's CV
        from app.db.models import CV
        cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
        
        if not cv or not cv.json_content:
            # If no CV, return jobs based on basic user info
            query = "software engineer"  # Default query
        else:
            # Extract skills/keywords from CV for search
            cv_data = cv.json_content
            skills = []
            if cv_data.get("skills"):
                skills_data = cv_data["skills"]
                if isinstance(skills_data, dict):
                    skills.extend(skills_data.get("job_related_skills", []))
                    skills.extend(skills_data.get("computer_skills", []))
                elif isinstance(skills_data, list):
                    skills = [s.get("name", s) if isinstance(s, dict) else s for s in skills_data]
            
            query = " ".join(skills[:5]) if skills else "software engineer"
        
        # Use global job API to search and match
        matched_jobs = global_job_api.match_cv_to_global_jobs(
            cv_data=cv.json_content if cv else {},
            query=query,
            location=location,
            limit=limit * 2  # Get more to filter by category
        )
        
        # Filter by category if provided (based on job title/description)
        if category:
            category_lower = category.lower()
            matched_jobs = [
                job for job in matched_jobs
                if category_lower in job.get("title", "").lower() or 
                   category_lower in job.get("description", "").lower() or
                   category_lower in job.get("source", "").lower()
            ]
        
        # Limit results
        matched_jobs = matched_jobs[:limit]
        
        # Format matches similar to old format for compatibility
        formatted_matches = []
        for job in matched_jobs:
            formatted_matches.append({
                "job_id": None,  # Integration jobs don't have database IDs
                "job_title": job.get("title", ""),
                "startup_id": None,
                "startup_name": job.get("company", ""),
                "startup_sector": category,
                "location": job.get("location", ""),
                "match_score": job.get("match_score", 0.0),
                "source": job.get("source", "Unknown"),
                "applyUrl": job.get("applyUrl"),
                "skills": job.get("skills", []),
            })
        
        return {"matches": formatted_matches, "count": len(formatted_matches)}
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match jobs: {str(e)}"
        )


@router.post("/api/jobs/match-global")
async def match_global_jobs(
    user_id: int,
    query: str,
    location: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Match user CV to global job opportunities."""
    try:
        # Get user's CV
        cv = cv_generator.get_cv(user_id, db)
        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found. Please create a CV first."
            )
        
        # Match to global jobs
        matched_jobs = global_job_api.match_cv_to_global_jobs(
            cv_data=cv["json_content"],
            query=query,
            location=location,
            limit=limit
        )
        
        return {"matches": matched_jobs, "count": len(matched_jobs)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching global jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match global jobs: {str(e)}"
        )


class JobSearchRequest(BaseModel):
    """Request model for job search based on CV keywords."""
    keywords: List[str] = []  # Default to empty list instead of required
    job_titles: Optional[List[str]] = None
    location: Optional[str] = None
    limit: int = 100  # Increased from 50 to 100 for more job variety
    user_id: Optional[int] = None  # Optional user_id to retrieve stored job matches


@router.post("/api/cv/jobs")
async def search_jobs_from_cv(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search jobs based on CV keywords and job titles.
    Uses ONLY external integrations (RemoteOK, Freelancer.com, Arbeitnow, Adzuna) - NO database jobs.
    
    FIXED: Now uses the SAME keyword extraction logic as upload_linkedin_pdf to ensure consistency.
    Also checks for stored job matches from upload first.
    """
    try:
        logger.info(f"Searching jobs for keywords: {request.keywords} (integrations only)")
        
        # STEP 1: ALWAYS check for stored job matches from Quick Upload FIRST
        # This is the SINGLE SOURCE OF TRUTH - never re-compute if stored matches exist
        # MATCH ONCE, REUSE EVERYWHERE - prevents "Jobs not found" after Quick Upload
        user_id = request.user_id
        logger.info(f"[MATCH REUSE] Starting search_jobs_from_cv - user_id: {user_id}, keywords: {request.keywords}")
        stored_jobs = []
        
        if user_id:
            try:
                from app.db.models import CV
                cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
                
                logger.info(f"[MATCH REUSE] CV lookup - user_id: {user_id}, CV found: {cv is not None}, CV ID: {cv.id if cv else None}, has json_content: {cv.json_content is not None if cv else False}")
                
                if cv and cv.json_content:
                    # Check if stored_job_matches exists (could be None, empty list, or list with jobs)
                    stored_jobs = cv.json_content.get("stored_job_matches")
                    stored_keywords = cv.json_content.get("job_match_keywords", [])
                    stored_count = cv.json_content.get("job_search", {}).get("last_results_count", 0)
                    
                    # Handle None or empty list
                    if stored_jobs is None:
                        stored_jobs = []
                    elif not isinstance(stored_jobs, list):
                        logger.warning(f"[MATCH REUSE] stored_job_matches is not a list: {type(stored_jobs)}")
                        stored_jobs = []
                    
                    logger.info(f"[MATCH REUSE] Stored matches check - CV ID: {cv.id}, stored_jobs type: {type(stored_jobs)}, stored_jobs count: {len(stored_jobs) if isinstance(stored_jobs, list) else 0}, stored_keywords: {len(stored_keywords) if stored_keywords else 0}, stored_count: {stored_count}")
                    logger.info(f"[MATCH REUSE] json_content keys (first 15): {list(cv.json_content.keys())[:15]}")
                    
                    # Debug: Check if stored_job_matches key exists at all
                    if "stored_job_matches" not in cv.json_content:
                        logger.warning(f"[MATCH REUSE] WARNING: 'stored_job_matches' key does NOT exist in json_content for CV {cv.id}")
                    else:
                        logger.info(f"[MATCH REUSE] 'stored_job_matches' key exists, value type: {type(cv.json_content.get('stored_job_matches'))}, length: {len(cv.json_content.get('stored_job_matches')) if isinstance(cv.json_content.get('stored_job_matches'), list) else 'N/A'}")
                    
                    # CRITICAL: If stored jobs exist, ALWAYS return them immediately
                    # This ensures CV Editor shows the SAME jobs as Quick Upload
                    # No re-computation, no keyword matching, no domain filtering needed
                    if stored_jobs and len(stored_jobs) > 0:
                        logger.info(f"[MATCH REUSE] Found {len(stored_jobs)} stored job matches from Quick Upload for user {user_id}")
                        logger.info(f"[MATCH REUSE] Stored keywords: {stored_keywords}")
                        logger.info(f"[MATCH REUSE] Stored count: {stored_count}")
                        logger.info(f"[MATCH REUSE] Returning stored matches - NO RE-COMPUTATION")
                        
                        # Return ALL stored jobs immediately (this is the SINGLE SOURCE OF TRUTH)
                        # Don't slice by request.limit - return ALL stored matches to ensure consistency
                        # This ensures CV Editor shows the SAME jobs as Quick Upload
                        return_jobs = stored_jobs  # Return all stored jobs, not limited
                        
                        # NEW: Add job-specific ATS scores to stored jobs if CV data is available
                        try:
                            from cv.ats_engine import ATSEngine
                            from app.services.pdf_parser_service import PDFParserService
                            
                            # Get CV data for ATS scoring
                            cv_data_for_ats = cv.json_content
                            if isinstance(cv_data_for_ats, dict):
                                # Extract original CV data if nested
                                if cv_data_for_ats.get("original_cv_data"):
                                    cv_data_for_ats = cv_data_for_ats.get("original_cv_data")
                                elif cv_data_for_ats.get("original_cv"):
                                    cv_data_for_ats = cv_data_for_ats.get("original_cv")
                                
                                pdf_parser = PDFParserService()
                                normalized_cv = pdf_parser.validate_cv_data(cv_data_for_ats)
                                
                                # Calculate generic ATS score once
                                ats_engine = ATSEngine()
                                generic_ats_result = ats_engine.calculate_ats_score(normalized_cv, force_recompute=False)
                                generic_ats_score = generic_ats_result.get("ats_score", 0)
                                
                                # Add job-specific ATS scores to each job
                                for job in return_jobs:
                                    try:
                                        job_context = {
                                            "job_title": job.get("title", ""),
                                            "job_description": job.get("description", ""),
                                            "job_skills": job.get("skills", []) if isinstance(job.get("skills"), list) else []
                                        }
                                        
                                        # Calculate job-specific ATS score
                                        job_ats_result = ats_engine.calculate_ats_score(
                                            normalized_cv,
                                            stored_hash=generic_ats_result.get("cv_hash"),
                                            force_recompute=False,
                                            job_context=job_context
                                        )
                                        
                                        # Add ATS data to job
                                        missing_skills = []
                                        if job_ats_result.get("job_specific_score") is not None:
                                            job["ats_score"] = job_ats_result.get("job_specific_score")
                                            job["ats_grade"] = job_ats_result.get("ats_grade", "D")
                                            job["ats_relevance"] = job_ats_result.get("job_relevance_factor", 0)
                                            job["ats_keyword_overlap"] = job_ats_result.get("keyword_overlap", 0)
                                            job["ats_keyword_overlap_percentage"] = job_ats_result.get("keyword_overlap_percentage", 0)
                                            missing_skills = job_ats_result.get("missing_skills", [])[:5]  # Top 5
                                            job["ats_missing_skills"] = missing_skills
                                            job["ats_matched_keywords"] = job_ats_result.get("matched_job_keywords", [])[:10]  # Top 10
                                        else:
                                            # Fallback to generic ATS score
                                            job["ats_score"] = generic_ats_score
                                            job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                                            job["ats_relevance"] = None
                                            # Try to get missing skills from generic result
                                            missing_skills = generic_ats_result.get("missing_skills", [])[:5]
                                            if missing_skills:
                                                job["ats_missing_skills"] = missing_skills
                                        
                                        # DISABLED: Learning resources feature removed
                                        job["skill_gaps"] = []
                                    except Exception as e:
                                        logger.warning(f"Failed to calculate ATS score for job '{job.get('title', 'Unknown')}': {str(e)}")
                                        # Fallback to generic
                                        job["ats_score"] = generic_ats_score
                                        job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                                
                                logger.info(f"[JOB ATS SCORING] Added job-specific ATS scores to {len(return_jobs)} jobs")
                        except Exception as e:
                            logger.warning(f"Failed to add job-specific ATS scores: {str(e)}", exc_info=True)
                            # Continue without ATS scores - jobs still returned
                        
                        return {
                            "jobs": return_jobs,  # Return all, frontend can paginate if needed
                            "count": len(return_jobs),
                            "total_count": len(stored_jobs),  # Total stored count
                            "sources": list(set(job.get('source', 'Unknown') for job in stored_jobs)),
                            "from_cache": True,
                            "from_stored": True,
                            "domain_filtered": True,
                            "message": f"Using {len(return_jobs)} job matches from Quick Upload"
                        }
                    else:
                        # NO STORED MATCHES FOUND - Generate jobs on-demand
                        # This handles CVs created via CV Builder or ATS Optimizer that don't have stored jobs
                        logger.warning(f"[MATCH REUSE] No stored job matches found for user {user_id} - generating jobs on-demand")
                        try:
                            # Extract CV data for job matching
                            cv_data = cv.json_content
                            
                            # Handle nested CV structures (optimized_cv, original_cv, etc.)
                            if isinstance(cv_data, dict):
                                # Try to get original CV data if nested
                                if cv_data.get("original_cv"):
                                    cv_data = cv_data.get("original_cv")
                                elif cv_data.get("original_cv_data"):
                                    cv_data = cv_data.get("original_cv_data")
                                elif cv_data.get("optimized_cv"):
                                    # Use optimized CV if original not available
                                    cv_data = cv_data.get("optimized_cv")
                            
                            # Normalize CV data structure
                            from app.services.pdf_parser_service import PDFParserService
                            pdf_parser = PDFParserService()
                            normalized_cv = pdf_parser.validate_cv_data(cv_data.copy() if isinstance(cv_data, dict) else {})
                            
                            # Extract keywords and search jobs (same logic as Quick Upload)
                            from cv.job_keyword_extractor import JobKeywordExtractor
                            from cv.job_aggregator import JobAggregator
                            from cv.timeout_utils import safe_execute_with_timeout
                            
                            keyword_extractor = JobKeywordExtractor()
                            tiers = keyword_extractor.extract_keywords(normalized_cv)
                            primary_keywords = tiers.get("primary_search", [])
                            platform_keywords = {
                                "remoteok": keyword_extractor.get_platform_keywords(normalized_cv, "remoteok"),
                                "arbeitnow": keyword_extractor.get_platform_keywords(normalized_cv, "arbeitnow"),
                                "freelancer": keyword_extractor.get_platform_keywords(normalized_cv, "freelancer"),
                                "adzuna": keyword_extractor.get_platform_keywords(normalized_cv, "adzuna"),
                            }
                            
                            aggregator = JobAggregator()
                            
                            # Search jobs with timeout
                            job_matches = safe_execute_with_timeout(
                                aggregator.search_jobs,
                                timeout_seconds=15,
                                fallback=[],
                                keywords=primary_keywords,
                                limit=100,
                                platform_keywords=platform_keywords,
                                cv_data=normalized_cv
                            )
                            
                            # Remove duplicates
                            seen = set()
                            unique_jobs = []
                            for job in job_matches:
                                title = job.get("title", "").strip().lower()
                                company = job.get("company", job.get("company_name", "")).strip().lower()
                                source = job.get("source", "Unknown")
                                key = (title, company, source)
                                if key not in seen and title and company:
                                    seen.add(key)
                                    unique_jobs.append(job)
                            
                            # Interleave jobs from different sources
                            from collections import defaultdict
                            jobs_by_source = defaultdict(list)
                            for job in unique_jobs:
                                source = job.get("source", "Unknown")
                                jobs_by_source[source].append(job)
                            
                            interleaved = []
                            max_per_source = max(len(jobs) for jobs in jobs_by_source.values()) if jobs_by_source else 0
                            interleave_limit = min(100, len(unique_jobs))
                            
                            for i in range(max_per_source):
                                if len(interleaved) >= interleave_limit:
                                    break
                                for source_name, source_jobs in jobs_by_source.items():
                                    if len(interleaved) >= interleave_limit:
                                        break
                                    if i < len(source_jobs):
                                        job = source_jobs[i]
                                        job_key = (job.get("title", "").strip().lower(), 
                                                 job.get("company", job.get("company_name", "")).strip().lower(), 
                                                 job.get("source", "Unknown"))
                                        if job_key[0] and job_key[1]:
                                            interleaved.append(job)
                            
                            # Store jobs in CV for future use
                            cv.json_content["stored_job_matches"] = interleaved
                            
                            # Extract and store CV domain
                            try:
                                from cv.domain_extractor import DomainExtractor
                                domain_extractor = DomainExtractor()
                                cv_domains = safe_execute_with_timeout(
                                    domain_extractor.extract_domains,
                                    timeout_seconds=15,
                                    fallback=set(),
                                    cv_data=normalized_cv
                                )
                                parsed_skills = domain_extractor._extract_skills(normalized_cv)
                                cv.json_content["cv_domain"] = list(cv_domains) if cv_domains else []
                                cv.json_content["parsed_skills"] = parsed_skills
                            except Exception as e:
                                logger.error(f"[ON-DEMAND JOBS] Failed to extract domain: {str(e)}")
                                cv.json_content["cv_domain"] = []
                                cv.json_content["parsed_skills"] = []
                            
                            # Store job search context
                            cv.json_content["job_search"] = {
                                "keywords_tiers": tiers,
                                "primary_keywords": primary_keywords,
                                "platform_keywords": platform_keywords,
                                "last_results_count": len(interleaved),
                                "cv_domain": cv.json_content.get("cv_domain", []),
                                "parsed_skills": cv.json_content.get("parsed_skills", []),
                            }
                            cv.json_content["job_match_keywords"] = primary_keywords
                            
                            # Flag as modified and commit
                            from sqlalchemy.orm.attributes import flag_modified
                            flag_modified(cv, "json_content")
                            db.commit()
                            db.refresh(cv)
                            
                            # Add ATS scores and learning resources to on-demand jobs
                            try:
                                from cv.ats_engine import ATSEngine
                                ats_engine = ATSEngine()
                                generic_ats_result = ats_engine.calculate_ats_score(normalized_cv, force_recompute=False)
                                
                                for job in interleaved:
                                    try:
                                        job_context = {
                                            "job_title": job.get("title", ""),
                                            "job_description": job.get("description", ""),
                                            "job_skills": job.get("skills", []) if isinstance(job.get("skills"), list) else []
                                        }
                                        
                                        job_ats_result = ats_engine.calculate_ats_score(
                                            normalized_cv,
                                            stored_hash=generic_ats_result.get("cv_hash"),
                                            force_recompute=False,
                                            job_context=job_context
                                        )
                                        
                                        missing_skills = []
                                        if job_ats_result.get("job_specific_score") is not None:
                                            job["ats_score"] = job_ats_result.get("job_specific_score")
                                            job["ats_grade"] = job_ats_result.get("ats_grade", "D")
                                            missing_skills = job_ats_result.get("missing_skills", [])[:5]
                                            job["ats_missing_skills"] = missing_skills
                                        else:
                                            job["ats_score"] = generic_ats_result.get("ats_score", 0)
                                            job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                                            missing_skills = generic_ats_result.get("missing_skills", [])[:5]
                                            if missing_skills:
                                                job["ats_missing_skills"] = missing_skills
                                        
                                        # DISABLED: Learning resources feature removed
                                        job["skill_gaps"] = []
                                    except Exception as job_error:
                                        logger.warning(f"Failed to add ATS/resources to job '{job.get('title', 'Unknown')}': {str(job_error)}")
                                        job["skill_gaps"] = []
                            except Exception as e:
                                logger.warning(f"Failed to add ATS scores/resources to on-demand jobs: {str(e)}")
                            
                            logger.info(f"[ON-DEMAND JOBS] Generated {len(interleaved)} jobs for CV {cv.id} on-demand")
                            
                            # Return generated jobs
                            return {
                                "jobs": interleaved,
                                "count": len(interleaved),
                                "total_count": len(interleaved),
                                "sources": list(set(job.get('source', 'Unknown') for job in interleaved)),
                                "from_cache": False,
                                "from_stored": False,
                                "domain_filtered": True,
                                "message": f"Generated {len(interleaved)} job matches on-demand"
                            }
                        except Exception as e:
                            logger.error(f"[ON-DEMAND JOBS] Error generating jobs on-demand: {str(e)}", exc_info=True)
                            # Return empty on error
                            return {
                                "jobs": [],
                                "count": 0,
                                "total_count": 0,
                                "sources": [],
                                "from_cache": False,
                                "from_stored": False,
                                "domain_filtered": False,
                                "message": f"Failed to generate job matches: {str(e)}"
                            }
            except Exception as e:
                logger.error(f"[MATCH REUSE] Error retrieving stored jobs: {str(e)}", exc_info=True)
                # On error, return empty - do NOT fallback to recomputation
                return {
                    "jobs": [],
                    "count": 0,
                    "total_count": 0,
                    "sources": [],
                    "from_cache": False,
                    "from_stored": False,
                    "domain_filtered": False,
                    "message": "Error retrieving stored job matches. Please try uploading your CV again."
                }
        else:
            logger.warning("[MATCH REUSE] No user_id provided - cannot retrieve stored matches")
            # No user_id = no CV context = return empty (deterministic behavior)
            return {
                "jobs": [],
                "count": 0,
                "total_count": 0,
                "sources": [],
                "from_cache": False,
                "from_stored": False,
                "domain_filtered": False,
                "message": "User ID is required to retrieve stored job matches. Please upload your CV via Quick Upload first."
            }
        
        # CRITICAL: Do NOT re-compute job matches in CV Editor
        # All job matches MUST come from Quick Upload (stored_job_matches)
        # This ensures deterministic, consistent results across Quick Upload → CV Editor
        logger.error("[MATCH REUSE] CRITICAL: Reached fallback recomputation - this should NEVER happen if Quick Upload stored matches correctly")
        logger.error("[MATCH REUSE] This indicates a bug in match storage or retrieval - returning empty to maintain determinism")
        return {
            "jobs": [],
            "count": 0,
            "total_count": 0,
            "sources": [],
            "from_cache": False,
            "from_stored": False,
            "domain_filtered": False,
            "message": "Job matching is only available after CV upload. Please use Quick Upload first."
        }
        
        all_jobs = []
        sources = []
        
        # Use JobAggregator with unified keyword extractor
        try:
            logger.info("Searching external job platforms (RemoteOK, Arbeitnow, Freelancer.com, Adzuna) with unified extractor...")
            aggregator = JobAggregator()
            keyword_extractor = JobKeywordExtractor()
            
            # If user_id is provided, try to use CV-based keywords
            primary_keywords = []
            platform_keywords = None
            job_search_ctx = {}  # Initialize here to avoid NameError
            
            if request.user_id:
                from app.db.models import CV
                cv = db.query(CV).filter(CV.user_id == request.user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content:
                    cv_data = cv.json_content
                    # If optimized_cv exists, use it for extraction
                    if isinstance(cv_data, dict) and cv_data.get("optimized_cv") and isinstance(cv_data.get("optimized_cv"), dict):
                        cv_data_for_search = cv_data.get("optimized_cv")
                    else:
                        cv_data_for_search = cv_data
                    # Prefer stored job_search context if present
                    job_search_ctx = cv_data.get("job_search", {})
                    if job_search_ctx and job_search_ctx.get("primary_keywords"):
                        primary_keywords = job_search_ctx.get("primary_keywords", [])
                        platform_keywords = job_search_ctx.get("platform_keywords")
                        logger.info(f"Using stored job_search context: {len(primary_keywords)} primary keywords")
                    else:
                        tiers = keyword_extractor.extract_keywords(cv_data_for_search)
                        primary_keywords = tiers.get("primary_search", [])
                        platform_keywords = {
                            "remoteok": keyword_extractor.get_platform_keywords(cv_data_for_search, "remoteok"),
                            "arbeitnow": keyword_extractor.get_platform_keywords(cv_data_for_search, "arbeitnow"),
                            "freelancer": keyword_extractor.get_platform_keywords(cv_data_for_search, "freelancer"),
                            "adzuna": keyword_extractor.get_platform_keywords(cv_data_for_search, "adzuna"),
                        }
            
            # Do NOT override stored keywords with request titles; keep consistency
            # Only extend with filtered role/skill keywords if job_search context was absent
            if not job_search_ctx and request.keywords:
                merged = set([str(k).strip().lower() for k in primary_keywords])
                # Very light filter: keep words that look like roles or skills
                for k in request.keywords:
                    if not isinstance(k, str):
                        continue
                    kl = k.strip().lower()
                    if len(kl) <= 2:
                        continue
                    # Skip executive-only noise
                    if any(s in kl for s in ["director", "head", "chief", "vp", "ceo", "cto"]):
                        continue
                    merged.add(kl)
                primary_keywords = list(merged)[:15]
            
            # HARD GATE: If no primary keywords AND no user_id, reject job search
            # Do NOT use tech default keywords - this causes domain mismatches
            if not primary_keywords and not request.user_id:
                logger.warning("No keywords and no user_id - REJECTING job search (hard gate)")
                return {
                    "jobs": [],
                    "count": 0,
                    "sources": [],
                    "message": "No CV context available. Please upload a CV first."
                }
            
            # Only use tech defaults if explicitly no CV and no user_id (shouldn't happen)
            if not primary_keywords:
                logger.warning("No keywords extracted - using minimal fallback (may return 0 jobs if domain mismatch)")
                primary_keywords = []  # Empty keywords will likely return 0 jobs after domain filtering
            
            logger.info(f"Searching with unified primary keywords: {primary_keywords[:5]}..., limit: {request.limit}")
            
            # HARD GATE: Get CV data for domain filtering - REQUIRED
            # If no CV context, reject all jobs
            cv_data_for_filtering = None
            if request.user_id:
                from app.db.models import CV
                from app.services.pdf_parser_service import PDFParserService
                
                cv = db.query(CV).filter(CV.user_id == request.user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content:
                    cv_data_for_filtering = cv.json_content
                    
                    # CRITICAL: Extract CV data from nested structure (optimized_cv, original_cv)
                    # Domain extractor expects education, experience, skills at top level
                    if isinstance(cv_data_for_filtering, dict):
                        # First, try to get original_cv_data (canonical content)
                        if cv_data_for_filtering.get("original_cv_data"):
                            cv_data_for_filtering = cv_data_for_filtering.get("original_cv_data")
                        # Or get from original_cv key
                        elif cv_data_for_filtering.get("original_cv") and isinstance(cv_data_for_filtering.get("original_cv"), dict):
                            cv_data_for_filtering = cv_data_for_filtering.get("original_cv")
                            # Merge with top-level to ensure all data is available
                            cv_data_for_filtering = {**cv_data_for_filtering, **cv.json_content}
                            cv_data_for_filtering.pop("original_cv", None)
                        # Or extract from optimized_cv if that's what we have
                        elif cv_data_for_filtering.get("optimized_cv") and isinstance(cv_data_for_filtering.get("optimized_cv"), dict):
                            # Use optimized_cv but also check original_cv if available
                            optimized = cv_data_for_filtering.get("optimized_cv")
                            original = cv_data_for_filtering.get("original_cv")
                            # Prefer original_cv for canonical content, fall back to optimized_cv
                            if original and isinstance(original, dict):
                                cv_data_for_filtering = {**original, **optimized}
                            else:
                                cv_data_for_filtering = optimized
                            # Clean up nested keys
                            cv_data_for_filtering.pop("optimized_cv", None)
                            cv_data_for_filtering.pop("original_cv", None)
                    
                    # CRITICAL: Normalize CV data structure BEFORE domain filtering
                    # validate_cv_data ensures education, experience, skills are at top level
                    pdf_parser = PDFParserService()
                    cv_data_for_filtering = pdf_parser.validate_cv_data(cv_data_for_filtering or {})
                    
                    logger.info(f"[CV DATA NORMALIZATION] Normalized CV data for domain filtering - has education: {bool(cv_data_for_filtering.get('education'))}, has experience: {bool(cv_data_for_filtering.get('experience') or cv_data_for_filtering.get('work_experience'))}, has skills: {bool(cv_data_for_filtering.get('skills') or cv_data_for_filtering.get('personal_skills'))}")
                else:
                    # No CV found - reject all jobs
                    logger.warning(f"No CV found for user {request.user_id} - REJECTING all jobs (hard gate)")
                    return {
                        "jobs": [],
                        "count": 0,
                        "sources": [],
                        "message": "No CV found. Please upload a CV first."
                    }
            else:
                # No user_id - reject all jobs
                logger.warning("No user_id provided - REJECTING all jobs (hard gate)")
                return {
                    "jobs": [],
                    "count": 0,
                    "sources": [],
                    "message": "CV context required. Please provide user_id."
                }
            
            # Apply timeout to job search (15 seconds)
            from cv.timeout_utils import safe_execute_with_timeout
            integration_jobs = safe_execute_with_timeout(
                aggregator.search_jobs,
                timeout_seconds=15,
                fallback=[],
                keywords=primary_keywords,
                job_titles=request.job_titles,
                location=request.location,
                limit=request.limit,
                platform_keywords=platform_keywords,
                cv_data=cv_data_for_filtering
            )
            
            if not integration_jobs:
                logger.warning(f"No jobs found for keywords: {primary_keywords}")
            else:
                all_jobs.extend(integration_jobs)
                
                # Track sources
                if integration_jobs:
                    unique_sources = set(job.get('source', 'Unknown') for job in integration_jobs)
                    sources.extend(unique_sources)
                    logger.info(f"Found {len(integration_jobs)} jobs from integrations: {sources}")
            
        except Exception as e:
            logger.error(f"Integration job search failed: {str(e)}", exc_info=True)
            # Don't raise - return empty results instead
            all_jobs = []
        
        # Return integration results and optionally persist latest search context
        final_jobs = all_jobs[:request.limit] if all_jobs else []
        logger.info(f"Returning {len(final_jobs)} jobs from integrations")
        
        # Add ATS scores and learning resources to final_jobs if CV data available
        normalized_cv_for_resources = None
        if request.user_id:
            try:
                from app.db.models import CV
                from app.services.pdf_parser_service import PDFParserService
                cv = db.query(CV).filter(CV.user_id == request.user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content:
                    pdf_parser = PDFParserService()
                    cv_data = cv.json_content.get("original_cv_data") or cv.json_content
                    normalized_cv_for_resources = pdf_parser.validate_cv_data(cv_data if isinstance(cv_data, dict) else {})
            except Exception as e:
                logger.warning(f"Failed to get CV for learning resources: {str(e)}")
        
        if normalized_cv_for_resources and final_jobs:
            try:
                from cv.ats_engine import ATSEngine
                ats_engine = ATSEngine()
                generic_ats_result = ats_engine.calculate_ats_score(normalized_cv_for_resources, force_recompute=False)
                
                for job in final_jobs:
                    try:
                        job_context = {
                            "job_title": job.get("title", ""),
                            "job_description": job.get("description", ""),
                            "job_skills": job.get("skills", []) if isinstance(job.get("skills"), list) else []
                        }
                        
                        job_ats_result = ats_engine.calculate_ats_score(
                            normalized_cv_for_resources,
                            stored_hash=generic_ats_result.get("cv_hash"),
                            force_recompute=False,
                            job_context=job_context
                        )
                        
                        missing_skills = []
                        if job_ats_result.get("job_specific_score") is not None:
                            job["ats_score"] = job_ats_result.get("job_specific_score")
                            job["ats_grade"] = job_ats_result.get("ats_grade", "D")
                            missing_skills = job_ats_result.get("missing_skills", [])[:5]
                            job["ats_missing_skills"] = missing_skills
                        else:
                            job["ats_score"] = generic_ats_result.get("ats_score", 0)
                            job["ats_grade"] = generic_ats_result.get("ats_grade", "D")
                            missing_skills = generic_ats_result.get("missing_skills", [])[:5]
                            if missing_skills:
                                job["ats_missing_skills"] = missing_skills
                        
                        # DISABLED: Learning resources feature removed
                        job["skill_gaps"] = []
                    except Exception as job_error:
                        logger.warning(f"Failed to add ATS/resources to job '{job.get('title', 'Unknown')}': {str(job_error)}")
                        job["skill_gaps"] = []
            except Exception as e:
                logger.warning(f"Failed to add ATS scores/resources to final jobs: {str(e)}")
        
        # Recalculate ATS score if CV changed (hash mismatch)
        ats_score_result = {}
        try:
            if request.user_id:
                from app.db.models import CV
                cv = db.query(CV).filter(CV.user_id == request.user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content:
                    # CRITICAL FIX: Use ORIGINAL CV data for hashing (not optimized_cv)
                    # Hash must be based on canonical CV content, not optimized version
                    # This ensures same CV → same hash → same score across all endpoints
                    cv_payload = None
                    if isinstance(cv.json_content, dict):
                        # Always use original_cv_data if available (canonical content)
                        if cv.json_content.get("original_cv_data"):
                            cv_payload = cv.json_content.get("original_cv_data")
                        else:
                            # Fall back to json_content but strip ATS metadata
                            cv_payload = {k: v for k, v in cv.json_content.items() 
                                        if k not in ["ats_score", "ats_grade", "ats_metadata", "ats_analysis",
                                                    "ats_issues", "ats_recommendations", "ats_optimized_content",
                                                    "ats_changes", "optimized_cv", "is_optimized"]}
                    
                    # CRITICAL FIX: Check if CV data is nested under 'original_cv' key
                    # This happens when CV comes from optimization results
                    if cv_payload and isinstance(cv_payload, dict) and cv_payload.get("original_cv") and isinstance(cv_payload.get("original_cv"), dict):
                        logger.info("search_jobs_from_cv: Found 'original_cv' key, using that instead")
                        original_cv = cv_payload.get("original_cv")
                        # Merge original_cv with top-level data (original_cv takes precedence)
                        cv_payload = {**cv_payload, **original_cv}
                        # Remove the nested original_cv key
                        cv_payload.pop("original_cv", None)
                    
                    # Normalize CV data before hashing (same as optimize-ats endpoint)
                    from app.services.pdf_parser_service import PDFParserService
                    pdf_parser = PDFParserService()
                    normalized_cv_payload = pdf_parser.validate_cv_data(cv_payload or {})

                    stored_hash = cv.json_content.get("cv_hash") if isinstance(cv.json_content, dict) else None
                    ats_engine = get_ats_engine()
                    # FIX 3: Only recalculate if CV changed (don't force recompute)
                    fresh_score = ats_engine.calculate_ats_score(normalized_cv_payload, stored_hash, force_recompute=False)
                    
                    if fresh_score.get("reused_from_cache"):
                        logger.info(f"ATS score cached (hash match)")
                        ats_score_result = {
                            "ats_score": cv.json_content.get("ats_score", 0),
                            "ats_grade": cv.json_content.get("ats_grade", "D"),
                            "cached": True
                        }
                    else:
                        # Ensure we have valid score data
                        ats_score = fresh_score.get("ats_score")
                        ats_grade = fresh_score.get("ats_grade", "D")
                        
                        if ats_score is not None:
                            logger.info(f"ATS score recalculated: {ats_score} (hash changed)")
                            # Update CV record with new score
                            cv.json_content["ats_score"] = ats_score
                            cv.json_content["ats_grade"] = ats_grade
                            cv.json_content["cv_hash"] = fresh_score.get("cv_hash")
                            cv.json_content["ats_issues"] = fresh_score.get("ats_issues", [])
                            cv.json_content["ats_recommendations"] = fresh_score.get("ats_recommendations", [])
                            # Store ATS context for debugging
                            if fresh_score.get("ats_context"):
                                if "ats_metadata" not in cv.json_content:
                                    cv.json_content["ats_metadata"] = {}
                                cv.json_content["ats_metadata"]["ats_context"] = fresh_score.get("ats_context")
                            db.commit()
                            
                            ats_score_result = {
                                "ats_score": ats_score,
                                "ats_grade": ats_grade,
                                "cached": False
                            }
                        else:
                            # Fallback to stored score if calculation returned None
                            logger.warning("ATS calculation returned None, using stored score")
                            ats_score_result = {
                                "ats_score": cv.json_content.get("ats_score", 0),
                                "ats_grade": cv.json_content.get("ats_grade", "D"),
                                "cached": True
                            }
        except Exception as e:
            logger.warning(f"Failed to recalculate ATS score: {e}", exc_info=True)
        
        # Persist latest search context if user_id is provided
        try:
            if request.user_id:
                from app.db.models import CV
                cv = db.query(CV).filter(CV.user_id == request.user_id).order_by(CV.created_at.desc()).first()
                if cv and cv.json_content is not None:
                    ctx = cv.json_content.get("job_search", {}) or {}
                    ctx["primary_keywords"] = primary_keywords
                    if platform_keywords:
                        ctx["platform_keywords"] = platform_keywords
                    ctx["last_results_count"] = len(final_jobs)
                    cv.json_content["job_search"] = ctx
                    db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist latest job search context: {e}")
        
        return {
            "jobs": final_jobs,
            "count": len(final_jobs),
            "sources": list(set(sources)) if sources else [],
            "ats_score": ats_score_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search jobs: {str(e)}"
        )


# ==================== INVESTMENT PLATFORM ENDPOINTS ====================

@router.get("/api/startups/list")
async def list_startups(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = None,
    min_credibility: float = 0.0,
    db: Session = Depends(get_db)
):
    """List verified startups available for investment."""
    try:
        startups = startup_verification.list_verified_startups(
            skip=skip,
            limit=limit,
            sector=sector,
            min_credibility=min_credibility,
            db=db
        )
        return {"startups": startups, "count": len(startups)}
    except Exception as e:
        logger.error(f"Error listing startups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list startups: {str(e)}"
        )


@router.get("/api/startups/verify/{startup_id}")
async def verify_startup_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Verify a startup on the blockchain."""
    try:
        verification = startup_verification.verify_startup(startup_id, db)
        return verification
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying startup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify startup: {str(e)}"
        )


@router.get("/api/startups/{startup_id}")
async def get_startup_details_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Get detailed startup information with verification proof."""
    try:
        details = startup_verification.get_startup_details(startup_id, db)
        return details
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting startup details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup details: {str(e)}"
        )


@router.get("/api/startups/{startup_id}/qr")
async def get_startup_qr_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Generate QR code for startup verification."""
    try:
        # Verify startup exists
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {startup_id} not found"
            )
        
        # Generate QR code
        qr_service = QRCodeService()
        qr_data = qr_service.generate_startup_qr(startup_id)
        
        return qr_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate QR code: {str(e)}"
        )


@router.get("/api/startups/{startup_id}/credibility-for-investor")
async def get_startup_credibility_for_investor(startup_id: str, db: Session = Depends(get_db)):
    """Get comprehensive credibility breakdown for investors.
    
    Shows what's verified, what's missing, risk assessment, and green/red flags.
    This is specifically designed for investor decision-making.
    """
    try:
        # Verify startup exists by startup_id (string field)
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {startup_id} not found"
            )
        
        # Get credibility service - pass the database id (int)
        credibility_service = CredibilityService()
        credibility_data = credibility_service.get_investor_credibility_view(db, startup.id)
        
        return credibility_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting investor credibility view: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credibility information: {str(e)}"
        )


@router.post("/api/startups/{startup_id}/recalculate-credibility")
async def recalculate_credibility_endpoint(startup_id: int, db: Session = Depends(get_db)):
    """Manually trigger credibility score recalculation for a startup."""
    try:
        startup = db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {startup_id} not found"
            )
        
        from app.services.credibility_service import CredibilityService
        credibility_service = CredibilityService()
        result = credibility_service.calculate_startup_credibility(db, startup_id)
        db.commit()
        db.refresh(startup)
        
        return {
            "success": True,
            "startup_id": startup_id,
            "credibility_score": startup.credibility_score,
            "factors": result.get("factors", {}),
            "grade": result.get("grade", "F")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating credibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate credibility: {str(e)}"
        )


@router.get("/api/startups/by-founder/{founder_id}")
async def get_startup_by_founder_endpoint(founder_id: int, db: Session = Depends(get_db)):
    """Get startup information by founder/user ID."""
    try:
        # Find startup by founder_id
        startup = db.query(Startup).filter(Startup.founder_id == founder_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No startup found for founder {founder_id}"
            )
        
        # Recalculate credibility score to ensure it's up-to-date with latest attestations
        try:
            from app.services.credibility_service import CredibilityService
            credibility_service = CredibilityService()
            credibility_service.calculate_startup_credibility(db, startup.id)
            db.refresh(startup)  # Refresh to get updated score
        except Exception as e:
            logger.warning(f"Failed to recalculate credibility for startup {startup.id}: {e}")
        
        # Calculate total investments
        total_investments_result = db.query(func.sum(Investment.amount)).filter(
            Investment.startup_id == startup.id
        ).scalar()
        total_investments = float(total_investments_result) if total_investments_result else 0.0
        
        # Get founder info
        founder = db.query(User).filter(User.id == founder_id).first()
        
        return {
            "id": startup.id,
            "startup_id": startup.startup_id,
            "name": startup.name,
            "sector": startup.sector,
            "country": startup.country,
            "description": startup.description,
            "funding_goal": startup.funding_goal,
            "pitch_deck_url": startup.pitch_deck_url,
            "credibility_score": startup.credibility_score,
            "employees_verified": startup.employees_verified,
            "transaction_signature": startup.transaction_signature,
            "website": startup.website,
            "contact_email": startup.contact_email,
            "phone": startup.phone,
            "address": startup.address,
            "year_founded": startup.year_founded,
            "team_size": startup.team_size,
            "mission": startup.mission,
            "vision": startup.vision,
            "products_services": startup.products_services,
            "total_investments": total_investments,
            "verified": startup.transaction_signature is not None,
            "on_chain": startup.transaction_signature is not None,
            "founder": {
                "id": founder.id if founder else None,
                "name": founder.full_name if founder else None,
                "email": founder.email if founder else None
            },
            "created_at": startup.created_at.isoformat() if startup.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting startup by founder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup: {str(e)}"
        )


class StartupRegisterRequest(BaseModel):
    name: str
    sector: str
    country: Optional[str] = None
    year_founded: Optional[int] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    description: Optional[str] = None
    products_services: Optional[str] = None
    funding_goal: Optional[float] = None
    pitch_deck_url: Optional[str] = None
    team_size: Optional[int] = 1
    founder_experience_years: Optional[int] = None
    wallet_address: str


class StartupUpdateRequest(BaseModel):
    """Update startup information for credibility improvement"""
    founder_experience_years: Optional[int] = None
    has_mvp: Optional[bool] = None
    user_base_count: Optional[int] = None
    monthly_revenue: Optional[float] = None
    employees_verified: Optional[int] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    business_registration_verified: Optional[bool] = None
    documents_url: Optional[str] = None
    founder_profile_verified: Optional[bool] = None


@router.post("/api/startups/register")
async def register_startup_endpoint(
    request: StartupRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new startup."""
    try:
        logger.info(f"Registering startup: {request.name}")
        
        # Find founder by wallet address
        founder = db.query(User).filter(User.wallet_address == request.wallet_address).first()
        if not founder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with wallet address {request.wallet_address} not found"
            )
        
        # Check if user already has a startup
        existing_startup = db.query(Startup).filter(Startup.founder_id == founder.id).first()
        if existing_startup:
            # Calculate total investments for existing startup
            total_investments_result = db.query(func.sum(Investment.amount)).filter(
                Investment.startup_id == existing_startup.id
            ).scalar()
            total_investments = float(total_investments_result) if total_investments_result else 0.0
            
            # Return existing startup data
            return {
                "id": existing_startup.id,
                "startup_id": existing_startup.startup_id,
                "name": existing_startup.name,
                "sector": existing_startup.sector,
                "transaction_signature": existing_startup.transaction_signature,
                "verified": existing_startup.transaction_signature is not None,
                "on_chain": existing_startup.transaction_signature is not None,
                "total_investments": total_investments,
                "funding_goal": existing_startup.funding_goal,
                "already_exists": True,
                "message": "You already have a registered startup"
            }
        
        # Generate startup_id immediately (without waiting for slow blockchain call)
        # Blockchain registration happens in background for better user experience
        import time
        blockchain_startup_id = f"STARTUP-{founder.id}-{int(time.time())}"
        transaction_signature = None

        # Truncate long text fields to fit DB column limits
        def _trim(value: Optional[str], max_len: int) -> Optional[str]:
            if value is None:
                return None
            if not isinstance(value, str):
                value = str(value)
            return value[:max_len]

        description = _trim(request.description, 2000)
        mission = _trim(request.mission, 1000)
        vision = _trim(request.vision, 1000)
        products_services = _trim(request.products_services, 2000)
        pitch_deck_url = _trim(request.pitch_deck_url, 500)
        website = _trim(request.website, 500)
        address = _trim(request.address, 500)
        contact_email = _trim(request.contact_email, 255)
        phone = _trim(request.phone, 50)
        
        # Try blockchain registration in background (non-blocking)
        # This prevents user from waiting for slow blockchain calls (60s+ timeout)
        def register_on_blockchain_background(startup_db_id, startup_name, sector, founder_address):
            """Register startup on blockchain in background thread"""
            try:
                from app.db.session import SessionLocal
                db_bg = SessionLocal()
                try:
                    startup_client = StartupClient()
                    blockchain_result = startup_client.register_startup(
                        startup_name=startup_name,
                        sector=sector,
                        founder_address=founder_address
                    )
                    # Update startup with blockchain data
                    startup = db_bg.query(Startup).filter(Startup.id == startup_db_id).first()
                    if startup:
                        startup.transaction_signature = blockchain_result.get("transaction_signature")
                        if blockchain_result.get("startup_id"):
                            startup.startup_id = blockchain_result.get("startup_id")
                        db_bg.commit()
                        logger.info(f"✅ Background blockchain registration complete: {startup.startup_id}")
                finally:
                    db_bg.close()
            except Exception as e:
                logger.warning(f"⚠️ Background blockchain registration failed: {str(e)}")
        
        # Schedule background task (don't wait for it)
        # Note: In production, use a proper task queue like Celery or RQ
        import threading
        
        # Create startup in database
        startup = Startup(
            founder_id=founder.id,
            startup_id=blockchain_startup_id,
            name=request.name,
            sector=request.sector,
            country=request.country,
            year_founded=request.year_founded,
            website=website,
            contact_email=contact_email,
            phone=phone,
            address=address,
            mission=mission,
            vision=vision,
            description=description,
            products_services=products_services,
            funding_goal=request.funding_goal,
            pitch_deck_url=pitch_deck_url,
            team_size=request.team_size,
            founder_experience_years=request.founder_experience_years,
            transaction_signature=transaction_signature,
            credibility_score=0.0,
            employees_verified=0
        )
        
        db.add(startup)
        db.commit()
        db.refresh(startup)
        
        # CRITICAL: Create founder credential (single source of truth)
        from app.services.trust_service import CredentialService
        from app.db.models import CredentialType, CredentialSource, Credential
        from datetime import datetime
        
        credential_service = CredentialService()
        
        # Check if founder credential already exists
        existing_founder_cred = (
            db.query(Credential)
            .filter(
                Credential.user_id == founder.id,
                Credential.type == CredentialType.STARTUP_ROLE,
                Credential.title == "Founder",
                Credential.organization == startup.name,
            )
            .first()
        )
        
        if not existing_founder_cred:
            try:
                start_date = None
                if startup.year_founded:
                    start_date = datetime(startup.year_founded, 1, 1)
                
                founder_credential = credential_service.create_credential(
                    db=db,
                    user_id=founder.id,
                    credential_type=CredentialType.STARTUP_ROLE,
                    title="Founder",
                    organization=startup.name,
                    start_date=start_date,
                    description=f"Founded {startup.name} in {startup.sector}",
                    source=CredentialSource.SYSTEM_GENERATED,
                )
                logger.info(f"Created founder credential {founder_credential.id} for startup {startup.name}")
            except Exception as e:
                logger.error(f"Error creating founder credential: {e}")
                # Don't fail startup registration if credential creation fails
        
        logger.info(f"Startup registered successfully: {startup.id}, startup_id: {startup.startup_id}")
        
        # Start background blockchain registration (non-blocking)
        try:
            bg_thread = threading.Thread(
                target=register_on_blockchain_background,
                args=(startup.id, request.name, request.sector, request.wallet_address),
                daemon=True
            )
            bg_thread.start()
            logger.info(f"Started background blockchain registration for startup {startup.id}")
        except Exception as e:
            logger.warning(f"Failed to start background blockchain registration: {str(e)}")
        
        return {
            "id": startup.id,
            "startup_id": startup.startup_id,
            "name": startup.name,
            "sector": startup.sector,
            "transaction_signature": startup.transaction_signature,
            "verified": transaction_signature is not None,
            "on_chain": transaction_signature is not None,
            "message": "Startup registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Avoid format-key errors when logging arbitrary exceptions
        logger.exception("Error registering startup: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register startup: {str(e)}"
        )


class USDCInvestmentRequest(BaseModel):
    investor_id: int
    startup_id: str
    amount_usdc: float


@router.post("/api/investments/usdc/send")
async def send_usdc_investment_endpoint(
    request: USDCInvestmentRequest,
    db: Session = Depends(get_db)
):
    """Send USDC investment to a startup."""
    try:
        result = usdc_transactions.send_usdc_investment(
            investor_id=request.investor_id,
            startup_id=request.startup_id,
            amount_usdc=request.amount_usdc,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending USDC investment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send investment: {str(e)}"
        )


class USDCInvestmentSignRequest(BaseModel):
    """Sign and broadcast a pre-built USDC transaction."""
    transactionBytes: str  # base58 encoded transaction bytes
    solanaAddress: str
    startupId: str
    investorId: int
    amount: float
    investmentType: str = "usdc"


@router.post("/api/investments/usdc/sign")
async def sign_usdc_investment_endpoint(
    request: USDCInvestmentSignRequest,
    db: Session = Depends(get_db)
):
    """
    Sign and broadcast a USDC investment transaction.
    
    The frontend pre-builds the transaction and sends the bytes.
    The backend signs it and broadcasts to Solana.
    """
    try:
        import base58
        from solders.transaction import VersionedTransaction
        from solders.keypair import Keypair
        from solana.rpc.async_api import AsyncClient
        from app.core.config import settings
        
        # Decode transaction bytes from base58
        try:
            tx_bytes = base58.b58decode(request.transactionBytes)
        except Exception as e:
            raise ValueError(f"Invalid transaction bytes: {str(e)}")
        
        # Deserialize transaction using solders VersionedTransaction
        # @solana/web3.js Transaction.serialize() creates a format compatible with solders
        try:
            tx = VersionedTransaction.from_bytes(tx_bytes)
        except Exception as e:
            # If VersionedTransaction fails, the transaction might be legacy format
            # Try to parse as legacy Transaction
            try:
                from solders.transaction import Transaction as LegacyTransaction
                # Legacy transactions might need different handling
                # For now, raise a clear error
                raise ValueError(
                    f"Failed to deserialize transaction as VersionedTransaction: {str(e)}. "
                    "Legacy Transaction format not yet supported. Please use VersionedTransaction."
                )
            except Exception as e2:
                raise ValueError(f"Failed to deserialize transaction: {str(e)}")
        
        # Sign with backend keypair (server-side signing for devnet testing)
        # In production, use a proper signer service (HSM, KMS, etc.)
        # Get the signer keypair from settings
        signer_secret = settings.SOLANA_SIGNER_SECRET_KEY
        if not signer_secret:
            raise ValueError(
                "SOLANA_SIGNER_SECRET_KEY not configured. "
                "Set it in backend/.env with a base58 encoded private key."
            )
        
        try:
            # Load keypair using from_base58_string (expects full 64-byte keypair)
            signer_keypair = Keypair.from_base58_string(signer_secret)
        except Exception as e:
            raise ValueError(f"Invalid signer keypair: {str(e)}")
        
        # Convert VersionedTransaction to legacy Transaction for signing
        # VersionedTransaction doesn't have a sign() method, need to convert to legacy
        try:
            legacy_tx = tx.into_legacy_transaction()
            logger.info(f"Converted VersionedTransaction to legacy Transaction for signing")
        except Exception as e:
            logger.error(f"Failed to convert to legacy transaction: {str(e)}")
            raise ValueError(f"Transaction conversion failed: {str(e)}")
        
        # IMPORTANT: The transaction was built by the frontend with the user's wallet as fee payer
        # We need to change the fee payer to the backend signer's public key
        # and rebuild the transaction with the same instructions
        try:
            from solders.message import Message
            
            # Get the message from the transaction
            old_message = legacy_tx.message
            
            # Create a new message with backend signer as fee payer
            new_message = Message.new_with_blockhash(
                old_message.instructions,
                signer_keypair.pubkey(),  # Backend signer is the fee payer
                old_message.recent_blockhash
            )
            
            # Create new transaction with updated message
            from solders.transaction import Transaction as LegacyTransaction
            legacy_tx = LegacyTransaction.new_unsigned(new_message)
            
            logger.info(f"Updated transaction fee payer to backend signer: {signer_keypair.pubkey()}")
        except Exception as e:
            logger.error(f"Failed to update fee payer: {str(e)}")
            raise ValueError(f"Failed to update transaction fee payer: {str(e)}")
        
        # Sign the legacy transaction with the signer keypair
        try:
            legacy_tx.sign([signer_keypair], legacy_tx.message.recent_blockhash)
            logger.info(f"Transaction signed successfully")
        except Exception as e:
            logger.error(f"Failed to sign transaction: {str(e)}")
            raise ValueError(f"Transaction signing failed: {str(e)}")
        
        # Broadcast to Solana devnet
        async with AsyncClient(settings.SOLANA_RPC_URL) as client:
            # Send the signed legacy transaction
            response = await client.send_transaction(legacy_tx)
            tx_signature = str(response.value)
        
        logger.info(f"✅ Transaction signed and broadcasted: {tx_signature}")
        
        return {
            "success": True,
            "signature": tx_signature,
            "error": None
        }
        
    except ValueError as e:
        logger.error(f"Validation error signing transaction: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error signing USDC investment transaction: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign transaction: {str(e)}"
        )


class USDCInvestmentPrepareRequest(BaseModel):
    """Prepare a user-signed USDC transfer transaction (devnet)."""
    investor_id: int
    startup_id: str
    amount_usdc: float


@router.post("/api/investments/usdc/prepare")
async def prepare_usdc_investment_endpoint(
    request: USDCInvestmentPrepareRequest,
    db: Session = Depends(get_db)
):
    """
    Prepare an unsigned USDC transfer plan that the *user signs* via Privy.

    Safety constraints:
    - Backend does NOT sign on behalf of user.
    - Backend returns only wallet addresses + mint + amount + blockhash (no private keys, no PII).
    """
    try:
        from app.core.config import settings
        from app.db.models import Startup, User
        from app.utils.helpers import validate_solana_address
        from solana.rpc.async_api import AsyncClient

        if not settings.DEVNET_USDC_MINT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DEVNET_USDC_MINT is not configured in backend/.env. Set DEVNET_USDC_MINT to your test USDC mint address."
            )

        investor = db.query(User).filter(User.id == request.investor_id).first()
        if not investor or not investor.wallet_address:
            raise HTTPException(status_code=400, detail="Investor must have a wallet address (login via Privy first).")

        startup = db.query(Startup).filter(Startup.startup_id == request.startup_id).first()
        if not startup:
            raise HTTPException(status_code=404, detail=f"Startup {request.startup_id} not found")

        founder = db.query(User).filter(User.id == startup.founder_id).first()
        if not founder or not founder.wallet_address:
            raise HTTPException(status_code=400, detail="Startup founder must have a wallet address.")

        investor_wallet = investor.wallet_address.strip()
        founder_wallet = founder.wallet_address.strip()

        if not validate_solana_address(investor_wallet):
            raise HTTPException(status_code=400, detail="Invalid investor Solana wallet address format")
        if not validate_solana_address(founder_wallet):
            raise HTTPException(status_code=400, detail="Invalid founder Solana wallet address format")

        if request.amount_usdc <= 0:
            raise HTTPException(status_code=400, detail="amount_usdc must be > 0")

        # USDC uses 6 decimals on Solana
        decimals = 6
        amount_base_units = int(round(request.amount_usdc * (10 ** decimals)))

        async with AsyncClient(settings.SOLANA_RPC_URL) as client:
            bh = await client.get_latest_blockhash()
            # Convert Hash object to string for JSON serialization
            blockhash = str(bh.value.blockhash)
            last_valid_block_height = int(bh.value.last_valid_block_height)

        return {
            "success": True,
            "cluster": "devnet",
            "rpc_url": settings.SOLANA_RPC_URL,
            "usdc_mint": settings.DEVNET_USDC_MINT,
            "decimals": decimals,
            "amount_usdc": request.amount_usdc,
            "amount_base_units": amount_base_units,
            "investor_wallet": investor_wallet,
            "recipient_wallet": founder_wallet,
            "startup_id": request.startup_id,
            "recent_blockhash": blockhash,
            "last_valid_block_height": last_valid_block_height,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing USDC investment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prepare investment: {str(e)}"
        )


class USDCInvestmentRecordRequest(BaseModel):
    """Record a user-signed USDC investment after it is confirmed on-chain."""
    investor_id: int
    startup_id: str
    amount_usdc: float
    tx_signature: str


@router.post("/api/investments/usdc/record")
async def record_usdc_investment_endpoint(
    request: USDCInvestmentRecordRequest,
    db: Session = Depends(get_db)
):
    """
    Record a completed USDC investment tx signature in the database.
    Backend verifies that the transaction exists and is not failed (devnet).
    """
    try:
        from app.core.config import settings
        from app.db.models import Investment, Startup, User
        from solana.rpc.async_api import AsyncClient

        tx_sig = (request.tx_signature or "").strip()
        if not tx_sig or tx_sig.startswith("mock_"):
            raise HTTPException(status_code=400, detail="Invalid tx_signature")

        investor = db.query(User).filter(User.id == request.investor_id).first()
        if not investor:
            raise HTTPException(status_code=404, detail=f"Investor {request.investor_id} not found")

        startup = db.query(Startup).filter(Startup.startup_id == request.startup_id).first()
        if not startup:
            raise HTTPException(status_code=404, detail=f"Startup {request.startup_id} not found")

        # If already recorded, return existing receipt
        existing = db.query(Investment).filter(Investment.tx_signature == tx_sig).first()
        if existing:
            return {
                "success": True,
                "transaction_signature": existing.tx_signature,
                "explorer_url": f"https://explorer.solana.com/tx/{existing.tx_signature}?cluster=devnet",
                "amount_usdc": existing.amount,
                "startup_id": request.startup_id,
                "investor_id": request.investor_id,
                "timestamp": existing.timestamp.isoformat() if existing.timestamp else None,
            }

        # Verify transaction status on devnet
        from solders.signature import Signature
        async with AsyncClient(settings.SOLANA_RPC_URL) as client:
            # Convert string signature to Signature object
            sig_obj = Signature.from_string(tx_sig)
            statuses = await client.get_signature_statuses([sig_obj])
            tx_status = statuses.value[0] if statuses and statuses.value else None
            if not tx_status:
                raise HTTPException(status_code=400, detail="Transaction not found on devnet yet. Try again in a few seconds.")
            if tx_status.err is not None:
                raise HTTPException(status_code=400, detail=f"Transaction failed: {tx_status.err}")

        # Store investment
        investment = Investment(
            startup_id=startup.id,
            investor_id=request.investor_id,
            amount=request.amount_usdc,
            tx_signature=tx_sig,
        )
        db.add(investment)
        db.commit()
        db.refresh(investment)

        # Recalculate credibility (keeps existing behavior)
        try:
            from app.services.credibility_service import CredibilityService
            CredibilityService().calculate_startup_credibility(db, startup.id)
        except Exception as e:
            logger.warning(f"Credibility recalculation failed after investment record: {e}")

        return {
            "success": True,
            "transaction_signature": investment.tx_signature,
            "explorer_url": f"https://explorer.solana.com/tx/{investment.tx_signature}?cluster=devnet",
            "amount_usdc": investment.amount,
            "startup_id": request.startup_id,
            "investor_id": request.investor_id,
            "timestamp": investment.timestamp.isoformat() if investment.timestamp else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording USDC investment: {str(e)}")
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record investment: {str(e)}"
        )


@router.get("/api/investments/portfolio/{investor_id}")
async def get_portfolio_endpoint(investor_id: int, db: Session = Depends(get_db)):
    """Get investor portfolio with all investments."""
    try:
        portfolio = investor_portfolio.get_portfolio(investor_id, db)
        return portfolio
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio: {str(e)}"
        )


@router.get("/api/investments/startup/{startup_id}")
async def get_startup_investments_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Get all investments for a specific startup."""
    try:
        investments = investor_portfolio.get_startup_investments(startup_id, db)
        return {"investments": investments, "count": len(investments)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting startup investments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup investments: {str(e)}"
        )


@router.get("/api/investments/{investment_id}/receipt")
async def download_investment_receipt_endpoint(
    investment_id: int,
    db: Session = Depends(get_db)
):
    """Download PDF receipt for an investment transaction."""
    try:
        # Get investment
        investment = db.query(Investment).filter(Investment.id == investment_id).first()
        if not investment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investment {investment_id} not found"
            )
        
        # Get investor
        investor = db.query(User).filter(User.id == investment.investor_id).first()
        if not investor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investor {investment.investor_id} not found"
            )
        
        # Get startup
        startup = db.query(Startup).filter(Startup.id == investment.startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {investment.startup_id} not found"
            )
        
        # Prepare data for receipt
        investment_data = {
            "id": investment.id,
            "amount": investment.amount,
            "tx_signature": investment.tx_signature,
            "timestamp": investment.timestamp.isoformat() if investment.timestamp else None,
            "explorer_url": f"https://explorer.solana.com/tx/{investment.tx_signature}?cluster=devnet" if investment.tx_signature and not investment.tx_signature.startswith("mock_") else None
        }
        
        investor_data = {
            "full_name": investor.full_name,
            "email": investor.email,
            "wallet_address": investor.wallet_address
        }
        
        startup_data = {
            "name": startup.name,
            "startup_id": startup.startup_id,
            "sector": startup.sector
        }
        
        # Generate receipt
        pdf_bytes = receipt_generator.generate_receipt(
            investment_data,
            investor_data,
            startup_data
        )
        
        # Generate filename
        filename = f"Investment-Receipt-{investment.id}-{startup.startup_id}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate receipt: {str(e)}"
        )


@router.patch("/api/startups/{startup_id}/update-credibility")
async def update_startup_credibility_fields(
    startup_id: str,
    update_data: StartupUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update startup credibility-related fields."""
    try:
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {startup_id} not found"
            )
        
        # Update fields if provided
        if update_data.founder_experience_years is not None:
            startup.founder_experience_years = update_data.founder_experience_years
        if update_data.has_mvp is not None:
            startup.has_mvp = update_data.has_mvp
        if update_data.user_base_count is not None:
            startup.user_base_count = update_data.user_base_count
        if update_data.monthly_revenue is not None:
            startup.monthly_revenue = update_data.monthly_revenue
        if update_data.employees_verified is not None:
            startup.employees_verified = update_data.employees_verified
        if update_data.website is not None:
            startup.website = update_data.website
        if update_data.contact_email is not None:
            startup.contact_email = update_data.contact_email
        if update_data.address is not None:
            startup.address = update_data.address
        if update_data.business_registration_verified is not None:
            startup.business_registration_verified = update_data.business_registration_verified
        if update_data.documents_url is not None:
            startup.documents_url = update_data.documents_url
        if update_data.founder_profile_verified is not None:
            startup.founder_profile_verified = update_data.founder_profile_verified
        
        # Recalculate credibility score
        credibility_service = CredibilityService()
        credibility_service.calculate_startup_credibility(db, startup.id)
        db.refresh(startup)
        
        db.commit()
        
        logger.info(f"Updated credibility fields for startup {startup_id}")
        return {
            "success": True,
            "startup_id": startup.startup_id,
            "credibility_score": startup.credibility_score,
            "message": "Credibility fields updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating startup credibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update startup credibility: {str(e)}"
        )


class AddEmployeeRequest(BaseModel):
    name: str
    email: str
    role: str
    wallet_address: Optional[str] = None
    certificate_id: Optional[str] = None


@router.post("/api/startups/{startup_id}/add-employee")
async def add_employee_to_startup(
    startup_id: str,
    employee_data: AddEmployeeRequest,
    db: Session = Depends(get_db)
):
    """Add a team member to a startup with optional blockchain verification."""
    try:
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup {startup_id} not found"
            )
        
        # Create employee record
        employee = Employee(
            startup_id=startup.id,
            name=employee_data.name,
            email=employee_data.email,
            role=employee_data.role,
            wallet_address=employee_data.wallet_address,
            certificate_id=employee_data.certificate_id,
            verified_on_chain=False
        )
        
        # If wallet address and certificate ID provided, attempt blockchain verification
        if employee_data.wallet_address and employee_data.certificate_id:
            try:
                startup_client = StartupClient()
                blockchain_result = startup_client.add_employee(
                    startup_id=startup_id,
                    certificate_id=employee_data.certificate_id,
                    employee_address=employee_data.wallet_address
                )
                employee.verified_on_chain = True
                employee.transaction_signature = blockchain_result.get("transaction_signature")
                logger.info(f"Employee {employee_data.name} verified on blockchain")
            except Exception as e:
                logger.warning(f"Blockchain verification failed for employee {employee_data.name}: {str(e)}")
                # Continue without blockchain verification - employee still added to database
        
        db.add(employee)
        
        # Update employees_verified count
        verified_count = db.query(Employee).filter(
            Employee.startup_id == startup.id,
            Employee.verified_on_chain == True
        ).count()
        startup.employees_verified = verified_count
        
        # Recalculate credibility score
        credibility_service = CredibilityService()
        credibility_service.calculate_startup_credibility(db, startup.id)
        db.refresh(startup)
        
        db.commit()
        
        logger.info(f"Employee {employee_data.name} added to startup {startup_id}")
        return {
            "success": True,
            "employee_id": employee.id,
            "verified_on_chain": employee.verified_on_chain,
            "transaction_signature": employee.transaction_signature,
            "employees_verified": startup.employees_verified,
            "credibility_score": startup.credibility_score,
            "message": "Employee added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add employee: {str(e)}"
        )


# ==================== ATTESTATION ENDPOINTS ====================

class BusinessVerificationRequest(BaseModel):
    wallet_address: str
    business_name: str
    registration_number: str
    issuer: str = "verify"  # "verify" or "civic"
    create_sas_attestation: bool = True
    additional_data: Optional[Dict[str, Any]] = None


class IdentityVerificationRequest(BaseModel):
    wallet_address: str
    full_name: str
    email: str
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    issuer: str = "civic"  # "civic" or "verify"
    create_sas_attestation: bool = True
    additional_data: Optional[Dict[str, Any]] = None


@router.post("/api/attestations/verify/business")
async def verify_business_ownership(
    request: BusinessVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify business ownership via Verify or Civic."""
    try:
        # Get user by wallet address
        user = db.query(User).filter(User.wallet_address == request.wallet_address).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with wallet address {request.wallet_address} not found"
            )
        
        # Prepare business data
        business_data = {
            "business_name": request.business_name,
            "registration_number": request.registration_number,
            **(request.additional_data or {})
        }
        
        # Verify business ownership
        result = await attestation_service.verify_business_ownership(
            wallet_address=request.wallet_address,
            business_data=business_data,
            issuer=request.issuer,
            create_sas_attestation=request.create_sas_attestation
        )
        
        # Store attestation in database
        if result.verified:
            # Extract transaction signature and cluster from data
            tx_signature = result.data.get("transaction_signature") if result.on_chain else None
            cluster = result.data.get("cluster", "devnet") if result.on_chain else None
            account_address = result.data.get("account_address") if result.on_chain else None
            
            attestation = Attestation(
                user_id=user.id,
                wallet_address=request.wallet_address,
                attestation_id=result.attestation_id,
                issuer=result.issuer,
                schema=result.schema,
                status=result.status.value,
                data=result.data,
                on_chain=result.on_chain,
                sas_attestation_id=result.data.get("sas_attestation_id") if result.on_chain else None,
                transaction_signature=tx_signature,  # Store transaction signature
                cluster=cluster,  # Store cluster (devnet/mainnet)
                account_address=account_address,  # Store account address
                verified_at=result.timestamp if result.verified else None,
                expires_at=result.expires_at
            )
            db.add(attestation)
            db.commit()
            db.refresh(attestation)
            
            # Recalculate startup credibility if user is a founder
            if result.verified and user.role in ["founder", "startup"]:
                try:
                    startup = db.query(Startup).filter(Startup.founder_id == user.id).first()
                    if startup:
                        from app.services.credibility_service import CredibilityService
                        credibility_service = CredibilityService()
                        credibility_service.calculate_startup_credibility(db, startup.id)
                        db.commit()
                        logger.info(f"Recalculated credibility for startup {startup.id} after business attestation")
                except Exception as e:
                    logger.warning(f"Failed to recalculate credibility after business attestation: {e}")
        
        # Build response with SAS transaction details if on-chain
        response_data = {
            "success": result.verified,
            "attestation": {
                "id": result.attestation_id,
                "issuer": result.issuer,
                "status": result.status.value,
                "verified": result.verified,
                "on_chain": result.on_chain,
                "badge_type": attestation_service.get_badge_type(result.issuer, result.schema),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            },
            "error": result.error
        }
        
        # Add SAS transaction details if on-chain
        if result.on_chain and result.data.get("transaction_signature"):
            response_data["sas"] = {
                "tx_signature": result.data.get("transaction_signature"),
                "cluster": result.data.get("cluster", "devnet"),
                "explorer_url": result.data.get("explorer_url"),
                "account_address": result.data.get("account_address")
            }
        
        return response_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying business ownership: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify business: {str(e)}"
        )


@router.post("/api/attestations/verify/identity")
async def verify_identity(
    request: IdentityVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify identity/KYC via Civic or Verify."""
    try:
        # Get user by wallet address
        user = db.query(User).filter(User.wallet_address == request.wallet_address).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with wallet address {request.wallet_address} not found"
            )
        
        # Prepare identity data
        identity_data = {
            "full_name": request.full_name,
            "email": request.email,
            "date_of_birth": request.date_of_birth,
            "nationality": request.nationality,
            **(request.additional_data or {})
        }
        
        # Verify identity
        result = await attestation_service.verify_identity(
            wallet_address=request.wallet_address,
            identity_data=identity_data,
            issuer=request.issuer,
            create_sas_attestation=request.create_sas_attestation
        )
        
        # Store attestation in database
        if result.verified:
            # Extract transaction signature and cluster from data
            tx_signature = result.data.get("transaction_signature") if result.on_chain else None
            cluster = result.data.get("cluster", "devnet") if result.on_chain else None
            account_address = result.data.get("account_address") if result.on_chain else None
            
            attestation = Attestation(
                user_id=user.id,
                wallet_address=request.wallet_address,
                attestation_id=result.attestation_id,
                issuer=result.issuer,
                schema=result.schema,
                status=result.status.value,
                data=result.data,
                on_chain=result.on_chain,
                sas_attestation_id=result.data.get("sas_attestation_id") if result.on_chain else None,
                transaction_signature=tx_signature,  # Store transaction signature
                cluster=cluster,  # Store cluster (devnet/mainnet)
                account_address=account_address,  # Store account address
                verified_at=result.timestamp if result.verified else None,
                expires_at=result.expires_at
            )
            db.add(attestation)
            db.commit()
            db.refresh(attestation)
            
            # Recalculate startup credibility if user is a founder
            if result.verified and user.role in ["founder", "startup"]:
                try:
                    startup = db.query(Startup).filter(Startup.founder_id == user.id).first()
                    if startup:
                        from app.services.credibility_service import CredibilityService
                        credibility_service = CredibilityService()
                        credibility_service.calculate_startup_credibility(db, startup.id)
                        db.commit()
                        logger.info(f"Recalculated credibility for startup {startup.id} after identity attestation")
                except Exception as e:
                    logger.warning(f"Failed to recalculate credibility after identity attestation: {e}")
        
        # Build response with SAS transaction details if on-chain
        response_data = {
            "success": result.verified,
            "attestation": {
                "id": result.attestation_id,
                "issuer": result.issuer,
                "status": result.status.value,
                "verified": result.verified,
                "on_chain": result.on_chain,
                "badge_type": attestation_service.get_badge_type(
                    result.issuer, 
                    result.schema, 
                    result.on_chain, 
                    result.data.get("cluster") if result.on_chain else None
                ),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            },
            "error": result.error
        }
        
        # Add SAS transaction details if on-chain
        if result.on_chain and result.data.get("transaction_signature"):
            response_data["sas"] = {
                "tx_signature": result.data.get("transaction_signature"),
                "cluster": result.data.get("cluster", "devnet"),
                "explorer_url": result.data.get("explorer_url"),
                "account_address": result.data.get("account_address")
            }
        
        return response_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying identity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify identity: {str(e)}"
        )


@router.get("/api/attestations/wallet/{wallet_address}")
async def get_attestations(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get all attestations for a wallet address."""
    try:
        # Get from database
        attestations = db.query(Attestation).filter(
            Attestation.wallet_address == wallet_address
        ).order_by(Attestation.created_at.desc()).all()
        
        # Also check on-chain (SAS)
        all_attestations = await attestation_service.get_all_attestations(wallet_address)
        
        # Combine and format
        result = []
        for att in attestations:
            att_data = {
                "id": att.attestation_id,
                "issuer": att.issuer,
                "schema": att.schema,
                "status": att.status,
                "verified": att.status == "verified",
                "on_chain": att.on_chain,
                "sas_attestation_id": att.sas_attestation_id,
                "badge_type": attestation_service.get_badge_type(
                    att.issuer, 
                    att.schema, 
                    att.on_chain, 
                    att.cluster
                ),
                "created_at": att.created_at.isoformat() if att.created_at else None,
                "expires_at": att.expires_at.isoformat() if att.expires_at else None,
                "data": att.data
            }
            
            # Add SAS transaction details if on-chain
            if att.on_chain and att.transaction_signature:
                cluster = att.cluster or "devnet"
                # Construct explorer URL if not in data
                explorer_url = None
                if att.data and att.data.get("explorer_url"):
                    explorer_url = att.data.get("explorer_url")
                elif att.transaction_signature:
                    # Build explorer URL from transaction signature
                    explorer_url = f"https://explorer.solana.com/tx/{att.transaction_signature}?cluster={cluster}"
                
                att_data["sas"] = {
                    "tx_signature": att.transaction_signature,
                    "cluster": cluster,
                    "explorer_url": explorer_url,
                    "account_address": att.account_address
                }
            
            result.append(att_data)
        
        return {
            "wallet_address": wallet_address,
            "attestations": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting attestations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attestations: {str(e)}"
        )


@router.get("/api/attestations/user/{user_id}")
async def get_user_attestations(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all attestations for a user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        if not user.wallet_address:
            return {
                "user_id": user_id,
                "wallet_address": None,
                "attestations": [],
                "count": 0
            }
        
        # Get attestations
        attestations = db.query(Attestation).filter(
            Attestation.user_id == user_id
        ).order_by(Attestation.created_at.desc()).all()
        
        result = []
        for att in attestations:
            att_data = {
                "id": att.attestation_id,
                "issuer": att.issuer,
                "schema": att.schema,
                "status": att.status,
                "verified": att.status == "verified",
                "on_chain": att.on_chain,
                "sas_attestation_id": att.sas_attestation_id,
                "badge_type": attestation_service.get_badge_type(
                    att.issuer, 
                    att.schema, 
                    att.on_chain, 
                    att.cluster
                ),
                "created_at": att.created_at.isoformat() if att.created_at else None,
                "expires_at": att.expires_at.isoformat() if att.expires_at else None
            }
            
            # Add SAS transaction details if on-chain
            if att.on_chain and att.transaction_signature:
                cluster = att.cluster or "devnet"
                # Construct explorer URL if not in data
                explorer_url = None
                if att.data and att.data.get("explorer_url"):
                    explorer_url = att.data.get("explorer_url")
                elif att.transaction_signature:
                    # Build explorer URL from transaction signature
                    explorer_url = f"https://explorer.solana.com/tx/{att.transaction_signature}?cluster={cluster}"
                
                att_data["sas"] = {
                    "tx_signature": att.transaction_signature,
                    "cluster": cluster,
                    "explorer_url": explorer_url,
                    "account_address": att.account_address
                }
            
            result.append(att_data)
        
        return {
            "user_id": user_id,
            "wallet_address": user.wallet_address,
            "attestations": result,
            "count": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user attestations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attestations: {str(e)}"
        )


@router.get("/api/attestations/status/{attestation_id}")
async def get_attestation_status(
    attestation_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a specific attestation."""
    try:
        attestation = db.query(Attestation).filter(
            Attestation.attestation_id == attestation_id
        ).first()
        
        if not attestation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attestation {attestation_id} not found"
            )
        
        # Check on-chain status if applicable
        on_chain_verified = False
        if attestation.on_chain and attestation.schema:
            on_chain_verified = await attestation_service.verify_attestation_on_chain(
                attestation.wallet_address,
                attestation.schema
            )
        
        return {
            "id": attestation.attestation_id,
            "issuer": attestation.issuer,
            "schema": attestation.schema,
            "status": attestation.status,
            "verified": attestation.status == "verified",
            "on_chain": attestation.on_chain,
            "on_chain_verified": on_chain_verified,
            "badge_type": attestation_service.get_badge_type(
                attestation.issuer, 
                attestation.schema, 
                attestation.on_chain, 
                attestation.cluster
            ),
            "created_at": attestation.created_at.isoformat() if attestation.created_at else None,
            "expires_at": attestation.expires_at.isoformat() if attestation.expires_at else None,
            "data": attestation.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attestation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attestation status: {str(e)}"
        )

