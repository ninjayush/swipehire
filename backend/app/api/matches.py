import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schemas import InterestRespondRequest
from app.models.match import Match, InterestRequest
from app.models.person import Person
from app.models.job import JobRole
from app.services.action_service import ActionService

router = APIRouter(tags=["Matches & Interests"])
logger = logging.getLogger("api.matches")

# -------------------------------------------------------------
# POST /api/interests/{id}/respond
# -------------------------------------------------------------
@router.post("/api/interests/{id}/respond")
def respond_interest(id: str, req: InterestRespondRequest, db: Session = Depends(get_db)):
    """Candidate accepts or rejects recruiter interest."""
    try:
        return ActionService.respond_to_interest(
            db=db,
            interest_id=id,
            response=req.response
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error responding to interest: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# GET /api/matches
# -------------------------------------------------------------
@router.get("/api/matches")
def list_matches(job_id: str | None = None, person_id: str | None = None, db: Session = Depends(get_db)):
    """List mutual matches, optionally filtered by job or person."""
    query = db.query(Match)
    if job_id:
        query = query.filter(Match.job_id == job_id)
    if person_id:
        query = query.filter(Match.person_id == person_id)

    matches = query.all()
    results = []
    for m in matches:
        person = db.query(Person).filter(Person.id == m.person_id).first()
        job = db.query(JobRole).filter(JobRole.id == m.job_id).first()
        results.append({
            "match_id": m.id,
            "job_id": m.job_id,
            "job_title": job.title if job else "Unknown Role",
            "person_id": m.person_id,
            "candidate_name": person.name if person else "Unknown Candidate",
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

    return {"matches": results}
