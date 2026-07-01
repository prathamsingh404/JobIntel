import os
import datetime
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db, init_db
from app.database.repository import JobRepository
from app.services.pipeline_service import PipelineService
from app.services.export_service import ExportService
from app.utils.logger import logger
from app.utils.auth import AuthHandler
from app.services.resume_matcher import ResumeMatcher
from app.models.database import CleanedJob

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Job Discovery Ingestion Platform",
    description="Real-time ingestion, cleaning, deduplication, AI classification & Relevance scoring.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def get_jobs(
    limit: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    rank: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """API endpoint returning lists of processed, AI-classified, and scored jobs."""
    try:
        jobs = await JobRepository.get_recent_jobs(
            db, limit=limit, search=search, role=role, rank=rank
        )
        return JSONResponse(content=jobs)
    except Exception as e:
        logger.error(f"Error fetching recent jobs: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Background runner locks and stop signals
running_locks = {}
stop_signals = {"ingestion": False}

async def _bg_run_pipeline(role: str):
    running_locks["ingestion"] = True
    stop_signals["ingestion"] = False
    
    from app.services.progress_manager import ProgressManager
    
    try:
        pipe = PipelineService()
        page = 1
        while not stop_signals.get("ingestion", False):
            logger.info(f"--- Ingestion Pipeline loop batch {page} starting for role '{role}' ---")
            await pipe.run_ingestion(role, page=page, complete=False)
            page += 1
            
            # Check stop signal before sleeping
            if stop_signals.get("ingestion", False):
                break
                
            # Sleep 5 seconds between batches, checking stop signal every second
            for _ in range(5):
                if stop_signals.get("ingestion", False):
                    break
                await asyncio.sleep(1)
                
        logger.info("Ingestion pipeline daemon loop stopped by user signal.")
        ProgressManager.complete_pipeline()
    except Exception as e:
        logger.error(f"Background pipeline run encountered exception: {e}", exc_info=True)
        ProgressManager.fail_pipeline(str(e))
    finally:
        running_locks["ingestion"] = False

@app.post("/api/trigger")
async def trigger_pipeline(background_tasks: BackgroundTasks, data: Optional[Dict[str, Any]] = None):
    """Triggers the job scraper & processing pipeline in a background task."""
    role = "AI Engineer"
    if data and "role" in data:
        role = data["role"]
        
    if running_locks.get("ingestion", False):
        return JSONResponse(status_code=409, content={"status": "error", "message": "Pipeline is already running."})
        
    background_tasks.add_task(_bg_run_pipeline, role)
    return {"status": "accepted", "message": f"Ingestion pipeline for '{role}' triggered in the background."}

@app.post("/api/stop")
async def stop_pipeline():
    """Cancels and stops the active continuous ingestion pipeline."""
    if not running_locks.get("ingestion", False):
        return JSONResponse(status_code=400, content={"status": "error", "message": "No active pipeline running."})
        
    stop_signals["ingestion"] = True
    return {"status": "accepted", "message": "Stop signal sent to the ingestion pipeline."}

@app.get("/api/scraper/progress")
async def get_scraper_progress():
    from app.services.progress_manager import ProgressManager
    return JSONResponse(content=ProgressManager.get_progress())

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

@app.post("/api/auth/register")
async def register(data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")
    
    existing = await JobRepository.get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="User already registered.")
        
    hashed = AuthHandler.hash_password(password)
    user = await JobRepository.save_user(db, email, hashed)
    return {"status": "success", "message": "User registered.", "user_id": user.id}

@app.post("/api/auth/login")
async def login(data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")
        
    user = await JobRepository.get_user_by_email(db, email)
    if not user or not AuthHandler.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
        
    token = AuthHandler.create_jwt({"user_id": user.id, "email": user.email, "role": user.role})
    return {"token": token, "role": user.role}

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        content = await file.read()
        resume_text = content.decode("utf-8", errors="ignore")
        
        # Save resume record
        resume = await JobRepository.save_resume(db, file.filename, resume_text)
        
        # Match against all cleaned jobs in DB
        from sqlalchemy import select
        stmt = select(CleanedJob)
        res = await db.execute(stmt)
        all_jobs = res.scalars().all()
        
        if not all_jobs:
            return {
                "resume_id": resume.id,
                "matches": [],
                "message": "No job posts found in database to match against."
            }
            
        matcher = ResumeMatcher()
        matches = []
        for job in all_jobs[:20]:  # Limit to top 20 candidate matches for performance
            match_res = await matcher.match_resume_to_job(resume_text, job)
            matches.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "match_score": match_res["match_score"],
                "missing_skills": match_res["missing_skills"][:5],
                "strengths": match_res["strengths"],
                "roadmap": match_res["roadmap"][:3]
            })
            
        # Sort matches by highest match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return {
            "resume_id": resume.id,
            "filename": file.filename,
            "top_matches": matches[:5]
        }
    except Exception as e:
        logger.error(f"Error matching resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/companies")
async def list_companies(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.database import Company
    stmt = select(Company)
    res = await db.execute(stmt)
    companies = res.scalars().all()
    return [{
        "id": c.id,
        "name": c.name,
        "website": c.website,
        "industry": c.industry,
        "size_range": c.size_range,
        "headquarters": c.headquarters,
        "glassdoor_rating": c.glassdoor_rating,
        "ai_hiring_score": c.ai_hiring_score
    } for c in companies]

@app.get("/api/companies/{company_id}")
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.database import Company
    stmt = select(Company).where(Company.id == company_id)
    res = await db.execute(stmt)
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found.")
    return {
        "id": c.id,
        "name": c.name,
        "website": c.website,
        "industry": c.industry,
        "size_range": c.size_range,
        "headquarters": c.headquarters,
        "tech_stack": c.tech_stack,
        "ats_provider": c.ats_provider,
        "glassdoor_rating": c.glassdoor_rating,
        "ai_hiring_score": c.ai_hiring_score,
        "hiring_trends_summary": c.hiring_trends_summary
    }

@app.get("/api/skills")
async def get_skills_distribution(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.database import CleanedJob
    stmt = select(CleanedJob.skills)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    
    skill_counts = {}
    for row in rows:
        if row:
            for s in row.split(","):
                s_clean = s.strip()
                if s_clean:
                    skill_counts[s_clean] = skill_counts.get(s_clean, 0) + 1
                    
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "top_skills": [{"name": k, "count": v} for k, v in sorted_skills[:15]],
        "knowledge_graph": [
            {"source": "Machine Learning", "target": "Deep Learning", "type": "parent"},
            {"source": "Deep Learning", "target": "PyTorch", "type": "framework"},
            {"source": "Deep Learning", "target": "TensorFlow", "type": "framework"},
            {"source": "Generative AI", "target": "LangChain", "type": "framework"},
            {"source": "Generative AI", "target": "LlamaIndex", "type": "framework"}
        ]
    }

@app.get("/api/analytics/reports")
async def get_market_reports(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from app.models.database import CleanedJob
    
    workplace_stmt = select(CleanedJob.workplace_type, func.count(CleanedJob.id)).group_by(CleanedJob.workplace_type)
    workplace_rows = (await db.execute(workplace_stmt)).all()
    workplace_dist = {row[0] or "onsite": row[1] for row in workplace_rows}
    
    seniority_stmt = select(CleanedJob.seniority, func.count(CleanedJob.id)).group_by(CleanedJob.seniority)
    seniority_rows = (await db.execute(seniority_stmt)).all()
    seniority_dist = {row[0] or "mid": row[1] for row in seniority_rows}
    
    currency_stmt = select(CleanedJob.salary_currency, func.count(CleanedJob.id)).group_by(CleanedJob.salary_currency)
    currency_rows = (await db.execute(currency_stmt)).all()
    currency_dist = {row[0] or "USD": row[1] for row in currency_rows}
    
    return {
        "workplace_distribution": workplace_dist,
        "seniority_distribution": seniority_dist,
        "currency_distribution": currency_dist,
        "market_summary": "AI Engineering and Large Language Model roles remain the fastest growing sectors for tech recruitment."
    }

@app.websocket("/api/logs/ws")
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_text("Logs pipeline connected. Listening to active background workers...")
        log_file = Path("logs/app.log")
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[-30:]
                for line in lines:
                    await websocket.send_text(line.strip())
                    
        while True:
            await asyncio.sleep(2.0)
            await websocket.send_text(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Worker polling queues... active tasks: 0")
    except WebSocketDisconnect:
        logger.info("Logs Websocket disconnected.")
    except Exception as e:
        logger.error(f"Websocket logging failed: {e}")
