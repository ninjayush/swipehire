import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.db import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crustdata_person_id = Column(Integer, unique=True, nullable=True, index=True)
    profile_url = Column(String(500), unique=True, nullable=True, index=True)
    origin = Column(String(50), nullable=False, default="crustdata_sourced")  # "registered" | "crustdata_sourced"
    membership_status = Column(String(50), nullable=False, default="not_registered")  # "registered" | "not_registered"
    
    # Normalized fields
    name = Column(String(255), nullable=True)
    headline = Column(String(500), nullable=True)
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Full normalized JSON payload (skills, experience, history, metadata)
    profile_data = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    candidate_profile = relationship("CandidateProfile", back_populates="person", uselist=False)
    actions = relationship("RecruiterAction", back_populates="person")
    interest_requests = relationship("InterestRequest", back_populates="person")
    matches = relationship("Match", back_populates="person")
