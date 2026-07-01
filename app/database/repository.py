import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    User,
    Company,
    RawJob,
    CleanedJob,
    JobVersion,
    RejectedJob,
    AIClassifiedJob,
    RelevanceJob,
    PipelineLog,
    Resume,
    SkillKnowledgeGraph
)
from app.models.schemas import (
    RawJobCreate,
    CleanedJobCreate,
    RejectedJobCreate,
    AIClassifiedJobCreate,
    RelevanceJobCreate
)

class JobRepository:
    @staticmethod
    async def get_raw_job_by_url(session: AsyncSession, url: str) -> Optional[RawJob]:
        """Check if a job URL already exists in the raw_jobs table."""
        stmt = select(RawJob).where(RawJob.source_url == url)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_raw_job(session: AsyncSession, job_in: RawJobCreate) -> RawJob:
        """Saves a new raw job."""
        raw_job = RawJob(
            source=job_in.source,
            source_url=job_in.source_url,
            company=job_in.company,
            title=job_in.title,
            description=job_in.description,
            raw_json=job_in.raw_json,
            raw_html=job_in.raw_html
        )
        session.add(raw_job)
        await session.flush()  # Populates raw_job.id and raw_job.scraped_date
        return raw_job

    @staticmethod
    async def save_cleaned_job(session: AsyncSession, job_in: CleanedJobCreate) -> CleanedJob:
        """Saves a cleaned job record."""
        cleaned_job = CleanedJob(
            raw_job_id=job_in.raw_job_id,
            title=job_in.title,
            normalized_title=job_in.normalized_title,
            company=job_in.company,
            location=job_in.location,
            employment_type=job_in.employment_type,
            experience=job_in.experience,
            salary=job_in.salary,
            skills=job_in.skills,
            benefits=job_in.benefits,
            posted_date=job_in.posted_date,
            clean_description=job_in.clean_description,
            language=job_in.language
        )
        session.add(cleaned_job)
        await session.flush()
        return cleaned_job

    @staticmethod
    async def save_rejected_job(session: AsyncSession, job_in: RejectedJobCreate) -> RejectedJob:
        """Saves a rejected job record."""
        rejected_job = RejectedJob(
            raw_job_id=job_in.raw_job_id,
            source=job_in.source,
            company=job_in.company,
            title=job_in.title,
            reason=job_in.reason
        )
        session.add(rejected_job)
        await session.flush()
        return rejected_job

    @staticmethod
    async def save_ai_classified_job(
        session: AsyncSession, job_in: AIClassifiedJobCreate
    ) -> AIClassifiedJob:
        """Saves an AI classification result."""
        classified_job = AIClassifiedJob(
            cleaned_job_id=job_in.cleaned_job_id,
            ai_label=job_in.ai_label,
            confidence=job_in.confidence,
            reason=job_in.reason,
            evidence=job_in.evidence,
            decision=job_in.decision
        )
        session.add(classified_job)
        await session.flush()
        return classified_job

    @staticmethod
    async def save_relevance_job(
        session: AsyncSession, job_in: RelevanceJobCreate
    ) -> RelevanceJob:
        """Saves a relevance evaluation."""
        relevance_job = RelevanceJob(
            ai_classified_job_id=job_in.ai_classified_job_id,
            relevance_score=job_in.relevance_score,
            rank=job_in.rank,
            match_details=job_in.match_details
        )
        session.add(relevance_job)
        await session.flush()
        return relevance_job

    @staticmethod
    async def create_pipeline_log(session: AsyncSession, log: PipelineLog) -> PipelineLog:
        """Logs the start of a pipeline run."""
        session.add(log)
        await session.flush()
        return log

    @staticmethod
    async def update_pipeline_log(
        session: AsyncSession, run_id: str, updates: Dict[str, Any]
    ) -> None:
        """Updates pipeline run statistics upon completion or failure."""
        stmt = (
            update(PipelineLog)
            .where(PipelineLog.run_id == run_id)
            .values(**updates, completed_at=datetime.datetime.utcnow())
        )
        await session.execute(stmt)

    @staticmethod
    async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
        """Aggregates and compiles system stats for dashboard analytics."""
        # Total counts in each table
        raw_count = (await session.execute(select(func.count(RawJob.id)))).scalar_one() or 0
        cleaned_count = (await session.execute(select(func.count(CleanedJob.id)))).scalar_one() or 0
        rejected_count = (await session.execute(select(func.count(RejectedJob.id)))).scalar_one() or 0
        classified_count = (
            await session.execute(select(func.count(AIClassifiedJob.id)))
        ).scalar_one() or 0
        relevant_count = (await session.execute(select(func.count(RelevanceJob.id)))).scalar_one() or 0
        avg_relevance = (await session.execute(select(func.avg(RelevanceJob.relevance_score)))).scalar_one() or 0.0

        # Distribution of AI Labels (Canonical roles)
        ai_stmt = (
            select(AIClassifiedJob.ai_label, func.count(AIClassifiedJob.id))
            .group_by(AIClassifiedJob.ai_label)
        )
        ai_rows = (await session.execute(ai_stmt)).all()
        ai_dist = {row[0]: row[1] for row in ai_rows}

        # Distribution of Relevance Ranks
        rank_stmt = (
            select(RelevanceJob.rank, func.count(RelevanceJob.id))
            .group_by(RelevanceJob.rank)
        )
        rank_rows = (await session.execute(rank_stmt)).all()
        rank_dist = {row[0]: row[1] for row in rank_rows}

        # Top hiring companies
        company_stmt = (
            select(CleanedJob.company, func.count(CleanedJob.id))
            .group_by(CleanedJob.company)
            .order_by(desc(func.count(CleanedJob.id)))
            .limit(10)
        )
        company_rows = (await session.execute(company_stmt)).all()
        top_companies = {row[0]: row[1] for row in company_rows}

        # Top locations
        loc_stmt = (
            select(CleanedJob.location, func.count(CleanedJob.id))
            .group_by(CleanedJob.location)
            .order_by(desc(func.count(CleanedJob.id)))
            .limit(10)
        )
        loc_rows = (await session.execute(loc_stmt)).all()
        top_locations = {row[0]: row[1] for row in loc_rows}

        # Ingestion funnel stats (from log history)
        funnel_stmt = (
            select(
                func.sum(PipelineLog.jobs_scraped),
                func.sum(PipelineLog.jobs_cleaned),
                func.sum(PipelineLog.jobs_rejected),
                func.sum(PipelineLog.jobs_classified),
                func.sum(PipelineLog.jobs_accepted),
            )
        )
        funnel_res = (await session.execute(funnel_stmt)).one_or_none()
        funnel = {
            "scraped": int(funnel_res[0]) if funnel_res and funnel_res[0] else 0,
            "cleaned": int(funnel_res[1]) if funnel_res and funnel_res[1] else 0,
            "rejected": int(funnel_res[2]) if funnel_res and funnel_res[2] else 0,
            "classified": int(funnel_res[3]) if funnel_res and funnel_res[3] else 0,
            "accepted": int(funnel_res[4]) if funnel_res and funnel_res[4] else 0,
        }

        # Rejected reasons counts
        reason_stmt = (
            select(RejectedJob.reason, func.count(RejectedJob.id))
            .group_by(RejectedJob.reason)
            .order_by(desc(func.count(RejectedJob.id)))
            .limit(5)
        )
        reason_rows = (await session.execute(reason_stmt)).all()
        rejected_reasons = {}
        for row in reason_rows:
            reason = row[0]
            # Group common reasons for summary
            if "Duplicate" in reason:
                reason = "Duplicate Job Listing"
            elif "Failed rule" in reason:
                reason = "Keyword Validation Failed"
            rejected_reasons[reason] = rejected_reasons.get(reason, 0) + row[1]

        # Recent pipeline runs
        runs_stmt = select(PipelineLog).order_by(desc(PipelineLog.started_at)).limit(5)
        runs_res = (await session.execute(runs_stmt)).scalars().all()
        recent_runs = [
            {
                "run_id": r.run_id,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "jobs_scraped": r.jobs_scraped,
                "jobs_cleaned": r.jobs_cleaned,
                "jobs_rejected": r.jobs_rejected,
                "jobs_classified": r.jobs_classified,
                "jobs_accepted": r.jobs_accepted,
                "status": r.status,
            }
            for r in runs_res
        ]

        return {
            "counts": {
                "raw": raw_count,
                "cleaned": cleaned_count,
                "rejected": rejected_count,
                "classified": classified_count,
                "relevant": relevant_count,
            },
            "avg_relevance_score": float(avg_relevance),
            "distributions": {
                "roles": ai_dist,
                "relevance": rank_dist,
            },
            "top_companies": top_companies,
            "top_locations": top_locations,
            "funnel": funnel,
            "rejected_reasons": rejected_reasons,
            "recent_runs": recent_runs,
        }

    @staticmethod
    async def get_recent_jobs(
        session: AsyncSession,
        limit: int = 50,
        search: Optional[str] = None,
        role: Optional[str] = None,
        rank: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch processed jobs join query for exploration in dashboard."""
        stmt = (
            select(CleanedJob)
            .join(AIClassifiedJob, AIClassifiedJob.cleaned_job_id == CleanedJob.id)
            .join(RelevanceJob, RelevanceJob.ai_classified_job_id == AIClassifiedJob.id)
            .options(
                selectinload(CleanedJob.ai_classified_job).selectinload(
                    AIClassifiedJob.relevance_job
                ),
                selectinload(CleanedJob.raw_job),
                selectinload(CleanedJob.versions)
            )
        )

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (CleanedJob.title.ilike(search_pattern)) |
                (CleanedJob.company.ilike(search_pattern)) |
                (CleanedJob.clean_description.ilike(search_pattern)) |
                (CleanedJob.skills.ilike(search_pattern))
            )
        if role:
            stmt = stmt.where(CleanedJob.normalized_title == role)
        if rank:
            stmt = stmt.where(RelevanceJob.rank == rank)

        stmt = stmt.order_by(desc(CleanedJob.cleaned_date)).limit(limit)
        results = (await session.execute(stmt)).scalars().all()

        jobs_list = []
        for job in results:
            class_info = job.ai_classified_job
            rel_info = class_info.relevance_job if class_info else None
            jobs_list.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "description": job.clean_description,
                    "url": job.raw_job.source_url if job.raw_job else "",
                    "salary_min": None,
                    "salary_max": None,
                    "salary_currency": job.salary_currency,
                    "workplace_type": job.workplace_type,
                    "seniority": job.seniority,
                    "skills": job.skills,
                    "relevance_score": (rel_info.relevance_score / 100.0) if rel_info else 0.5,
                    "relevance_explanation": rel_info.match_details if rel_info else (class_info.reason if class_info else ""),
                    "rank": rel_info.rank if rel_info else "reject",
                    "collected_at": job.cleaned_date.isoformat(),
                    "versions": [
                        {
                            "version_number": v.version_number,
                            "updated_at": v.updated_at.isoformat(),
                            "changes_payload": v.changes_payload
                        } for v in job.versions
                    ] if job.versions else []
                }
            )
        return jobs_list

    @staticmethod
    async def get_all_relevant_records_for_export(session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch all high-fidelity relevant records for dataset exports."""
        stmt = (
            select(CleanedJob)
            .join(AIClassifiedJob, AIClassifiedJob.cleaned_job_id == CleanedJob.id)
            .join(RelevanceJob, RelevanceJob.ai_classified_job_id == AIClassifiedJob.id)
            .options(
                selectinload(CleanedJob.ai_classified_job).selectinload(
                    AIClassifiedJob.relevance_job
                )
            )
        )
        results = (await session.execute(stmt)).scalars().all()

        records = []
        for job in results:
            class_info = job.ai_classified_job
            rel_info = class_info.relevance_job if class_info else None
            records.append(
                {
                    "job_id": job.id,
                    "company": job.company,
                    "title": job.title,
                    "clean_description": job.clean_description,
                    "location": job.location,
                    "employment_type": job.employment_type,
                    "experience": job.experience,
                    "salary": job.salary,
                    "skills": job.skills,
                    "benefits": job.benefits,
                    "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                    "scraped_date": job.cleaned_date.isoformat(),
                    "normalized_title": job.normalized_title,
                    "ai_label": class_info.ai_label if class_info else None,
                    "confidence": class_info.confidence if class_info else None,
                    "relevance_score": rel_info.relevance_score if rel_info else None,
                    "rank": rel_info.rank if rel_info else None,
                }
            )
        return records

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Fetch user profile by email address."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
        """Fetch user profile by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_user(session: AsyncSession, email: str, hashed_password: str, role: str = "user") -> User:
        """Create and save a new user."""
        user = User(email=email, hashed_password=hashed_password, role=role)
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def get_company_by_name(session: AsyncSession, name: str) -> Optional[Company]:
        """Fetch enriched company details by name."""
        stmt = select(Company).where(Company.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_company(session: AsyncSession, company_data: Dict[str, Any]) -> Company:
        """Create and save an enriched company profile."""
        company = Company(**company_data)
        session.add(company)
        await session.flush()
        return company

    @staticmethod
    async def get_job_versions(session: AsyncSession, job_id: str) -> List[JobVersion]:
        """Fetch the update version history of a specific job listing."""
        stmt = select(JobVersion).where(JobVersion.job_id == job_id).order_by(JobVersion.version_number)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def save_job_version(session: AsyncSession, job_id: str, version_number: int, changes_payload: str, status: str = "active") -> JobVersion:
        """Log a new version update of a job listing."""
        version = JobVersion(job_id=job_id, version_number=version_number, changes_payload=changes_payload, status=status)
        session.add(version)
        await session.flush()
        return version

    @staticmethod
    async def save_resume(session: AsyncSession, filename: str, resume_text: str, skills_extracted: Optional[str] = None, embedding_id: Optional[str] = None, user_id: Optional[str] = None) -> Resume:
        """Save a candidate's uploaded resume profile."""
        resume = Resume(filename=filename, resume_text=resume_text, skills_extracted=skills_extracted, embedding_id=embedding_id, user_id=user_id)
        session.add(resume)
        await session.flush()
        return resume

    @staticmethod
    async def get_resume_by_id(session: AsyncSession, resume_id: str) -> Optional[Resume]:
        """Fetch an uploaded resume by ID."""
        stmt = select(Resume).where(Resume.id == resume_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_skill_relation(session: AsyncSession, skill_name: str, parent_skill: Optional[str] = None, relationship_type: str = "subset") -> SkillKnowledgeGraph:
        """Add a skill relationship node to the skills taxonomy knowledge graph."""
        relation = SkillKnowledgeGraph(skill_name=skill_name, parent_skill=parent_skill, relationship_type=relationship_type)
        session.add(relation)
        await session.flush()
        return relation

    @staticmethod
    async def get_all_skills(session: AsyncSession) -> List[SkillKnowledgeGraph]:
        """Fetch all registered skill relationship nodes."""
        stmt = select(SkillKnowledgeGraph)
        result = await session.execute(stmt)
        return list(result.scalars().all())
