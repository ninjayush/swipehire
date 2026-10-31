import uuid
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.job import JobRole
from app.models.person import Person
from app.models.match import MatchRun, CandidateMatch
from app.database.schemas import JobRequirements, PersonRecord, CandidateEvaluation, CandidateDeckResponse
from app.services.person_service import PersonService, normalize_crustdata_person, normalize_profile_url
from app.integrations.crustdata import crustdata_client

logger = logging.getLogger("discovery")

def get_person_2_deck_builder():
    """Dynamically import Person 2's matching function if available, else use baseline fallback."""
    try:
        from app.matching.deck import build_candidate_deck
        return build_candidate_deck
    except (ImportError, ModuleNotFoundError):
        logger.info("Person 2 matching module not yet installed; using baseline evaluation fallback.")
        return fallback_build_candidate_deck

def fallback_build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
    """
    Temporary baseline implementation complying with Person 2's exact signature.
    Replaced when Person 2 merges app.matching.deck.
    """
    displayed: list[CandidateEvaluation] = []
    excluded: list[CandidateEvaluation] = []

    req_skills = set(s.lower() for s in requirements.must_have_skills)

    for cand in candidates:
        cand_skills = set(s.lower() for s in cand.skills)
        matched = req_skills.intersection(cand_skills) if req_skills else set()
        coverage = len(matched) / len(req_skills) if req_skills else 1.0

        # Check dealbreakers
        dealbreaker_triggered = False
        reasons: list[str] = []
        if requirements.min_experience_years and cand.experience_years:
            if cand.experience_years < requirements.min_experience_years:
                dealbreaker_triggered = True
                reasons.append(f"Requires {requirements.min_experience_years}+ yrs, has {cand.experience_years} yrs")

        if dealbreaker_triggered:
            excluded.append(CandidateEvaluation(
                person_id=cand.person_id,
                eligible=False,
                exclusion_reasons=reasons,
                fit_score=0.0,
                fit_type=None,
                reasons=reasons
            ))
        else:
            score = round(min(100.0, (coverage * 70.0) + 30.0), 1)
            fit_type = "direct" if score >= 75.0 else "adjacent"
            displayed.append(CandidateEvaluation(
                person_id=cand.person_id,
                eligible=True,
                fit_score=score,
                evidence_coverage=coverage,
                fit_type=fit_type,
                reasons=[f"Matched skills: {', '.join(matched) or 'General fit'}"],
                match_explanation=f"Profile has strong alignment with {requirements.title}."
            ))

    displayed.sort(key=lambda x: x.fit_score or 0.0, reverse=True)
    for idx, eval_item in enumerate(displayed[:deck_size]):
        eval_item.rank = idx + 1

    return displayed[:deck_size], excluded


class DiscoveryService:
    @staticmethod
    async def run_discovery_and_matching(db: Session, job_id: str) -> CandidateDeckResponse:
        """
        Executes candidate discovery pipeline:
        1. Fetch registered candidates from DB
        2. Query Crustdata search for external candidates
        3. Deduplicate and normalize
        4. Call matching deck builder (Person 2)
        5. Persist MatchRun and CandidateMatch records
        6. Return CandidateDeckResponse
        """
        job = db.query(JobRole).filter(JobRole.id == job_id).first()
        if not job:
            raise ValueError(f"Job with id {job_id} not found")

        requirements = JobRequirements(**job.requirements)

        # 1. Gather registered candidates from DB
        db_persons = db.query(Person).all()
        candidates_by_id: dict[str, PersonRecord] = {}

        for p in db_persons:
            record_dict = dict(p.profile_data or {})
            record_dict["person_id"] = p.id
            record_dict["membership_status"] = p.membership_status
            record = PersonRecord(**record_dict)
            candidates_by_id[p.id] = record

        # 2. Query Crustdata search
        search_query: dict[str, Any] = {}
        if requirements.title:
            search_query["title"] = requirements.title
        if requirements.locations:
            search_query["location"] = requirements.locations[0]
        if requirements.must_have_skills:
            search_query["skills"] = requirements.must_have_skills[:3]

        try:
            search_result = await crustdata_client.search_persons(query=search_query, limit=10)
            items = search_result.get("profiles") or search_result.get("data") or search_result.get("results") or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        rec = normalize_crustdata_person(item, origin="crustdata_sourced")
                        # Deduplicate & persist
                        saved = PersonService.get_or_create_person(db, rec)
                        rec.person_id = saved.id
                        rec.membership_status = saved.membership_status  # type: ignore
                        candidates_by_id[saved.id] = rec
        except Exception as e:
            logger.warning(f"Crustdata search failed or returned no results: {e}")

        all_candidates = list(candidates_by_id.values())

        # 3. Call matching deck function
        deck_builder = get_person_2_deck_builder()
        displayed_evals, excluded_evals = deck_builder(requirements, all_candidates, deck_size=20)

        # 4. Persist MatchRun
        run_id = str(uuid.uuid4())
        direct_count = sum(1 for e in displayed_evals if e.fit_type == "direct")
        adjacent_count = sum(1 for e in displayed_evals if e.fit_type == "adjacent")

        match_run = MatchRun(
            id=run_id,
            job_id=job.id,
            status="completed",
            total_candidates=len(all_candidates),
            direct_count=direct_count,
            adjacent_count=adjacent_count,
            excluded_count=len(excluded_evals),
            diagnostics={"candidate_pool_size": len(all_candidates)}
        )
        db.add(match_run)
        db.commit()

        # 5. Persist CandidateMatch records
        cards: list[dict[str, Any]] = []

        for eval_res in displayed_evals:
            cm = CandidateMatch(
                job_id=job.id,
                match_run_id=run_id,
                person_id=eval_res.person_id,
                eligible=True,
                fit_score=eval_res.fit_score,
                component_scores=eval_res.component_scores,
                evidence_coverage=eval_res.evidence_coverage,
                fit_type=eval_res.fit_type,
                rank=eval_res.rank,
                match_explanation=eval_res.match_explanation,
                reasons=eval_res.reasons,
                exclusion_reasons=[]
            )
            db.add(cm)
            cand_record = candidates_by_id.get(eval_res.person_id)
            if cand_record:
                card_data = {
                    "person": cand_record.model_dump(),
                    "evaluation": eval_res.model_dump()
                }
                cards.append(card_data)

        for eval_res in excluded_evals:
            cm = CandidateMatch(
                job_id=job.id,
                match_run_id=run_id,
                person_id=eval_res.person_id,
                eligible=False,
                fit_score=eval_res.fit_score or 0.0,
                component_scores=eval_res.component_scores,
                exclusion_reasons=eval_res.exclusion_reasons,
                reasons=eval_res.reasons
            )
            db.add(cm)

        db.commit()

        return CandidateDeckResponse(
            job_id=job.id,
            match_run_id=run_id,
            status="completed",
            total_candidates=len(all_candidates),
            direct_count=direct_count,
            adjacent_count=adjacent_count,
            excluded_count=len(excluded_evals),
            cards=cards
        )
