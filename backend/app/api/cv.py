from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.db.models.cv import CV
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.ai_service import AIService
from app.utils.logger import logger
import json
import io
from fastapi.responses import StreamingResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER

router = APIRouter(prefix="/api/cv", tags=["cv"])
ai_service = AIService()

class CVSaveRequest(BaseModel):
    personal_info: Dict[str, Any]
    summary: str
    work_experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: Dict[str, Any]
    certifications: Optional[List[Dict[str, Any]]] = None
    template_name: Optional[str] = "Modern"

class AIEnhanceRequest(BaseModel):
    section: str
    content: str

@router.get("/me")
async def get_my_cv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv

@router.post("/save")
async def save_cv(request: CVSaveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.user_id == current_user.id).first()
    if not cv:
        cv = CV(user_id=current_user.id)
        db.add(cv)

    cv.personal_info = request.personal_info
    cv.summary = request.summary
    cv.work_experience = request.work_experience
    cv.education = request.education
    cv.skills = request.skills
    cv.certifications = request.certifications
    cv.template_name = request.template_name

    # Update json_content for backward compatibility
    cv.json_content = request.model_dump()

    db.commit()
    db.refresh(cv)
    return {"message": "CV saved successfully", "cv_id": cv.id}

@router.post("/ai-enhance")
async def ai_enhance(request: AIEnhanceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if request.section == "summary":
            # Generate summary from experience if content is empty or short
            cv = db.query(CV).filter(CV.user_id == current_user.id).first()
            exp_text = ""
            if cv and cv.work_experience:
                exp_text = " ".join([f"{e.get('job_title')} at {e.get('company')}: {e.get('description')}" for e in cv.work_experience])

            prompt = f"Generate a professional CV summary based on this work experience: {exp_text}. "
            if request.content:
                prompt += f"Also consider this existing draft: {request.content}"

            # Using ai_service.enhance_language as a proxy for generation for now
            enhanced_text = ai_service.enhance_language(prompt, "summary")
        else:
            enhanced_text = ai_service.enhance_language(request.content, request.section)

        return {"enhanced_content": enhanced_text}
    except Exception as e:
        logger.error(f"AI Enhancement failed: {str(e)}")
        raise HTTPException(status_code=500, detail="AI enhancement failed")

@router.post("/export-pdf")
async def export_pdf(request: Dict[str, Any], current_user: User = Depends(get_current_user)):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    personal = request.get('personal_info', {})
    story.append(Paragraph(f"<b>{personal.get('full_name', 'CV')}</b>", styles['Title']))
    story.append(Paragraph(f"{personal.get('email', '')} | {personal.get('phone', '')}", styles['Normal']))
    story.append(Paragraph(f"{personal.get('location', '')}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Professional Summary</b>", styles['Heading2']))
    story.append(Paragraph(request.get('summary', ''), styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Work Experience</b>", styles['Heading2']))
    for exp in request.get('work_experience', []):
        story.append(Paragraph(f"<b>{exp.get('job_title')}</b> at {exp.get('company')}", styles['Normal']))
        story.append(Paragraph(exp.get('description', ''), styles['Normal']))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Education</b>", styles['Heading2']))
    for edu in request.get('education', []):
        story.append(Paragraph(f"<b>{edu.get('degree')}</b>, {edu.get('institution')} ({edu.get('year')})", styles['Normal']))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Skills</b>", styles['Heading2']))
    skills = request.get('skills', {})
    for cat, items in skills.items():
        if items:
            story.append(Paragraph(f"<b>{cat.capitalize()}:</b> {', '.join(items)}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=cv.pdf"})

@router.post("/upload-parse")
async def upload_parse(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Read file content
    content = await file.read()

    # Simple text extraction for PDF/Text (in real scenario would use a PDF lib)
    try:
        text = content.decode('utf-8')
    except:
        text = "File content extracted (binary)"

    # Use AIService to parse and structure the CV
    parsed_data = ai_service.parse_and_structure_cv(text, current_user.id, db)

    # Tailor it with AI enhancements
    tailored_data = ai_service.tailor_parsed_cv(parsed_data, db)

    return tailored_data

class CVSearchRequest(BaseModel):
    job_title: Optional[str] = None
    skills: List[str] = []
    experience_level: Optional[str] = "Mid"
    location: Optional[str] = None
    education: Optional[str] = None
    qualifications: Optional[str] = None

@router.post("/search")
async def search_cvs(request: CVSearchRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Query all CVs
    query = db.query(CV)

    # Simple location filtering if provided
    if request.location:
        query = query.join(User).filter(or_(
            CV.personal_info.op('->>')('location').ilike(f"%{request.location}%"),
            User.university.ilike(f"%{request.location}%")
        ))

    cvs = query.all()
    results = []

    from app.services.matching_service import MatchingService
    matching_service = MatchingService()

    for cv in cvs:
        # Normalize skills
        user_skills_list = []
        if cv.skills:
            if isinstance(cv.skills, dict):
                for cat in cv.skills.values():
                    if isinstance(cat, list):
                        user_skills_list.extend([str(s).lower() for s in cat])
            elif isinstance(cv.skills, list):
                user_skills_list = [str(s).lower() for s in cv.skills]

        user_skills_set = set(user_skills_list)

        # Calculate skills match
        skills_match = matching_service._calculate_skills_match_fast(request.skills, user_skills_set) if request.skills else 1.0

        # Calculate experience match
        exp_years = len(cv.work_experience) if cv.work_experience else 0
        min_exp = 0
        if request.experience_level in ["Junior", "Entry"]: min_exp = 1
        elif request.experience_level == "Mid": min_exp = 3
        elif request.experience_level == "Senior": min_exp = 5

        experience_match = matching_service._calculate_experience_match(min_exp, exp_years)

        # Education & Qualification match
        edu_match = 1.0
        if request.education:
            edu_text = json.dumps(cv.education).lower() if cv.education else ""
            edu_match = 1.0 if request.education.lower() in edu_text else 0.3

        qual_match = 1.0
        if request.qualifications:
            qual_text = json.dumps(cv.certifications).lower() if cv.certifications else ""
            qual_match = 1.0 if request.qualifications.lower() in qual_text else 0.3

        # Title match
        title_match = 1.0
        if request.job_title:
            summary_text = (cv.summary or "").lower()
            work_text = json.dumps(cv.work_experience).lower() if cv.work_experience else ""
            title_match = 1.0 if (request.job_title.lower() in summary_text or request.job_title.lower() in work_text) else 0.5

        # Combined score (Weighted)
        match_score = int((skills_match * 0.4 + experience_match * 0.2 + edu_match * 0.15 + qual_match * 0.15 + title_match * 0.1) * 100)

        if (request.skills or request.education or request.qualifications or request.job_title) and match_score < 30:
            continue

        match_reason = f"Matches {int(skills_match*100)}% skills and {int(experience_match*100)}% experience."
        if edu_match > 0.8 and request.education: match_reason += " Matches education."

        results.append({
            "cv_id": cv.id,
            "user_id": cv.user_id,
            "name": cv.personal_info.get("full_name") if cv.personal_info else "Hidden Name",
            "skills": user_skills_list[:10],
            "experience_years": exp_years,
            "match_score": match_score,
            "match_reason": match_reason,
            "personal_info": cv.personal_info,
            "summary": cv.summary,
            "work_experience": cv.work_experience,
            "education": cv.education,
            "certifications": cv.certifications
        })

    # Rank by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
