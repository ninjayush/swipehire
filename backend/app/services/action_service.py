import uuid
from datetime import datetime, timezone
from typing import Literal, Any
from sqlalchemy.orm import Session
from app.models.person import Person
from app.models.match import RecruiterAction, InterestRequest, Match
from app.models.job import JobRole

class ActionService:
    @staticmethod
    def record_recruiter_action(
        db: Session,
        job_id: str,
        person_id: str,
        action: Literal["shortlist", "pass", "save"],
        notes: str | None = None
    ) -> dict[str, Any]:
        """
        Records recruiter action.
        - For a registered candidate, shortlist creates a pending InterestRequest.
        - For a Crustdata-sourced non-member, shortlist creates ONLY an internal recruiter action.
        - No external outreach, emails, or webhooks are sent to real people.
        """
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise ValueError(f"Person {person_id} not found")

        job = db.query(JobRole).filter(JobRole.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Save RecruiterAction
        recruiter_action = RecruiterAction(
            job_id=job_id,
            person_id=person_id,
            action=action,
            notes=notes
        )
        db.add(recruiter_action)

        interest_request_id = None
        # Only create InterestRequest if candidate is registered and action is shortlist
        if action == "shortlist":
            if person.membership_status == "registered":
                existing_ir = db.query(InterestRequest).filter(
                    InterestRequest.job_id == job_id,
                    InterestRequest.person_id == person_id
                ).first()
                if not existing_ir:
                    ir = InterestRequest(
                        job_id=job_id,
                        person_id=person_id,
                        status="pending"
                    )
                    db.add(ir)
                    db.commit()
                    db.refresh(ir)
                    interest_request_id = ir.id
                else:
                    interest_request_id = existing_ir.id
            else:
                # Sourced non-member: internal-only action, no InterestRequest created
                db.commit()
        else:
            db.commit()

        return {
            "status": "success",
            "action": action,
            "person_id": person_id,
            "membership_status": person.membership_status,
            "interest_request_id": interest_request_id
        }

    @staticmethod
    def respond_to_interest(
        db: Session,
        interest_id: str,
        response: Literal["accept", "reject"]
    ) -> dict[str, Any]:
        """
        Candidate responds to recruiter interest request.
        A Match is created ONLY when a registered candidate accepts.
        Idempotent: Repeated accept requests return the existing match without creating duplicates.
        """
        ir = db.query(InterestRequest).filter(InterestRequest.id == interest_id).first()
        if not ir:
            raise ValueError(f"Interest request {interest_id} not found")

        person = db.query(Person).filter(Person.id == ir.person_id).first()
        if not person or person.membership_status != "registered":
            raise PermissionError("Sourced non-members cannot receive or respond to interest requests.")

        ir.status = "accepted" if response == "accept" else "rejected"
        ir.responded_at = datetime.now(timezone.utc)

        match_id = None
        if response == "accept":
            # Idempotency check: if match already exists, return it without duplicate row
            existing_match = db.query(Match).filter(
                Match.job_id == ir.job_id,
                Match.person_id == ir.person_id
            ).first()

            if not existing_match:
                new_match = Match(
                    job_id=ir.job_id,
                    person_id=ir.person_id,
                    interest_request_id=ir.id
                )
                db.add(new_match)
                db.commit()
                db.refresh(new_match)
                match_id = new_match.id
            else:
                match_id = existing_match.id
        else:
            db.commit()

        return {
            "status": "success",
            "interest_id": ir.id,
            "response": response,
            "match_id": match_id
        }

    @staticmethod
    def sanitize_candidate_profile_for_viewer(profile_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Enforces candidate privacy:
        If candidate_preferences.salary_visible is False, masks salary and compensation fields.
        """
        sanitized = dict(profile_dict)
        prefs = sanitized.get("candidate_preferences")
        if isinstance(prefs, dict):
            salary_visible = prefs.get("salary_visible", True)
            if not salary_visible:
                sanitized_prefs = dict(prefs)
                sanitized_prefs.pop("expected_salary", None)
                sanitized_prefs.pop("salary", None)
                sanitized_prefs.pop("current_salary", None)
                sanitized_prefs["salary_visible"] = False
                sanitized["candidate_preferences"] = sanitized_prefs
        return sanitized
