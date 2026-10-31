import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crustdata_company_id = Column(Integer, unique=True, nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    enriched_data = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("CompanyMember", back_populates="company")
    jobs = relationship("JobRole", back_populates="company")


class CompanyMember(Base):
    __tablename__ = "company_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default="recruiter")  # "recruiter" | "admin"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="members")
    user = relationship("User", back_populates="company_memberships")
