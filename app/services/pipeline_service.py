import asyncio
import datetime
import uuid
from typing import List

from app.collectors import (
    GreenhouseCollector,
    LeverCollector,
    AshbyCollector,
    LinkedInCollector,
    IndeedCollector,
    NaukriCollector,
    CompanySiteCollector,
)
from app.database.connection import AsyncSessionLocal
from app.database.repository import JobRepository
from app.models.database import PipelineLog
from app.models.schemas import RawJobCreate
from app.services.worker import IngestionWorker
from app.services.progress_manager import ProgressManager
from app.utils.logger import logger


class PipelineService:
    """Orchestrator executing the complete multi-layer Job Ingestion & Filtering Pipeline."""

    def __init__(self):
        self.worker = IngestionWorker()

    async def run_ingestion(self, role: str = "AI Engineer", page: int = 1, complete: bool = True) -> str:
        """Runs the ingestion cycle end-to-end and returns the run_id."""
        run_id = str(uuid.uuid4())
        started_at = datetime.datetime.now(datetime.UTC)
        
        logger.info(f"Starting Job Ingestion Pipeline (Batch {page}) for role '{role}'. Run ID: {run_id}")
        ProgressManager.start_pipeline(role)
        
        try:
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

            # Set keywords and page for each collector
            for coll in collectors:
                if hasattr(coll, "keywords"):
                    coll.keywords = [role]
                if hasattr(coll, "set_page"):
                    coll.set_page(page)

            # 2. Fetch raw job posts in parallel, tracking progress
            async def run_collector(coll):
                ProgressManager.update_collector(coll.name, "scraping")
                try:
                    res = await coll.collect()
                    count = len(res) if res else 0
                    ProgressManager.update_collector(coll.name, "completed", count)
                    return res or []
                except Exception as e:
                    logger.error(f"Collector {coll.name} failed: {e}")
                    ProgressManager.update_collector(coll.name, "failed", 0)
                    return []

            logger.info("Triggering data collection tasks in parallel...")
            collect_results = await asyncio.gather(
                *[run_collector(coll) for coll in collectors],
                return_exceptions=True
            )

            # Merge raw jobs and close collectors
            all_raw_jobs: List[RawJobCreate] = []
            for idx, res in enumerate(collect_results):
                coll = collectors[idx]
                await coll.close()
                if isinstance(res, Exception):
                    logger.error(f"Collector {coll.name} encountered error: {res}")
                elif res:
                    all_raw_jobs.extend(res)

            logger.info(f"Collection completed. Total raw job listings gathered: {len(all_raw_jobs)}")
            ProgressManager.start_processing(len(all_raw_jobs))

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
                        raw_job_id = None
                        async with AsyncSessionLocal() as session:
                            async with session.begin():
                                # 3. Check for exact URL duplicate in database to avoid reprocessing
                                existing_raw = await JobRepository.get_raw_job_by_url(session, raw_job_in.source_url)
                                if existing_raw:
                                    logger.debug(f"Skipping already scraped URL: {raw_job_in.source_url}")
                                    ProgressManager.increment_processed(is_cleaned=False)
                                    continue

                                # Save to raw_jobs table
                                raw_job = await JobRepository.save_raw_job(session, raw_job_in)
                                raw_job_id = raw_job.id

                        if raw_job_id:
                            # Process raw job using worker logic
                            success = await self.worker.process_raw_job(raw_job_id)
                            ProgressManager.increment_processed(is_cleaned=success)
                            if success:
                                cleaned_count += 1
                                classified_count += 1
                                accepted_count += 1
                            else:
                                rejected_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing raw job: {raw_job_in.title}. Error: {e}", exc_info=True)
                        ProgressManager.increment_processed(is_cleaned=False)
                        continue

                # Update PipelineLog status with completed run statistics
                updates = {
                    "jobs_cleaned": cleaned_count,
                    "jobs_rejected": rejected_count,
                    "jobs_classified": classified_count,
                    "jobs_accepted": accepted_count,
                    "status": "success"
                }
                
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        await JobRepository.update_pipeline_log(session, run_id, updates)

            logger.info(
                f"Pipeline run {run_id} completed successfully. "
                f"Ingested: {cleaned_count}, Rejected: {rejected_count}, AI Classified: {classified_count}, Accepted: {accepted_count}"
            )
            if complete:
                ProgressManager.complete_pipeline()
            return run_id
            
        except Exception as e:
            logger.error(f"Pipeline run {run_id} encountered critical error: {e}", exc_info=True)
            ProgressManager.fail_pipeline(str(e))
            raise e
