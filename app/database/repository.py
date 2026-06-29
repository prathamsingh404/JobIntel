import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    RawJob,
    CleanedJob,
    RejectedJob,
    AIClassifiedJob,
    RelevanceJob,
    PipelineLog
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
    async def get_recent_jobs(session: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch processed jobs join query for exploration in dashboard."""
        stmt = (
            select(CleanedJob)
            .join(AIClassifiedJob, AIClassifiedJob.cleaned_job_id == CleanedJob.id)
            .join(RelevanceJob, RelevanceJob.ai_classified_job_id == AIClassifiedJob.id)
            .options(
                selectinload(CleanedJob.ai_classified_job).selectinload(
                    AIClassifiedJob.relevance_job
                )
            )
            .order_by(desc(CleanedJob.cleaned_date))
            .limit(limit)
        )
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
                    "scraped_date": job.cleaned_date.isoformat(),
                    "normalized_title": job.normalized_title,
                    "ai_label": class_info.ai_label if class_info else "N/A",
                    "confidence": class_info.confidence if class_info else 0.0,
                    "decision": class_info.decision if class_info else "reject",
                    "relevance_score": rel_info.relevance_score if rel_info else 0,
                    "rank": rel_info.rank if rel_info else "reject",
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
