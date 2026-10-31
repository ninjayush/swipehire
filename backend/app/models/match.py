import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class MatchRun(Base):
    __tablename__ = "match_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), nullable=False, default="processing")  # "completed", "failed", "processing"
    input_hash = Column(String(64), nullable=True)
    total_candidates = Column(Integer, default=0)
    direct_count = Column(Integer, default=0)
    adjacent_count = Column(Integer, default=0)
    excluded_count = Column(Integer, default=0)
    diagnostics = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("JobRole", back_populates="match_runs")
    candidate_matches = relationship("CandidateMatch", back_populates="match_run")


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    match_run_id = Column(String(36), ForeignKey("match_runs.id"), nullable=False)
    person_id = Column(String(36), ForeignKey("persons.id"), nullable=False)

    eligible = Column(Boolean, nullable=False, default=True)
    fit_score = Column(Float, nullable=True)
    component_scores = Column(JSON, nullable=False, default=dict)
    evidence_coverage = Column(Float, nullable=True)
    fit_type = Column(String(50), nullable=True)  # "direct", "adjacent"
    rank = Column(Integer, nullable=True)
    match_explanation = Column(String, nullable=True)
    reasons = Column(JSON, nullable=False, default=list)
    exclusion_reasons = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("JobRole", back_populates="candidate_matches")
    match_run = relationship("MatchRun", back_populates="candidate_matches")
    evidence_items = relationship("EvidenceItem", back_populates="candidate_match")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_match_id = Column(String(36), ForeignKey("candidate_matches.id"), nullable=False)
    criterion = Column(String(255), nullable=False)
    evidence_text = Column(String, nullable=False)
    source_type = Column(String(50), nullable=False, default="crustdata_profile")  # "resume", "crustdata_profile", "user_input"
    confidence_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    candidate_match = relationship("CandidateMatch", back_populates="evidence_items")


class RecruiterAction(Base):
    __tablename__ = "recruiter_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    person_id = Column(String(36), ForeignKey("persons.id"), nullable=False)
    action = Column(String(50), nullable=False)  # "shortlist", "pass", "save"
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("JobRole", back_populates="recruiter_actions")
    person = relationship("Person", back_populates="actions")


class InterestRequest(Base):
    __tablename__ = "interest_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    person_id = Column(String(36), ForeignKey("persons.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # "pending", "accepted", "rejected"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    job = relationship("JobRole", back_populates="interest_requests")
    person = relationship("Person", back_populates="interest_requests")
    match = relationship("Match", back_populates="interest_request", uselist=False)


class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    person_id = Column(String(36), ForeignKey("persons.id"), nullable=False)
    interest_request_id = Column(String(36), ForeignKey("interest_requests.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("JobRole", back_populates="matches")
    person = relationship("Person", back_populates="matches")
    interest_request = relationship("InterestRequest", back_populates="match")
