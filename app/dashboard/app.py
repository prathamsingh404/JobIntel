import os
from pathlib import Path
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db, init_db
from app.database.repository import JobRepository
from app.services.pipeline_service import PipelineService
from app.services.export_service import ExportService
from app.utils.logger import logger

app = FastAPI(
    title="AI Job Discovery Ingestion Platform",
    description="Real-time ingestion, cleaning, deduplication, AI classification & Relevance scoring.",
    version="1.0.0"
)

# Setup path for index.html
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initializes the database schema on server startup."""
    logger.info("Starting up FastAPI application. Preparing database...")
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the single page dashboard web interface."""
    index_html_path = TEMPLATE_DIR / "index.html"
    if not index_html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard index.html not found.")
    
    with open(index_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """API endpoint returning pipeline summary metrics and aggregates."""
    try:
        stats = await JobRepository.get_dashboard_stats(db)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/jobs")
async def get_jobs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """API endpoint returning lists of processed, AI-classified, and scored jobs."""
    try:
        jobs = await JobRepository.get_recent_jobs(db, limit=limit)
        return JSONResponse(content=jobs)
    except Exception as e:
        logger.error(f"Error fetching recent jobs: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Background runner lock to prevent concurrent triggers
running_locks = {}

async def _bg_run_pipeline():
    running_locks["ingestion"] = True
    try:
        pipe = PipelineService()
        await pipe.run_ingestion()
    except Exception as e:
        logger.error(f"Background pipeline run failed: {e}", exc_info=True)
    finally:
        running_locks["ingestion"] = False

@app.post("/api/trigger")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """Triggers the job scraper & processing pipeline in a background task."""
    if running_locks.get("ingestion", False):
        return JSONResponse(status_code=409, content={"status": "error", "message": "Pipeline is already running."})
        
    background_tasks.add_task(_bg_run_pipeline)
    return {"status": "accepted", "message": "Ingestion pipeline triggered in the background."}

@app.post("/api/export")
async def trigger_export():
    """Compiles SQLite, DuckDB, Parquet, and CSV datasets in exports directory."""
    try:
        exporter = ExportService()
        paths = await exporter.export_all()
        return {"status": "success", "message": "ML datasets generated.", "exports": paths}
    except Exception as e:
        logger.error(f"Export execution failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
