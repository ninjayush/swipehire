from typing import Literal
from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    title: str
    seniority: str | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    locations: list[str] = Field(default_factory=list)
    work_modes: list[str] = Field(default_factory=list)
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    mandatory_qualifications: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    dealbreakers: list[str] = Field(default_factory=list)
    unknown_or_needs_confirmation: list[str] = Field(default_factory=list)
    raw_jd: str | None = None


class PersonRecord(BaseModel):
    person_id: str
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
    experience_years: float | None = None
    employment_history: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    resume_highlights: list[dict] = Field(default_factory=list)
    candidate_preferences: dict = Field(default_factory=dict)
    source_metadata: list[dict] = Field(default_factory=list)


class CandidateEvaluation(BaseModel):
    person_id: str
    eligible: bool
    exclusion_reasons: list[str] = Field(default_factory=list)
    fit_score: float | None = None
    component_scores: dict[str, float] = Field(default_factory=dict)
    evidence_coverage: float | None = None
    fit_type: Literal["direct", "adjacent"] | None = None
    match_explanation: str | None = None
    reasons: list[str] = Field(default_factory=list)
    rank: int | None = None
