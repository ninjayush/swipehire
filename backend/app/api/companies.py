import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schemas import CompanyResolveRequest, CompanyResolveResponse
from app.services.company_service import CompanyService

router = APIRouter(prefix="/api/companies", tags=["Companies"])
logger = logging.getLogger("api.companies")

# -------------------------------------------------------------
# POST /api/companies/resolve
# -------------------------------------------------------------
@router.post("/resolve", response_model=CompanyResolveResponse)
async def resolve_company(req: CompanyResolveRequest, db: Session = Depends(get_db)):
    """Identify and enrich company identity using Crustdata."""
    if not req.company_name and not req.domain:
        raise HTTPException(status_code=400, detail="Either company_name or domain must be provided")

    try:
        response = await CompanyService.resolve_company(
            db=db,
            company_name=req.company_name,
            domain=req.domain
        )
        return response
    except Exception as e:
        logger.error(f"Error resolving company: {e}")
        raise HTTPException(status_code=400, detail=str(e))
