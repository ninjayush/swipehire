import asyncio
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

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def get_person_2_resume_parser():
    """Import Person 2's resume parser function if present; otherwise return None."""
    try:
        from app.ai.resume_parser import parse_resume_text
        return parse_resume_text
    except (ImportError, ModuleNotFoundError):
        return None

# -------------------------------------------------------------
# POST /api/candidates/enrich
# -------------------------------------------------------------
@router.post("/enrich", response_model=CandidateEnrichResponse)
async def enrich_candidate(req: CandidateEnrichRequest, db: Session = Depends(get_db)):
    """Enrich candidate from professional network profile URL."""
    try:
        record = await PersonService.enrich_candidate_from_url(db, req.profile_url)
        return CandidateEnrichResponse(person=record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error enriching candidate: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to enrich candidate: {str(e)}")

# -------------------------------------------------------------
# POST /api/candidates/register
# -------------------------------------------------------------
@router.post("/register", response_model=CandidateEnrichResponse)
def register_candidate(req: CandidateRegisterRequest, db: Session = Depends(get_db)):
    """Register candidate or link existing sourced profile to registered account."""
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering candidate: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# POST /api/candidates/{id}/resume
# -------------------------------------------------------------
@router.post("/{id}/resume")
async def upload_resume(id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload resume file with strict type checking, size enforcement,
    safe storage (no path traversal), and Person 2 parser integration boundary.
    """
    person = db.query(Person).filter(Person.id == id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Candidate {id} not found")

    # 1. Validate file extension
    orig_name = os.path.basename(file.filename or "")
    _, ext = os.path.splitext(orig_name.lower())
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and DOCX files are permitted."
        )

    # 2. Read content and enforce size limit
    content = await file.read()
    if len(content) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {MAX_RESUME_SIZE_BYTES / (1024 * 1024):.1f}MB"
        )

    # 3. Secure server-side filename (prevents directory traversal)
    safe_filename = f"{uuid.uuid4().hex[:12]}_{orig_name.replace(' ', '_')}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 4. Text extraction attempt
    text_content = ""
    try:
        text_content = content.decode("utf-8", errors="ignore")
    except Exception:
        text_content = f"Binary content extracted from {orig_name}"

    # 5. Call Person 2's parser or return integration-not-ready status
    resume_parser = get_person_2_resume_parser()
    parsed_json = None
    parser_status = "completed"

    if resume_parser:
        try:
            # Claude-backed and synchronous; run in a worker thread to avoid blocking the event loop.
            parsed_json = await asyncio.to_thread(resume_parser, text_content)
        except Exception as e:
            logger.warning(f"Person 2 resume parser error: {e}")
            parsed_json = None
            parser_status = f"parser_error: {str(e)}"
    else:
        # Integration not merged yet by Person 2
        parser_status = "person_2_ai_module_not_ready"

    # 6. Ensure CandidateProfile exists
    profile = db.query(CandidateProfile).filter(CandidateProfile.person_id == id).first()
    if not profile:
        user = db.query(User).filter(User.role == "candidate").first()
        profile = CandidateProfile(
            user_id=user.id if user else str(uuid.uuid4()),
            person_id=id,
            preferences={}
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    resume = Resume(
        candidate_profile_id=profile.id,
        filename=orig_name,
        file_path=file_path,
        extracted_text=text_content,
        parsed_json=parsed_json
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Note: local file_path is NEVER returned in response
    return {
        "status": "success",
        "resume_id": resume.id,
        "filename": orig_name,
        "file_size_bytes": len(content),
        "parser_status": parser_status,
        "parsed_data": parsed_json
    }

# -------------------------------------------------------------
# GET /api/candidates/{id}
# -------------------------------------------------------------
@router.get("/{id}", response_model=CandidateEnrichResponse)
def get_candidate(id: str, db: Session = Depends(get_db)):
    """Retrieve candidate profile by canonical ID."""
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

    if person.membership_status != "registered":
        raise HTTPException(status_code=403, detail="Only registered candidates can view interest requests.")

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
