import os
import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schemas import (
    CandidateEnrichRequest,
    CandidateEnrichResponse,
    CandidateRegisterRequest,
    PersonRecord,
)
from app.models.person import Person
from app.models.user import User, CandidateProfile, Resume
from app.models.match import InterestRequest
from app.models.job import JobRole
from app.services.person_service import PersonService
from app.config import settings

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])
logger = logging.getLogger("api.candidates")

def get_person_2_resume_parser():
    try:
        from app.ai.resume_parser import parse_resume_text
        return parse_resume_text
    except (ImportError, ModuleNotFoundError):
        def fallback_parser(text: str) -> dict:
            return {"skills": ["Python", "FastAPI"], "summary": text[:200]}
        return fallback_parser

# -------------------------------------------------------------
# POST /api/candidates/enrich
# -------------------------------------------------------------
@router.post("/enrich", response_model=CandidateEnrichResponse)
async def enrich_candidate(req: CandidateEnrichRequest, db: Session = Depends(get_db)):
    """Enrich candidate from professional network profile URL."""
    try:
        record = await PersonService.enrich_candidate_from_url(db, req.profile_url)
        return CandidateEnrichResponse(person=record)
    except Exception as e:
        logger.error(f"Error enriching candidate: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# POST /api/candidates/register
# -------------------------------------------------------------
@router.post("/register", response_model=CandidateEnrichResponse)
def register_candidate(req: CandidateRegisterRequest, db: Session = Depends(get_db)):
    """Register or link candidate profile."""
    try:
        record = PersonService.register_candidate(
            db=db,
            email=req.email,
            name=req.name,
            profile_url=req.profile_url,
            person_id=req.person_id,
            preferences=req.candidate_preferences
        )
        return CandidateEnrichResponse(person=record)
    except Exception as e:
        logger.error(f"Error registering candidate: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# POST /api/candidates/{id}/resume
# -------------------------------------------------------------
@router.post("/{id}/resume")
async def upload_resume(id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload resume file and trigger resume parser."""
    person = db.query(Person).filter(Person.id == id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Candidate not found")

    profile = db.query(CandidateProfile).filter(CandidateProfile.person_id == id).first()
    if not profile:
        # Create candidate profile if needed
        user = db.query(User).filter(User.role == "candidate").first()
        profile = CandidateProfile(
            user_id=user.id if user else str(uuid.uuid4()),
            person_id=id,
            preferences={}
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{id}_{file.filename}")
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Simple text extraction
    text_content = ""
    try:
        text_content = content.decode("utf-8", errors="ignore")
    except Exception:
        text_content = f"Binary resume uploaded: {file.filename}"

    # Call Person 2's resume parser
    resume_parser = get_person_2_resume_parser()
    parsed_json = resume_parser(text_content)

    resume = Resume(
        candidate_profile_id=profile.id,
        filename=file.filename or "resume.pdf",
        file_path=file_path,
        extracted_text=text_content,
        parsed_json=parsed_json
    )
    db.add(resume)
    db.commit()

    return {
        "status": "success",
        "resume_id": resume.id,
        "filename": resume.filename,
        "parsed_data": parsed_json
    }

# -------------------------------------------------------------
# GET /api/candidates/{id}
# -------------------------------------------------------------
@router.get("/{id}", response_model=CandidateEnrichResponse)
def get_candidate(id: str, db: Session = Depends(get_db)):
    """Retrieve candidate profile by ID."""
    person = db.query(Person).filter(Person.id == id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Candidate not found")

    data = dict(person.profile_data or {})
    data["person_id"] = person.id
    data["membership_status"] = person.membership_status
    data["name"] = person.name or data.get("name")
    data["profile_url"] = person.profile_url or data.get("profile_url")

    return CandidateEnrichResponse(person=PersonRecord(**data))

# -------------------------------------------------------------
# GET /api/candidates/{id}/interests
# -------------------------------------------------------------
@router.get("/{id}/interests")
def get_candidate_interests(id: str, db: Session = Depends(get_db)):
    """Retrieve incoming interest requests for a registered candidate."""
    person = db.query(Person).filter(Person.id == id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Candidate not found")

    requests = db.query(InterestRequest).filter(InterestRequest.person_id == id).all()
    results = []
    for r in requests:
        job = db.query(JobRole).filter(JobRole.id == r.job_id).first()
        results.append({
            "interest_id": r.id,
            "job_id": r.job_id,
            "job_title": job.title if job else "Unknown Role",
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return {"interests": results}
