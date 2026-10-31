from typing import Literal, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Core Shared Contracts (Frozen for Persons 1, 2, and 3)
# ---------------------------------------------------------

class JobRequirements(BaseModel):
    title: str
    seniority: str | None = None
    min_experience_years: float | None = Field(default=None, ge=0.0)
    max_experience_years: float | None = Field(default=None, ge=0.0)
    locations: list[str] = Field(default_factory=list)
    work_modes: list[str] = Field(default_factory=list)       # e.g. onsite, hybrid, remote
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    mandatory_qualifications: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)  # e.g. availability, resume, salary
    dealbreakers: list[str] = Field(default_factory=list)
    unknown_or_needs_confirmation: list[str] = Field(default_factory=list)
    raw_jd: str | None = None


class PersonRecord(BaseModel):
    person_id: str                         # SwipeHire canonical ID (UUID/string)
    crustdata_person_id: int | None = None
    profile_url: str | None = None
    origin: Literal["registered", "crustdata_sourced"]
    membership_status: Literal["registered", "not_registered"]
    name: str | None = None
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0.0)
    employment_history: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    resume_highlights: list[dict[str, Any]] = Field(default_factory=list)
    candidate_preferences: dict[str, Any] = Field(default_factory=dict)
    source_metadata: list[dict[str, Any]] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str | None = None
    candidate_match_id: str | None = None
    criterion: str
    evidence_text: str
    source_type: Literal["resume", "crustdata_profile", "user_input"] = "crustdata_profile"
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class CandidateEvaluation(BaseModel):
    person_id: str
    eligible: bool
    exclusion_reasons: list[str] = Field(default_factory=list)
    fit_score: float | None = Field(default=None, ge=0.0, le=100.0)
    component_scores: dict[str, float] = Field(default_factory=dict)
    evidence_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    fit_type: Literal["direct", "adjacent"] | None = None
    match_explanation: str | None = None
    reasons: list[str] = Field(default_factory=list)
    rank: int | None = Field(default=None, ge=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CandidateDeckResponse(BaseModel):
    job_id: str
    match_run_id: str
    status: Literal["completed", "failed", "processing"]
    total_candidates: int = Field(default=0, ge=0)
    direct_count: int = Field(default=0, ge=0)
    adjacent_count: int = Field(default=0, ge=0)
    excluded_count: int = Field(default=0, ge=0)
    cards: list[dict[str, Any]] = Field(default_factory=list)  # serialized PersonRecord + CandidateEvaluation


# ---------------------------------------------------------
# REST API DTOs (Request / Response schemas for endpoints)
# ---------------------------------------------------------

class CandidateEnrichRequest(BaseModel):
    profile_url: str

class CandidateEnrichResponse(BaseModel):
    person: PersonRecord

class CandidateRegisterRequest(BaseModel):
    person_id: str | None = None
    email: str | None = None
    name: str | None = None
    profile_url: str | None = None
    candidate_preferences: dict[str, Any] = Field(default_factory=dict)

class CompanyResolveRequest(BaseModel):
    company_name: str | None = None
    domain: str | None = None

class CompanyResolveResponse(BaseModel):
    company_id: str
    name: str
    domain: str | None = None
    enriched: dict[str, Any] = Field(default_factory=dict)
    ambiguous_options: list[dict[str, Any]] = Field(default_factory=list)

class JobCreateRequest(BaseModel):
    company_id: str
    input_type: Literal["jd", "structured"]
    raw_jd: str | None = None
    requirements: JobRequirements | dict[str, Any] | None = None

class JobResponse(BaseModel):
    job_id: str
    company_id: str
    requirements: JobRequirements
    status: str

class JobUpdateRequest(BaseModel):
    title: str | None = None
    status: str | None = None
    requirements: dict[str, Any] | JobRequirements | None = None

class RecruiterActionRequest(BaseModel):
    person_id: str
    action: Literal["shortlist", "pass", "save"]

class InterestRespondRequest(BaseModel):
    response: Literal["accept", "reject"]
