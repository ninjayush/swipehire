import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class JobRole(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # "active" | "draft" | "closed"
    raw_jd = Column(Text, nullable=True)
    requirements = Column(JSON, nullable=False, default=dict)  # Stores JobRequirements dict

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    match_runs = relationship("MatchRun", back_populates="job")
    candidate_matches = relationship("CandidateMatch", back_populates="job")
    recruiter_actions = relationship("RecruiterAction", back_populates="job")
    interest_requests = relationship("InterestRequest", back_populates="job")
    matches = relationship("Match", back_populates="job")
