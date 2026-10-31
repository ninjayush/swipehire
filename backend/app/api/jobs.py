import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schemas import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobRequirements,
    CandidateDeckResponse,
    RecruiterActionRequest,
    PersonRecord,
)
from app.models.job import JobRole
from app.models.company import Company
from app.models.person import Person
from app.models.match import MatchRun, CandidateMatch, RecruiterAction
from app.services.discovery_service import DiscoveryService
from app.services.action_service import ActionService

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
logger = logging.getLogger("api.jobs")

def get_person_2_jd_parser():
    try:
        from app.ai.jd_parser import parse_job_description
        return parse_job_description
    except (ImportError, ModuleNotFoundError):
        def fallback_parser(raw_jd: str) -> JobRequirements:
            lines = [line.strip() for line in raw_jd.split("\n") if line.strip()]
            title = lines[0] if lines else "Software Engineer"
            return JobRequirements(
                title=title,
                raw_jd=raw_jd,
                must_have_skills=["Python"]
            )
        return fallback_parser

# -------------------------------------------------------------
# POST /api/jobs
# -------------------------------------------------------------
@router.post("", response_model=JobResponse)
def create_job(req: JobCreateRequest, db: Session = Depends(get_db)):
    """Create a new job role from structured data or raw JD."""
    company = db.query(Company).filter(Company.id == req.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {req.company_id} not found")

    if req.input_type == "jd":
        if not req.raw_jd:
            raise HTTPException(status_code=400, detail="raw_jd must be provided for input_type 'jd'")
        parser = get_person_2_jd_parser()
        requirements = parser(req.raw_jd)
        status = "needs_confirmation"
    else:
        if not req.requirements:
            raise HTTPException(status_code=400, detail="requirements must be provided for input_type 'structured'")
        if isinstance(req.requirements, JobRequirements):
            requirements = req.requirements
        else:
            requirements = JobRequirements(**req.requirements)
        status = "active"

    job_id = str(uuid.uuid4())
    job = JobRole(
        id=job_id,
        company_id=req.company_id,
        title=requirements.title,
        status=status,
        raw_jd=req.raw_jd,
        requirements=requirements.model_dump()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobResponse(
        job_id=job.id,
        company_id=job.company_id,
        requirements=requirements,
        status=job.status
    )

# -------------------------------------------------------------
# GET /api/jobs
# -------------------------------------------------------------
@router.get("")
def list_jobs(company_id: str | None = None, db: Session = Depends(get_db)):
    """List all jobs, optionally filtered by company."""
    query = db.query(JobRole)
    if company_id:
        query = query.filter(JobRole.company_id == company_id)
    jobs = query.all()

    return {
        "jobs": [
            {
                "job_id": j.id,
                "company_id": j.company_id,
                "title": j.title,
                "status": j.status,
                "requirements": j.requirements,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
    }

# -------------------------------------------------------------
# PATCH /api/jobs/{id}
# -------------------------------------------------------------
@router.patch("/{id}", response_model=JobResponse)
def update_job(id: str, req: JobUpdateRequest, db: Session = Depends(get_db)):
    """Recruiter confirmation or edits for a job description."""
    job = db.query(JobRole).filter(JobRole.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {id} not found")

    if req.title:
        job.title = req.title

    if req.status:
        job.status = req.status

    if req.requirements is not None:
        if isinstance(req.requirements, JobRequirements):
            req_dict = req.requirements.model_dump()
        else:
            req_dict = dict(req.requirements)
        # Merge with existing
        merged = {**job.requirements, **req_dict}
        job.requirements = merged
        if not req.title and "title" in merged:
            job.title = merged["title"]

    db.commit()
    db.refresh(job)

    return JobResponse(
        job_id=job.id,
        company_id=job.company_id,
        requirements=JobRequirements(**job.requirements),
        status=job.status
    )

# -------------------------------------------------------------
# POST /api/jobs/{id}/discover
# -------------------------------------------------------------
@router.post("/{id}/discover", response_model=CandidateDeckResponse)
async def discover_candidates(id: str, db: Session = Depends(get_db)):
    """Trigger candidate discovery and scoring pipeline."""
    job = db.query(JobRole).filter(JobRole.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {id} not found")

    # If job was in needs_confirmation, confirm it on discovery trigger
    if job.status == "needs_confirmation":
        job.status = "active"
        db.commit()

    try:
        return await DiscoveryService.run_discovery_and_matching(db, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in discovery pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

# -------------------------------------------------------------
# GET /api/jobs/{id}/deck
# -------------------------------------------------------------
@router.get("/{id}/deck", response_model=CandidateDeckResponse)
def get_candidate_deck(id: str, db: Session = Depends(get_db)):
    """Retrieve ranked candidate cards for the most recent match run."""
    run = db.query(MatchRun).filter(MatchRun.job_id == id).order_by(MatchRun.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No candidate deck found. Run discovery first.")

    matches = db.query(CandidateMatch).filter(
        CandidateMatch.match_run_id == run.id,
        CandidateMatch.eligible == True
    ).order_by(CandidateMatch.rank.asc()).all()

    cards = []
    for m in matches:
        person = db.query(Person).filter(Person.id == m.person_id).first()
        if person:
            person_dict = dict(person.profile_data or {})
            person_dict["person_id"] = person.id
            person_dict["membership_status"] = person.membership_status
            cards.append({
                "person": person_dict,
                "evaluation": {
                    "person_id": m.person_id,
                    "eligible": m.eligible,
                    "fit_score": m.fit_score,
                    "component_scores": m.component_scores,
                    "evidence_coverage": m.evidence_coverage,
                    "fit_type": m.fit_type,
                    "rank": m.rank,
                    "match_explanation": m.match_explanation,
                    "reasons": m.reasons or []
                }
            })

    return CandidateDeckResponse(
        job_id=id,
        match_run_id=run.id,
        status=run.status,  # type: ignore
        total_candidates=run.total_candidates,
        direct_count=run.direct_count,
        adjacent_count=run.adjacent_count,
        excluded_count=run.excluded_count,
        cards=cards
    )

# -------------------------------------------------------------
# GET /api/jobs/{id}/shortlist
# -------------------------------------------------------------
@router.get("/{id}/shortlist")
def get_shortlist(id: str, db: Session = Depends(get_db)):
    """Retrieve shortlisted candidates for a job."""
    actions = db.query(RecruiterAction).filter(
        RecruiterAction.job_id == id,
        RecruiterAction.action == "shortlist"
    ).all()

    candidates = []
    for a in actions:
        person = db.query(Person).filter(Person.id == a.person_id).first()
        if person:
            candidates.append({
                "person_id": person.id,
                "name": person.name,
                "membership_status": person.membership_status,
                "origin": person.origin,
                "action_created_at": a.created_at.isoformat() if a.created_at else None
            })

    return {"job_id": id, "shortlist": candidates}

# -------------------------------------------------------------
# POST /api/jobs/{id}/actions
# -------------------------------------------------------------
@router.post("/{id}/actions")
def perform_action(id: str, req: RecruiterActionRequest, db: Session = Depends(get_db)):
    """Shortlist, pass, or save candidate card."""
    try:
        return ActionService.record_recruiter_action(
            db=db,
            job_id=id,
            person_id=req.person_id,
            action=req.action
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=400, detail=str(e))
