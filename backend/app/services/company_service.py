import uuid
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from app.models.company import Company, CompanyMember
from app.models.user import User
from app.database.schemas import CompanyResolveResponse
from app.integrations.crustdata import crustdata_client, CrustdataError

class CompanyService:
    @staticmethod
    async def resolve_company(
        db: Session,
        company_name: str | None = None,
        domain: str | None = None,
        recruiter_user_id: str | None = None
    ) -> CompanyResolveResponse:
        """
        Identifies and enriches a company using Crustdata, persisting it with provenance,
        canonical IDs, and linking the demo recruiter through CompanyMember.
        """
        clean_name = company_name.strip() if company_name else None
        clean_domain = domain.strip().lower() if domain else None

        # Check existing company in DB first
        existing: Company | None = None
        if clean_domain:
            existing = db.query(Company).filter(Company.domain == clean_domain).first()
        if not existing and clean_name:
            existing = db.query(Company).filter(Company.name.ilike(clean_name)).first()

        if existing and existing.enriched_data:
            # Ensure recruiter is linked
            CompanyService._link_recruiter(db, existing.id, recruiter_user_id)
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

        crustdata_id = None
        matched_domain = clean_domain
        matched_name = clean_name or "Company"
        ambiguous_options: list[dict[str, Any]] = []

        # Parse match candidates and confidence from live Crustdata response
        matches_pool: list[dict[str, Any]] = []
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

        # Check for ambiguity (multiple plausible choices)
        if len(matches_pool) > 1:
            for m in matches_pool:
                comp = m.get("company_data") or m
                basic = comp.get("basic_info") or comp
                ambiguous_options.append({
                    "crustdata_company_id": comp.get("crustdata_company_id") or basic.get("crustdata_company_id"),
                    "name": basic.get("name") or comp.get("name"),
                    "domain": basic.get("primary_domain") or comp.get("domain"),
                    "confidence_score": m.get("confidence_score")
                })

        if matches_pool:
            first_match = matches_pool[0]
            comp_data = first_match.get("company_data") or first_match
            basic_info = comp_data.get("basic_info") or comp_data

            crustdata_id = (
                comp_data.get("crustdata_company_id")
                or basic_info.get("crustdata_company_id")
                or first_match.get("id")
            )
            matched_name = basic_info.get("name") or comp_data.get("name") or matched_name
            matched_domain = basic_info.get("primary_domain") or comp_data.get("domain") or matched_domain

        # Enrich company with canonical ID or domain
        enriched_data: dict[str, Any] = {}
        try:
            if crustdata_id or matched_domain:
                enrich_res = await crustdata_client.enrich_company(
                    company_id=crustdata_id,
                    domain=matched_domain
                )
                if isinstance(enrich_res, dict):
                    enriched_data = enrich_res
                elif isinstance(enrich_res, list) and enrich_res:
                    first_enr = enrich_res[0]
                    if isinstance(first_enr, dict) and "matches" in first_enr and first_enr["matches"]:
                        enriched_data = first_enr["matches"][0].get("company_data") or first_enr["matches"][0]
                    else:
                        enriched_data = first_enr if isinstance(first_enr, dict) else {}
        except Exception:
            enriched_data = identify_res if isinstance(identify_res, dict) else {}

        # Add data provenance metadata
        enriched_data["_source"] = "crustdata"
        enriched_data["_retrieved_at"] = datetime.utcnow().isoformat()
        if clean_domain:
            enriched_data["_searched_domain"] = clean_domain

        # Upsert Company by canonical Crustdata identity/domain
        if not existing:
            company_id = str(uuid.uuid4())
            new_company = Company(
                id=company_id,
                crustdata_company_id=int(crustdata_id) if (crustdata_id and str(crustdata_id).isdigit()) else None,
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
            if not existing.crustdata_company_id and crustdata_id and str(crustdata_id).isdigit():
                existing.crustdata_company_id = int(crustdata_id)
            if not existing.domain and matched_domain:
                existing.domain = matched_domain
            db.commit()
            db.refresh(existing)

        # Link recruiter to resolved company through CompanyMember
        CompanyService._link_recruiter(db, existing.id, recruiter_user_id)

        return CompanyResolveResponse(
            company_id=existing.id,
            name=existing.name,
            domain=existing.domain,
            enriched=existing.enriched_data,
            ambiguous_options=ambiguous_options
        )

    @staticmethod
    def _link_recruiter(db: Session, company_id: str, recruiter_user_id: str | None = None) -> None:
        """Links the recruiter to the resolved company through CompanyMember."""
        recruiter = None
        if recruiter_user_id:
            recruiter = db.query(User).filter(User.id == recruiter_user_id).first()
        if not recruiter:
            recruiter = db.query(User).filter(User.role == "recruiter").first()

        if recruiter:
            existing_member = db.query(CompanyMember).filter(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == recruiter.id
            ).first()
            if not existing_member:
                membership = CompanyMember(
                    company_id=company_id,
                    user_id=recruiter.id,
                    role="recruiter"
                )
                db.add(membership)
                db.commit()
