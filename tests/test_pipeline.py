import asyncio
import pytest
from unittest.mock import patch
from sqlalchemy import select
import httpx

from app.config.settings import settings
from app.database.connection import AsyncSessionLocal, init_db, engine
from app.services.pipeline_service import PipelineService
from app.models.database import RawJob, CleanedJob, RejectedJob, AIClassifiedJob, RelevanceJob

@pytest.mark.asyncio
async def test_pipeline_e2e():
    # 1. Override database to a separate temporary SQLite file for testing
    settings.DATABASE_URL = "sqlite+aiosqlite:///test_pipeline.db"
    
    # Force Mock AI Provider for test runs
    settings.AI_PROVIDER = "mock"
    
    # 2. Init tables
    await init_db()
    
    # 3. Patch network clients to immediately trigger local mock data fallbacks
    with patch("httpx.AsyncClient.get", side_effect=httpx.HTTPError("Mocked network error")), \
         patch("playwright.async_api.async_playwright", side_effect=Exception("Mocked browser error")):
         
        # 4. Instantiate and run pipeline
        pipeline = PipelineService()
        run_id = await pipeline.run_ingestion()
        
        # Check that run_id is returned
        assert run_id is not None
        
        # 5. Connect to database and verify results
        async with AsyncSessionLocal() as session:
            # Check raw jobs were stored
            raw_count = (await session.execute(select(RawJob))).scalars().all()
            assert len(raw_count) > 0
            
            # Check cleaned jobs were created
            cleaned_jobs = (await session.execute(select(CleanedJob))).scalars().all()
            assert len(cleaned_jobs) > 0
            
            # Check that AI classification and relevance scoring tables are populated
            classified_jobs = (await session.execute(select(AIClassifiedJob))).scalars().all()
            assert len(classified_jobs) > 0
            
            relevance_jobs = (await session.execute(select(RelevanceJob))).scalars().all()
            assert len(relevance_jobs) > 0
            
            # Ensure rejected jobs exist
            rejected_jobs = (await session.execute(select(RejectedJob))).scalars().all()
            assert len(rejected_jobs) > 0

    # Clean up test database connection pool
    await engine.dispose()
