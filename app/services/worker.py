import asyncio
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.database.repository import JobRepository
from app.models.database import RawJob, CleanedJob, AIClassifiedJob, RelevanceJob
from app.models.schemas import RawJobCreate, CleanedJobCreate, RejectedJobCreate, AIClassifiedJobCreate, RelevanceJobCreate
from app.cleaner.pipeline import JobCleaner
from app.normalizer.title_normalizer import TitleNormalizer
from app.deduplicator.detector import DuplicateDetector
from app.rule_engine.evaluator import RuleEvaluator
from app.classifier import get_classifier
from app.relevance.scorer import RelevanceScorer
from app.services.parser_service import JobParserService
from app.services.enrichment_service import EnrichmentService
from app.utils.logger import logger

class IngestionWorker:
    """Worker service executing separate ingestion and pipeline tasks for JobIntel V2."""

    def __init__(self):
        self.cleaner = JobCleaner()
        self.normalizer = TitleNormalizer()
        self.deduplicator = DuplicateDetector()
        self.rule_engine = RuleEvaluator()
        self.classifier = get_classifier()
        self.relevance_scorer = RelevanceScorer()

    async def process_raw_job(self, raw_job_id: str) -> bool:
        """Processes a single raw job post through all V2 pipeline stages."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # 1. Fetch raw job record
                stmt = select(RawJob).where(RawJob.id == raw_job_id)
                res = await session.execute(stmt)
                raw_job = res.scalar_one_or_none()
                if not raw_job:
                    logger.error(f"Worker process failed: Raw job {raw_job_id} not found in DB.")
                    return False

                # 2. Parse raw fields
                parsed = JobParserService.parse_raw_job(raw_job)
                
                # 3. Validate job payload
                is_valid, err_reason = JobParserService.validate(parsed)
                if not is_valid:
                    await JobRepository.save_rejected_job(
                        session,
                        RejectedJobCreate(
                            raw_job_id=raw_job.id,
                            source=raw_job.source,
                            company=raw_job.company,
                            title=raw_job.title,
                            reason=err_reason
                        )
                    )
                    return False

                # 4. Clean HTML and Text formatting
                cleaned_desc = self.cleaner.clean(parsed["description"])
                cleaned_title = self.cleaner.clean(parsed["title"])

                # Language filtering
                if not self.cleaner.is_english(cleaned_desc):
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
                    return False

                # 5. Normalize title
                normalized_title = self.normalizer.normalize(cleaned_title)

                # 6. Deduplication Check (compare vs same company jobs)
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
                    return False

                # 7. Check for Job Version Updates (Compare description changes with existing active versions)
                existing_cleaned = next((j for j in existing_company_jobs if j.title == cleaned_title), None)
                if existing_cleaned:
                    # Compare description hashes or similarity
                    if existing_cleaned.clean_description != cleaned_desc:
                        # Log a new version update
                        stmt = select(CleanedJob).where(CleanedJob.id == existing_cleaned.id)
                        # Fetch job versions to increment number
                        versions = await JobRepository.get_job_versions(session, existing_cleaned.id)
                        new_version_num = len(versions) + 1
                        
                        # Save version log
                        await JobRepository.save_job_version(
                            session,
                            job_id=existing_cleaned.id,
                            version_number=new_version_num,
                            changes_payload=f"Description updated. Length changed from {len(existing_cleaned.clean_description)} to {len(cleaned_desc)} characters.",
                            status="updated"
                        )
                        # Update current cleaned job description
                        existing_cleaned.clean_description = cleaned_desc
                        existing_cleaned.cleaned_date = datetime.datetime.utcnow()
                        # Re-enrich metadata on updated description
                        EnrichmentService.enrich_job_metadata(existing_cleaned)
                        session.add(existing_cleaned)
                        logger.info(f"Logged Job Version update for job: '{cleaned_title}' at {raw_job.company} (Version {new_version_num})")
                        # Proceed with relevance and classification update on the existing record
                        cleaned_job = existing_cleaned
                    else:
                        logger.debug(f"Skipping identical job listing: '{cleaned_title}' at {raw_job.company}")
                        return False
                else:
                    # Save new unique CleanedJob record
                    cleaned_job = await JobRepository.save_cleaned_job(
                        session,
                        CleanedJobCreate(
                            raw_job_id=raw_job.id,
                            title=cleaned_title,
                            normalized_title=normalized_title,
                            company=raw_job.company,
                            location=parsed.get("location") or "Remote",
                            clean_description=cleaned_desc,
                            language="en"
                        )
                    )
                    # Enrich properties
                    cleaned_job.workplace_type = parsed["workplace_type"]
                    cleaned_job.seniority = parsed["seniority"]
                    cleaned_job.salary_currency = parsed["salary_currency"]
                    cleaned_job.recruiter_name = parsed["recruiter_name"]
                    cleaned_job.recruiter_contact = parsed["recruiter_contact"]

                    # Enrich and link company profile
                    company = await EnrichmentService.enrich_company(session, raw_job.company)
                    cleaned_job.company_id = company.id

                    # Enrich extra job metadata
                    EnrichmentService.enrich_job_metadata(cleaned_job)

                    session.add(cleaned_job)

                # 8. Rule Engine filtering
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
                    return False

                # 9. AI Role Classification (Gemini API)
                ai_res = await self.classifier.classify(
                    cleaned_title, cleaned_desc, raw_job.company
                )
                
                # Fetch or create AI classified job record
                stmt_class = select(AIClassifiedJob).where(AIClassifiedJob.cleaned_job_id == cleaned_job.id)
                res_class = await session.execute(stmt_class)
                classified_job = res_class.scalar_one_or_none()
                if classified_job:
                    classified_job.ai_label = ai_res.ai_label
                    classified_job.confidence = ai_res.confidence
                    classified_job.reason = ai_res.reason
                    classified_job.evidence = ai_res.evidence
                    classified_job.decision = ai_res.decision
                else:
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
                    return False

                # 10. Relevance scoring
                rel_score, rank, match_details = self.relevance_scorer.calculate_score(cleaned_job)
                
                stmt_rel = select(RelevanceJob).where(RelevanceJob.ai_classified_job_id == classified_job.id)
                res_rel = await session.execute(stmt_rel)
                relevance_job = res_rel.scalar_one_or_none()
                if relevance_job:
                    relevance_job.relevance_score = rel_score
                    relevance_job.rank = rank
                    relevance_job.match_details = match_details
                else:
                    await JobRepository.save_relevance_job(
                        session,
                        RelevanceJobCreate(
                            ai_classified_job_id=classified_job.id,
                            relevance_score=rel_score,
                            rank=rank,
                            match_details=match_details
                        )
                    )
                
                return True

class AsyncQueueWorker:
    """Lightweight in-memory task runner loop for executing backend workers locally."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.ingestion_worker = IngestionWorker()
        self.active = False
        self._worker_task = None

    async def start(self) -> None:
        if self.active:
            return
        self.active = True
        self._worker_task = asyncio.create_task(self._loop())
        logger.info("Local background Queue Worker started.")

    async def stop(self) -> None:
        self.active = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Local background Queue Worker stopped.")

    async def enqueue_job(self, raw_job_id: str) -> None:
        await self.queue.put(raw_job_id)
        logger.debug(f"Raw job enqueued for processing: {raw_job_id}")

    async def _loop(self) -> None:
        while self.active:
            try:
                raw_job_id = await self.queue.get()
                logger.debug(f"Worker dequeued job: {raw_job_id}")
                try:
                    await self.ingestion_worker.process_raw_job(raw_job_id)
                except Exception as e:
                    logger.error(f"Worker failed processing job {raw_job_id}: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Exception in worker task loop: {e}", exc_info=True)
                await asyncio.sleep(1)

# Global queue instance
queue_worker = AsyncQueueWorker()
