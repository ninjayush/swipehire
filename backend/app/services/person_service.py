import re
import uuid
from typing import Any
from urllib.parse import urlparse, urlunparse
from sqlalchemy.orm import Session
from app.models.person import Person
from app.models.user import User, CandidateProfile
from app.database.schemas import PersonRecord
from app.integrations.crustdata import crustdata_client, CrustdataError

def normalize_profile_url(url: str | None) -> str | None:
    """Normalize professional profile URLs for consistent deduplication."""
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.netloc:
        return url.lower().rstrip("/")
    
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    path = parsed.path.lower().rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))

def normalize_crustdata_person(data: dict[str, Any], origin: str = "crustdata_sourced") -> PersonRecord:
    """
    Transforms raw Crustdata person response into the canonical PersonRecord contract.
    Handles varied key structures gracefully.
    """
    person_id = str(uuid.uuid4())
    
    # Crustdata person ID
    crustdata_id = data.get("crustdata_person_id") or data.get("id") or data.get("person_id")
    if isinstance(crustdata_id, str) and crustdata_id.isdigit():
        crustdata_id = int(crustdata_id)
    elif not isinstance(crustdata_id, int):
        crustdata_id = None

    # Profile URL
    raw_url = data.get("profile_url") or data.get("linkedin_profile_url") or data.get("linkedin_url")
    profile_url = normalize_profile_url(raw_url)

    # Name
    name = data.get("name") or data.get("full_name")
    if not name:
        first = data.get("first_name", "")
        last = data.get("last_name", "")
        name = f"{first} {last}".strip() or None

    headline = data.get("headline") or data.get("summary")
    current_title = data.get("current_title") or data.get("title")
    current_company = data.get("current_company") or data.get("company_name")
    location = data.get("location") or data.get("city")

    # Skills extraction
    raw_skills = data.get("skills", [])
    skills: list[str] = []
    if isinstance(raw_skills, list):
        for s in raw_skills:
            if isinstance(s, str):
                skills.append(s)
            elif isinstance(s, dict) and "name" in s:
                skills.append(s["name"])

    # Experience years
    exp_years = data.get("experience_years") or data.get("years_of_experience")
    if exp_years is not None:
        try:
            exp_years = float(exp_years)
        except (ValueError, TypeError):
            exp_years = None

    # Employment & Education
    employment = data.get("employment_history") or data.get("work_experience") or []
    if not isinstance(employment, list):
        employment = []

    education = data.get("education") or []
    if not isinstance(education, list):
        education = []

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
        source_metadata=[{"raw_source": "crustdata" if origin == "crustdata_sourced" else "user_registration"}],
    )


class PersonService:
    @staticmethod
    def get_or_create_person(db: Session, record: PersonRecord) -> Person:
        """
        Finds existing person by crustdata_person_id or normalized profile_url,
        preventing duplicate person records in the system.
        """
        existing: Person | None = None

        if record.crustdata_person_id:
            existing = db.query(Person).filter(Person.crustdata_person_id == record.crustdata_person_id).first()

        if not existing and record.profile_url:
            norm_url = normalize_profile_url(record.profile_url)
            existing = db.query(Person).filter(Person.profile_url == norm_url).first()

        if existing:
            # Update attributes without overwriting canonical ID
            record.person_id = existing.id
            if not existing.crustdata_person_id and record.crustdata_person_id:
                existing.crustdata_person_id = record.crustdata_person_id
            if not existing.profile_url and record.profile_url:
                existing.profile_url = normalize_profile_url(record.profile_url)
            if record.name and not existing.name:
                existing.name = record.name
            if record.current_title and not existing.current_title:
                existing.current_title = record.current_title
            if record.current_company and not existing.current_company:
                existing.current_company = record.current_company
            if record.location and not existing.location:
                existing.location = record.location
            
            # Merge profile data
            existing.profile_data = record.model_dump()
            db.commit()
            db.refresh(existing)
            return existing

        # Create new person
        norm_url = normalize_profile_url(record.profile_url)
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
        Calls Crustdata person/enrich, normalizes into PersonRecord,
        deduplicates and persists to database.
        """
        norm_url = normalize_profile_url(profile_url)
        
        # Check DB first for existing person
        existing = db.query(Person).filter(Person.profile_url == norm_url).first()
        if existing and existing.profile_data:
            rec = PersonRecord(**existing.profile_data)
            rec.person_id = existing.id
            rec.membership_status = existing.membership_status  # type: ignore
            return rec

        # Call Crustdata
        raw_data = await crustdata_client.enrich_person(norm_url)
        person_record = normalize_crustdata_person(raw_data, origin="crustdata_sourced")
        person_record.profile_url = norm_url

        # Save to DB
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
        Registers a candidate or links an existing sourced person to a registered profile.
        Never duplicates Person records.
        """
        norm_url = normalize_profile_url(profile_url)
        person: Person | None = None

        if person_id:
            person = db.query(Person).filter(Person.id == person_id).first()
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
            # Upgrade membership status
            person.membership_status = "registered"
            if name and not person.name:
                person.name = name
            db.commit()
            db.refresh(person)

        # Create or update User
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

        # Create or update CandidateProfile
        profile = db.query(CandidateProfile).filter(CandidateProfile.person_id == person.id).first()
        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                person_id=person.id,
                preferences=preferences or {}
            )
            db.add(profile)
        else:
            if preferences:
                profile.preferences = {**profile.preferences, **preferences}
        db.commit()

        # Update profile_data
        data = dict(person.profile_data or {})
        data["person_id"] = person.id
        data["membership_status"] = "registered"
        data["name"] = person.name
        data["candidate_preferences"] = profile.preferences
        person.profile_data = data
        db.commit()

        return PersonRecord(**data)
