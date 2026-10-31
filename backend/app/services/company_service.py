import uuid
from typing import Any
from sqlalchemy.orm import Session
from app.models.company import Company
from app.database.schemas import CompanyResolveResponse
from app.integrations.crustdata import crustdata_client, CrustdataError

class CompanyService:
    @staticmethod
    async def resolve_company(
        db: Session,
        company_name: str | None = None,
        domain: str | None = None
    ) -> CompanyResolveResponse:
        """
        Identifies and enriches a company using Crustdata, persisting it in the database.
        """
        clean_name = company_name.strip() if company_name else None
        clean_domain = domain.strip().lower() if domain else None

        # Check existing company in DB
        existing: Company | None = None
        if clean_domain:
            existing = db.query(Company).filter(Company.domain == clean_domain).first()
        if not existing and clean_name:
            existing = db.query(Company).filter(Company.name.ilike(clean_name)).first()

        if existing and existing.enriched_data:
            return CompanyResolveResponse(
                company_id=existing.id,
                name=existing.name,
                domain=existing.domain,
                enriched=existing.enriched_data,
                ambiguous_options=[]
            )

        # Call Crustdata /company/identify
        identify_res = await crustdata_client.identify_company(
            company_name=clean_name,
            domain=clean_domain
        )

        # Extract identify result
        crustdata_id = None
        matched_domain = clean_domain
        matched_name = clean_name or "Company"
        ambiguous: list[dict[str, Any]] = []

        # If top-level is list of matched_on objects (standard live Crustdata response)
        matches_pool = []
        if isinstance(identify_res, list) and identify_res:
            first_entry = identify_res[0]
            if isinstance(first_entry, dict) and "matches" in first_entry:
                matches_pool = first_entry.get("matches", [])
            else:
                matches_pool = identify_res
        elif isinstance(identify_res, dict):
            if "matches" in identify_res:
                matches_pool = identify_res.get("matches", [])
            else:
                matches_pool = [identify_res]

        if len(matches_pool) > 1:
            ambiguous = matches_pool

        if matches_pool:
            first_match = matches_pool[0]
            comp_data = first_match.get("company_data") or first_match
            basic_info = comp_data.get("basic_info") or comp_data
            
            crustdata_id = comp_data.get("crustdata_company_id") or basic_info.get("crustdata_company_id") or first_match.get("id")
            matched_name = basic_info.get("name") or comp_data.get("name") or matched_name
            matched_domain = basic_info.get("primary_domain") or comp_data.get("domain") or matched_domain

        # Enrich company if crustdata_id or domain is present
        enriched_data = {}
        try:
            if crustdata_id or matched_domain:
                enriched_data = await crustdata_client.enrich_company(
                    company_id=crustdata_id,
                    domain=matched_domain
                )
        except Exception:
            # Fallback to identify result if enrich endpoint is unavailable
            enriched_data = identify_res if isinstance(identify_res, dict) else {}

        # Save or update Company in DB
        if not existing:
            company_id = str(uuid.uuid4())
            new_company = Company(
                id=company_id,
                crustdata_company_id=int(crustdata_id) if (isinstance(crustdata_id, int) or (isinstance(crustdata_id, str) and crustdata_id.isdigit())) else None,
                domain=matched_domain,
                name=matched_name,
                enriched_data=enriched_data
            )
            db.add(new_company)
            db.commit()
            db.refresh(new_company)
            existing = new_company
        else:
            existing.enriched_data = enriched_data
            if not existing.crustdata_company_id and crustdata_id:
                existing.crustdata_company_id = int(crustdata_id) if str(crustdata_id).isdigit() else None
            db.commit()

        return CompanyResolveResponse(
            company_id=existing.id,
            name=existing.name,
            domain=existing.domain,
            enriched=existing.enriched_data,
            ambiguous_options=ambiguous
        )
