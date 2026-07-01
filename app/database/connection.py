from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config.settings import settings
from app.models.database import Base
from app.utils.logger import logger

# Configure async engine options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings to handle concurrency issues
    connect_args["check_same_thread"] = False

engine_args = {
    "connect_args": connect_args,
    "echo": False,
    "pool_pre_ping": True,
}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db() -> None:
    """Creates all database tables defined in SQLAlchemy models."""
    try:
        async with engine.begin() as conn:
            from app.models.database import (
                User, Company, RawJob, CleanedJob, JobVersion,
                RejectedJob, AIClassifiedJob, RelevanceJob, PipelineLog,
                Resume, SkillKnowledgeGraph
            )
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
