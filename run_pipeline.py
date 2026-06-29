import argparse
import asyncio
import sys
import uvicorn

from app.config.settings import settings
from app.database.connection import init_db
from app.services.pipeline_service import PipelineService
from app.services.export_service import ExportService
from app.utils.logger import logger

async def run_pipeline_action():
    """Helper to initialize the database, execute pipeline, and export datasets."""
    logger.info("Initializing Database...")
    await init_db()
    
    logger.info("Starting Ingestion Run...")
    pipe = PipelineService()
    run_id = await pipe.run_ingestion()
    
    logger.info(f"Ingestion completed. Run ID: {run_id}. Compiling dataset exports...")
    exporter = ExportService()
    paths = await exporter.export_all()
    logger.info(f"Dataset exports generated: {paths}")

async def run_export_action():
    """Helper to run the export compilation directly."""
    logger.info("Starting dataset exports compilation...")
    exporter = ExportService()
    paths = await exporter.export_all()
    logger.info(f"Dataset exports generated: {paths}")

def main():
    parser = argparse.ArgumentParser(
        description="AI Job Discovery Ingestion Platform CLI"
    )
    parser.add_argument(
        "action",
        choices=["run", "export", "server"],
        help="Action to perform: 'run' to execute ingestion pipeline, 'export' to generate dataset formats, 'server' to start uvicorn dashboard"
    )
    parser.add_argument(
        "--host",
        default=settings.HOST,
        help=f"Host address for the server (default: {settings.HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port number for the server (default: {settings.PORT})"
    )

    args = parser.parse_args()

    if args.action == "run":
        try:
            asyncio.run(run_pipeline_action())
        except KeyboardInterrupt:
            logger.info("Pipeline execution cancelled by user.")
            sys.exit(0)
            
    elif args.action == "export":
        try:
            asyncio.run(run_export_action())
        except KeyboardInterrupt:
            logger.info("Export execution cancelled.")
            sys.exit(0)
            
    elif args.action == "server":
        logger.info(f"Starting Uvicorn dashboard server on {args.host}:{args.port}...")
        uvicorn.run(
            "app.dashboard.app:app",
            host=args.host,
            port=args.port,
            log_level=settings.LOG_LEVEL.lower(),
            reload=True
        )

if __name__ == "__main__":
    main()
