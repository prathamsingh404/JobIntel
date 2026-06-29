import asyncio
import datetime
import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.collectors import (
    GreenhouseCollector,
    LeverCollector,
    AshbyCollector,
    LinkedInCollector,
    IndeedCollector,
    NaukriCollector,
    CompanySiteCollector,
)
from app.cleaner.pipeline import JobCleaner
from app.normalizer.title_normalizer import TitleNormalizer
from app.deduplicator.detector import DuplicateDetector
from app.rule_engine.evaluator import RuleEvaluator
from app.classifier import get_classifier
from app.relevance.scorer import RelevanceScorer

from app.database.connection import AsyncSessionLocal
from app.database.repository import JobRepository
from app.models.database import PipelineLog, CleanedJob
from app.models.schemas import (
    RawJobCreate,
    CleanedJobCreate,
    RejectedJobCreate,
    AIClassifiedJobCreate,
    RelevanceJobCreate,
)
from app.utils.logger import logger

class PipelineService:
    """Orchestrator executing the complete multi-layer Job Ingestion & Filtering Pipeline."""

    def __init__(self):
        self.cleaner = JobCleaner()
        self.normalizer = TitleNormalizer()
        self.deduplicator = DuplicateDetector()
        self.rule_engine = RuleEvaluator()
        self.classifier = get_classifier()
        self.relevance_scorer = RelevanceScorer()

    async def run_ingestion(self) -> str:
        """Runs the ingestion cycle end-to-end and returns the run_id."""
        run_id = str(uuid.uuid4())
        started_at = datetime.datetime.utcnow()
        
        logger.info(f"Starting Job Ingestion Pipeline. Run ID: {run_id}")
        
        # 1. Instantiate collectors
        collectors = [
            GreenhouseCollector(),
            LeverCollector(),
            AshbyCollector(),
            LinkedInCollector(),
            IndeedCollector(),
            NaukriCollector(),
            CompanySiteCollector(),
        ]

        # 2. Fetch raw job posts in parallel
        logger.info("Triggering data collection tasks in parallel...")
        collect_results = await asyncio.gather(
            *[coll.collect() for coll in collectors],
            return_exceptions=True
        )

        # Merge raw jobs and close collectors
        all_raw_jobs: List[RawJobCreate] = []
        for idx, res in enumerate(collect_results):
            coll = collectors[idx]
            await coll.close()
            if isinstance(res, Exception):
                logger.error(f"Collector {coll.name} failed during collection: {res}")
            elif res:
                all_raw_jobs.extend(res)

        logger.info(f"Collection completed. Total raw job listings gathered: {len(all_raw_jobs)}")

        # Initialize pipeline execution log
        log_record = PipelineLog(
            run_id=run_id,
            started_at=started_at,
            jobs_scraped=len(all_raw_jobs),
            status="running"
        )

        async with AsyncSessionLocal() as session:
            async with session.begin():
                await JobRepository.create_pipeline_log(session, log_record)

            # Keep track of counts for summary log updates
            cleaned_count = 0
            rejected_count = 0
            classified_count = 0
            accepted_count = 0

            # Process jobs sequentially or in batches to optimize transactions
            for raw_job_in in all_raw_jobs:
                try:
                    async with session.begin_nested():
                        # 3. Check for exact URL duplicate in database to avoid reprocessing
                        existing_raw = await JobRepository.get_raw_job_by_url(session, raw_job_in.source_url)
                        if existing_raw:
                            logger.debug(f"Skipping already scraped URL: {raw_job_in.source_url}")
                            continue

                        # Save to raw_jobs table
                        raw_job = await JobRepository.save_raw_job(session, raw_job_in)

                        # 4. Clean Raw HTML and Description
                        cleaned_desc = self.cleaner.clean(raw_job.description)
                        cleaned_title = self.cleaner.clean(raw_job.title)
                        
                        # Validate description language
                        if not self.cleaner.is_english(cleaned_desc):
                            # Save language-rejection record
                            await JobRepository.save_rejected_job(
                                session,
                                RejectedJobCreate(
                                    raw_job_id=raw_job.id,
                                    source=raw_job.source,
                                    company=raw_job.company,
                                    title=raw_job.title,
                                    reason="Language Filter: Non-English description text detected."
                                )
                            )
                            rejected_count += 1
                            continue

                        # 5. Normalize Title
                        normalized_title = self.normalizer.normalize(cleaned_title)

                        # 6. Deduplication Check (compare vs same company/title to optimize database index scans)
                        stmt = select(CleanedJob).where(CleanedJob.company == raw_job.company)
                        res = await session.execute(stmt)
                        existing_company_jobs = res.scalars().all()

                        is_dup, dup_reason = self.deduplicator.is_duplicate(
                            cleaned_title,
                            raw_job.company,
                            cleaned_desc,
                            existing_company_jobs
                        )

                        if is_dup:
                            await JobRepository.save_rejected_job(
                                session,
                                RejectedJobCreate(
                                    raw_job_id=raw_job.id,
                                    source=raw_job.source,
                                    company=raw_job.company,
                                    title=raw_job.title,
                                    reason=dup_reason
                                )
                            )
                            rejected_count += 1
                            continue

                        # Save unique listing to cleaned_jobs
                        cleaned_job = await JobRepository.save_cleaned_job(
                            session,
                            CleanedJobCreate(
                                raw_job_id=raw_job.id,
                                title=cleaned_title,
                                normalized_title=normalized_title,
                                company=raw_job.company,
                                location="Remote" if "remote" in raw_job.title.lower() or "remote" in cleaned_desc.lower() else "USA",
                                clean_description=cleaned_desc,
                                language="en"
                            )
                        )
                        cleaned_count += 1

                        # 7. Rule Engine Filtering
                        rule_passed, rule_score, rule_reason = self.rule_engine.evaluate(
                            cleaned_title, cleaned_desc
                        )

                        if not rule_passed:
                            await JobRepository.save_rejected_job(
                                session,
                                RejectedJobCreate(
                                    raw_job_id=raw_job.id,
                                    source=raw_job.source,
                                    company=raw_job.company,
                                    title=cleaned_title,
                                    reason=f"Failed rule engine keywords. {rule_reason}"
                                )
                            )
                            rejected_count += 1
                            continue

                        # 8. AI Role Classification (Gemini / Mock)
                        ai_res = await self.classifier.classify(
                            cleaned_title, cleaned_desc, raw_job.company
                        )
                        classified_job = await JobRepository.save_ai_classified_job(
                            session,
                            AIClassifiedJobCreate(
                                cleaned_job_id=cleaned_job.id,
                                ai_label=ai_res.ai_label,
                                confidence=ai_res.confidence,
                                reason=ai_res.reason,
                                evidence=ai_res.evidence,
                                decision=ai_res.decision
                            )
                        )
                        classified_count += 1

                        if ai_res.decision == "reject":
                            await JobRepository.save_rejected_job(
                                session,
                                RejectedJobCreate(
                                    raw_job_id=raw_job.id,
                                    source=raw_job.source,
                                    company=raw_job.company,
                                    title=cleaned_title,
                                    reason=f"AI rejected role label: {ai_res.ai_label}. Reason: {ai_res.reason}"
                                )
                            )
                            rejected_count += 1
                            continue

                        # 9. Relevance Scoring & Candidate Profile Alignment
                        rel_score, rank, match_details = self.relevance_scorer.calculate_score(cleaned_job)
                        
                        await JobRepository.save_relevance_job(
                            session,
                            RelevanceJobCreate(
                                ai_classified_job_id=classified_job.id,
                                relevance_score=rel_score,
                                rank=rank,
                                match_details=match_details
                            )
                        )
                        accepted_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing raw job: {raw_job_in.title}. Error: {e}", exc_info=True)
                    # Safe rollback of this inner transaction block to preserve DB integrity
                    continue

            # Update PipelineLog status with completed run statistics
            updates = {
                "jobs_cleaned": cleaned_count,
                "jobs_rejected": rejected_count,
                "jobs_classified": classified_count,
                "jobs_accepted": accepted_count,
                "status": "success"
            }
            
            await JobRepository.update_pipeline_log(session, run_id, updates)
            await session.commit()

        logger.info(
            f"Pipeline run {run_id} completed successfully. "
            f"Ingested: {cleaned_count}, Rejected: {rejected_count}, AI Classified: {classified_count}, Accepted: {accepted_count}"
        )
        return run_id
