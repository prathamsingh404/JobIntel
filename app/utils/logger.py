import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config.settings import BASE_DIR, settings

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

def setup_logger(name: str = "job_pipeline") -> logging.Logger:
    """Configures and returns a logger with console and file handlers."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already setup
    if logger.hasHandlers():
        return logger

    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Formatter for structured logs
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file logger at {LOG_FILE}: {e}")

    return logger

# Global pipeline logger
logger = setup_logger()
