import re
import uuid
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse, urlunparse
from sqlalchemy.orm import Session
from app.models.person import Person
from app.models.user import User, CandidateProfile
from app.database.schemas import PersonRecord
from app.integrations.crustdata import crustdata_client, CrustdataError

logger = logging.getLogger("person_service")

VALID_PROFILE_DOMAINS = {"linkedin.com", "github.com", "twitter.com", "x.com"}

def normalize_profile_url(url: str | None) -> str | None:
    """
    Validate and normalize professional profile URLs.
    Rejects malformed or unsupported URLs.
    """
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL structure: {url}")

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Check that domain is recognized or has valid TLD
    domain_match = any(netloc == d or netloc.endswith("." + d) for d in VALID_PROFILE_DOMAINS)
    if not domain_match and "." not in netloc:
        raise ValueError(f"Unsupported profile URL domain: {netloc}")

    path = parsed.path.lower().rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))


def normalize_crustdata_person(data: dict[str, Any], origin: str = "crustdata_sourced") -> PersonRecord:
    """
    Transforms raw Crustdata person response into the canonical PersonRecord contract.
    Handles nested live Crustdata schemas (e.g. basic_profile, matches, person_data) gracefully.
    Preserves data provenance and explicit non-member registration status.
    """
    # If wrapped in matches list
    if "matches" in data and isinstance(data["matches"], list) and data["matches"]:
        match_item = data["matches"][0]
        data = match_item.get("person_data") or match_item

    # If wrapped in basic_profile
    profile = data.get("basic_profile") if isinstance(data.get("basic_profile"), dict) else data

    person_id = str(uuid.uuid4())
    
    # Crustdata person ID
    crustdata_id = (
        data.get("crustdata_person_id")
        or profile.get("crustdata_person_id")
        or data.get("id")
        or data.get("person_id")
    )
    if isinstance(crustdata_id, str) and crustdata_id.isdigit():
        crustdata_id = int(crustdata_id)
    elif not isinstance(crustdata_id, int):
        crustdata_id = None

    # Profile URL
    raw_url = (
        profile.get("professional_network_profile_url")
        or data.get("profile_url")
        or data.get("linkedin_profile_url")
        or data.get("linkedin_url")
    )
    profile_url = None
    if raw_url:
        try:
            profile_url = normalize_profile_url(raw_url)
        except ValueError:
            profile_url = str(raw_url).strip().rstrip("/")

    # Name
    name = profile.get("name") or data.get("name") or data.get("full_name")
    if not name:
        first = profile.get("first_name", "") or data.get("first_name", "")
        last = profile.get("last_name", "") or data.get("last_name", "")
        name = f"{first} {last}".strip() or None

    headline = profile.get("headline") or data.get("headline") or data.get("summary")
    current_title = profile.get("current_title") or data.get("current_title") or data.get("title")
    current_company = profile.get("current_company") or data.get("current_company") or data.get("company_name")
    
    # Location
    loc_obj = profile.get("location") or data.get("location")
    if isinstance(loc_obj, dict):
        location = loc_obj.get("full_location") or loc_obj.get("raw") or loc_obj.get("city")
    else:
        location = loc_obj or data.get("city")

    # Skills extraction
    raw_skills = profile.get("skills") or data.get("skills", [])
    skills: list[str] = []
    if isinstance(raw_skills, list):
        for s in raw_skills:
            if isinstance(s, str):
                skills.append(s)
            elif isinstance(s, dict) and "name" in s:
                skills.append(s["name"])

    # Experience years
    exp_years = profile.get("experience_years") or data.get("experience_years") or data.get("years_of_experience")
    if exp_years is not None:
        try:
            exp_years = max(0.0, float(exp_years))
        except (ValueError, TypeError):
            exp_years = None

    # Employment & Education
    employment = profile.get("employment_history") or data.get("employment_history") or data.get("work_experience") or []
    if not isinstance(employment, list):
        employment = []

    education = profile.get("education") or data.get("education") or []
    if not isinstance(education, list):
        education = []

    # Provenance metadata
    metadata = [
        {
            "source": "crustdata" if origin == "crustdata_sourced" else "user_registration",
            "source_id": crustdata_id,
            "source_url": profile_url,
            "retrieved_at": datetime.utcnow().isoformat(),
            "verified": False,
        }
    ]

    return PersonRecord(
        person_id=person_id,
        crustdata_person_id=crustdata_id,
        profile_url=profile_url,
        origin=origin,  # type: ignore
        membership_status="not_registered" if origin == "crustdata_sourced" else "registered",
        name=name,
        headline=headline,
        current_title=current_title,
        current_company=current_company,
        location=location,
        skills=skills,
        experience_years=exp_years,
        employment_history=employment,
        education=education,
        resume_highlights=[],
        candidate_preferences={},
        source_metadata=metadata,
    )


class PersonService:
    @staticmethod
    def get_or_create_person(db: Session, record: PersonRecord) -> Person:
        """
        Reusable canonical identity lookup and upsert:
        1. Lookup by non-null crustdata_person_id
        2. Lookup by normalized profile_url
        3. Detect and reconcile conflicting rows safely without creating duplicates
        4. Enforce one canonical Person per Crustdata identity / profile URL
        """
        by_id_person: Person | None = None
        by_url_person: Person | None = None

        if record.crustdata_person_id:
            by_id_person = db.query(Person).filter(
                Person.crustdata_person_id == record.crustdata_person_id
            ).first()

        norm_url = normalize_profile_url(record.profile_url) if record.profile_url else None
        if norm_url:
            by_url_person = db.query(Person).filter(
                Person.profile_url == norm_url
            ).first()

        # Conflict Reconciliation
        if by_id_person and by_url_person and (by_id_person.id != by_url_person.id):
            logger.warning(
                f"Identity conflict detected: Crustdata ID {record.crustdata_person_id} maps to "
                f"{by_id_person.id}, but URL {norm_url} maps to {by_url_person.id}. Reconciling..."
            )
            # Favor registered person or existing enriched person
            primary = by_id_person if by_id_person.membership_status == "registered" else by_url_person
            secondary = by_url_person if primary.id == by_id_person.id else by_id_person

            # Update primary with missing identity tokens
            if not primary.crustdata_person_id and secondary.crustdata_person_id:
                primary.crustdata_person_id = secondary.crustdata_person_id
            if not primary.profile_url and secondary.profile_url:
                primary.profile_url = secondary.profile_url
            
            existing = primary
        else:
            existing = by_id_person or by_url_person

        if existing:
            # Update attributes without overwriting canonical ID
            record.person_id = existing.id
            if not existing.crustdata_person_id and record.crustdata_person_id:
                existing.crustdata_person_id = record.crustdata_person_id
            if not existing.profile_url and norm_url:
                existing.profile_url = norm_url
            if record.name and not existing.name:
                existing.name = record.name
            if record.current_title and not existing.current_title:
                existing.current_title = record.current_title
            if record.current_company and not existing.current_company:
                existing.current_company = record.current_company
            if record.location and not existing.location:
                existing.location = record.location

            existing.profile_data = record.model_dump()
            db.commit()
            db.refresh(existing)
            return existing

        # Create new canonical Person record
        new_person = Person(
            id=record.person_id,
            crustdata_person_id=record.crustdata_person_id,
            profile_url=norm_url,
            origin=record.origin,
            membership_status=record.membership_status,
            name=record.name,
            headline=record.headline,
            current_title=record.current_title,
            current_company=record.current_company,
            location=record.location,
            profile_data=record.model_dump()
        )
        db.add(new_person)
        db.commit()
        db.refresh(new_person)
        return new_person

    @staticmethod
    async def enrich_candidate_from_url(db: Session, profile_url: str) -> PersonRecord:
        """
        Validates URL, calls Crustdata person/enrich, normalizes into canonical PersonRecord,
        upserts into database, and returns preview.
        """
        norm_url = normalize_profile_url(profile_url)
        if not norm_url:
            raise ValueError("Profile URL cannot be empty")

        # Check DB first for cached profile
        existing = db.query(Person).filter(Person.profile_url == norm_url).first()
        if existing and existing.profile_data:
            rec = PersonRecord(**existing.profile_data)
            rec.person_id = existing.id
            rec.membership_status = existing.membership_status  # type: ignore
            return rec

        # Call Crustdata Person Enrich
        result = await crustdata_client.person_enrich(norm_url)
        raw_data = result.data

        # Handle list-wrapped responses from Crustdata
        item = raw_data[0] if (isinstance(raw_data, list) and raw_data) else raw_data
        person_record = normalize_crustdata_person(item if isinstance(item, dict) else {}, origin="crustdata_sourced")
        person_record.profile_url = norm_url

        # Upsert canonical Person
        db_person = PersonService.get_or_create_person(db, person_record)
        person_record.person_id = db_person.id
        return person_record

    @staticmethod
    def register_candidate(
        db: Session,
        email: str | None = None,
        name: str | None = None,
        profile_url: str | None = None,
        person_id: str | None = None,
        preferences: dict[str, Any] | None = None
    ) -> PersonRecord:
        """
        Registers candidate and links User + CandidateProfile to existing Person.
        Preserves all prior recruiter actions and match run history.
        """
        norm_url = None
        if profile_url:
            try:
                norm_url = normalize_profile_url(profile_url)
            except ValueError:
                norm_url = profile_url.strip()

        person: Person | None = None

        if person_id:
            person = db.query(Person).filter(Person.id == person_id).first()
        if not person and email:
            clean_email = email.strip().lower()
            existing_user = db.query(User).filter(User.email.ilike(clean_email)).first()
            if existing_user:
                existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == existing_user.id).first()
                if existing_profile and existing_profile.person_id:
                    person = db.query(Person).filter(Person.id == existing_profile.person_id).first()
        if not person and norm_url:
            person = db.query(Person).filter(Person.profile_url == norm_url).first()

        if not person:
            # Create fresh Person record
            person_rec = PersonRecord(
                person_id=str(uuid.uuid4()),
                profile_url=norm_url,
                origin="registered",
                membership_status="registered",
                name=name,
                candidate_preferences=preferences or {}
            )
            person = PersonService.get_or_create_person(db, person_rec)
        else:
            # Upgrade membership status without losing history
            person.membership_status = "registered"
            if name and not person.name:
                person.name = name
            db.commit()
            db.refresh(person)

        # Create or link User
        user_email = email or f"candidate_{person.id[:8]}@swipehire.local"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(
                email=user_email,
                role="candidate",
                name=name or person.name
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create or update CandidateProfile (query by person_id or user_id to prevent duplicate user_id conflict)
        profile = db.query(CandidateProfile).filter(
            (CandidateProfile.person_id == person.id) | (CandidateProfile.user_id == user.id)
        ).first()
        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                person_id=person.id,
                preferences=preferences or {}
            )
            db.add(profile)
        else:
            profile.person_id = person.id
            profile.user_id = user.id
            if preferences:
                profile.preferences = {**(profile.preferences or {}), **preferences}
        db.commit()

        # Update normalized profile JSON
        data = dict(person.profile_data or {})
        data["person_id"] = person.id
        data["membership_status"] = "registered"
        data["name"] = person.name
        data["candidate_preferences"] = profile.preferences
        person.profile_data = data
        db.commit()

        return PersonRecord(**data)
