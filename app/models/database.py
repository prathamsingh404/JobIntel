import datetime
import uuid
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user")  # user, admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON or comma-separated list
    ats_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    glassdoor_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_hiring_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0 to 100
    hiring_trends_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    cleaned_jobs = relationship("CleanedJob", back_populates="company_profile")


class RawJob(Base):
    __tablename__ = "raw_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scraped_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships
    cleaned_job = relationship("CleanedJob", back_populates="raw_job", uselist=False)
    rejected_job = relationship("RejectedJob", back_populates="raw_job", uselist=False)


class CleanedJob(Base):
    __tablename__ = "cleaned_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    raw_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("raw_jobs.id"), nullable=False)
    company_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("companies.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    experience: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma separated or JSON list
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma separated or JSON list
    posted_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    clean_description: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    cleaned_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Enriched fields
    seniority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    workplace_type: Mapped[Optional[str]] = mapped_column(String(50), default="remote")  # remote, hybrid, onsite
    application_deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    job_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    recruiter_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recruiter_contact: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # Relationships
    raw_job = relationship("RawJob", back_populates="cleaned_job")
    company_profile = relationship("Company", back_populates="cleaned_jobs")
    ai_classified_job = relationship("AIClassifiedJob", back_populates="cleaned_job", uselist=False)
    versions = relationship("JobVersion", back_populates="cleaned_job", cascade="all, delete-orphan")


class JobVersion(Base):
    __tablename__ = "job_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("cleaned_jobs.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    changes_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text representing changes
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, closed, updated
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships
    cleaned_job = relationship("CleanedJob", back_populates="versions")


class RejectedJob(Base):
    __tablename__ = "rejected_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    raw_job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("raw_jobs.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships
    raw_job = relationship("RawJob", back_populates="rejected_job")


class AIClassifiedJob(Base):
    __tablename__ = "ai_classified_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    cleaned_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("cleaned_jobs.id"), nullable=False)
    ai_label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)  # 'accept' or 'reject'
    classified_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships
    cleaned_job = relationship("CleanedJob", back_populates="ai_classified_job")
    relevance_job = relationship("RelevanceJob", back_populates="ai_classified_job", uselist=False)


class RelevanceJob(Base):
    __tablename__ = "relevance_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    ai_classified_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_classified_jobs.id"), nullable=False
    )
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 to 100
    rank: Mapped[str] = mapped_column(String(20), nullable=False)  # reject, weak, moderate, good, excellent
    match_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON summary of match parameters
    evaluated_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships
    ai_classified_job = relationship("AIClassifiedJob", back_populates="relevance_job")


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    jobs_scraped: Mapped[int] = mapped_column(Integer, default=0)
    jobs_cleaned: Mapped[int] = mapped_column(Integer, default=0)
    jobs_rejected: Mapped[int] = mapped_column(Integer, default=0)
    jobs_classified: Mapped[int] = mapped_column(Integer, default=0)
    jobs_accepted: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running, success, failed


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    skills_extracted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class SkillKnowledgeGraph(Base):
    __tablename__ = "skill_knowledge_graph"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_skill: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    relationship_type: Mapped[str] = mapped_column(String(50), default="subset")  # subset, equivalent, dependency
