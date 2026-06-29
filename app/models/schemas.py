from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class RawJobCreate(BaseModel):
    source: str = Field(..., max_length=50)
    source_url: str = Field(..., max_length=512)
    company: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: str
    raw_json: Optional[str] = None
    raw_html: Optional[str] = None

class RawJobSchema(RawJobCreate):
    id: str
    scraped_date: datetime

    model_config = ConfigDict(from_attributes=True)

class CleanedJobCreate(BaseModel):
    raw_job_id: str
    title: str = Field(..., max_length=200)
    normalized_title: str = Field(..., max_length=100)
    company: str = Field(..., max_length=100)
    location: str = Field(..., max_length=150)
    employment_type: Optional[str] = Field(None, max_length=50)
    experience: Optional[str] = Field(None, max_length=100)
    salary: Optional[str] = Field(None, max_length=100)
    skills: Optional[str] = None
    benefits: Optional[str] = None
    posted_date: Optional[datetime] = None
    clean_description: str
    language: str = "en"

class CleanedJobSchema(CleanedJobCreate):
    id: str
    cleaned_date: datetime

    model_config = ConfigDict(from_attributes=True)

class RejectedJobCreate(BaseModel):
    raw_job_id: Optional[str] = None
    source: str = Field(..., max_length=50)
    company: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    reason: str

class RejectedJobSchema(RejectedJobCreate):
    id: str
    rejected_date: datetime

    model_config = ConfigDict(from_attributes=True)

class AIClassifiedJobCreate(BaseModel):
    cleaned_job_id: str
    ai_label: str = Field(..., max_length=100)
    confidence: float
    reason: str
    evidence: Optional[str] = None
    decision: str = Field(..., max_length=10)  # 'accept' or 'reject'

class AIClassifiedJobSchema(AIClassifiedJobCreate):
    id: str
    classified_date: datetime

    model_config = ConfigDict(from_attributes=True)

class RelevanceJobCreate(BaseModel):
    ai_classified_job_id: str
    relevance_score: int
    rank: str = Field(..., max_length=20)  # reject, weak, moderate, good, excellent
    match_details: Optional[str] = None

class RelevanceJobSchema(RelevanceJobCreate):
    id: str
    evaluated_date: datetime

    model_config = ConfigDict(from_attributes=True)

class PipelineLogSchema(BaseModel):
    id: int
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    jobs_scraped: int
    jobs_cleaned: int
    jobs_rejected: int
    jobs_classified: int
    jobs_accepted: int
    status: str

    model_config = ConfigDict(from_attributes=True)

# Schema for AI Provider output
class AIServiceResult(BaseModel):
    ai_label: str
    confidence: float
    reason: str
    evidence: Optional[str] = None
    decision: str  # 'accept' or 'reject'
