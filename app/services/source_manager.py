import datetime
from typing import Dict, Any, List, Optional
from app.utils.logger import logger
from app.config.settings import settings

class SourceMetadata:
    def __init__(self, name: str, enabled: bool = True, interval_minutes: int = 60):
        self.name = name
        self.enabled = enabled
        self.interval_minutes = interval_minutes
        self.last_run: Optional[datetime.datetime] = None
        self.last_success: Optional[datetime.datetime] = None
        self.success_count = 0
        self.failure_count = 0
        self.jobs_collected_total = 0
        self.last_failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "jobs_collected_total": self.jobs_collected_total,
            "last_failure_reason": self.last_failure_reason,
            "health_score": self.get_health_score()
        }

    def get_health_score(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 100.0
        return round((self.success_count / total) * 100.0, 1)


class SourceManager:
    """Central registry and controller for multi-source scraping collectors in JobIntel V2."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SourceManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self) -> None:
        self.sources: Dict[str, SourceMetadata] = {}
        # Load from active collectors config
        active_collectors = settings.pipeline_config.get("collectors", {}).get("active", [
            "greenhouse", "lever", "ashby", "linkedin", "indeed", "naukri", "company_site"
        ])
        
        for name in active_collectors:
            # Register with default hourly intervals
            self.register_source(name, enabled=True, interval_minutes=60)
        logger.info(f"SourceManager initialized with registered sources: {list(self.sources.keys())}")

    def register_source(self, name: str, enabled: bool = True, interval_minutes: int = 60) -> None:
        """Registers a scraping source connector."""
        self.sources[name] = SourceMetadata(name, enabled, interval_minutes)

    def enable_source(self, name: str) -> bool:
        if name in self.sources:
            self.sources[name].enabled = True
            logger.info(f"Scraper source '{name}' enabled.")
            return True
        return False

    def disable_source(self, name: str) -> bool:
        if name in self.sources:
            self.sources[name].enabled = False
            logger.info(f"Scraper source '{name}' disabled.")
            return True
        return False

    def get_active_sources(self) -> List[SourceMetadata]:
        return [s for s in self.sources.values() if s.enabled]

    def get_all_sources(self) -> List[SourceMetadata]:
        return list(self.sources.values())

    def update_run_stats(self, name: str, success: bool, jobs_collected: int = 0, error_msg: Optional[str] = None) -> None:
        """Updates run histories and computes current health metrics."""
        if name not in self.sources:
            return
        
        meta = self.sources[name]
        meta.last_run = datetime.datetime.utcnow()
        if success:
            meta.last_success = meta.last_run
            meta.success_count += 1
            meta.jobs_collected_total += jobs_collected
            meta.last_failure_reason = None
            logger.info(f"Scraper '{name}' execution completed. Ingested {jobs_collected} jobs.")
        else:
            meta.failure_count += 1
            meta.last_failure_reason = error_msg
            logger.warning(f"Scraper '{name}' run execution failed. Reason: {error_msg}")

    def get_source_status(self, name: str) -> Optional[Dict[str, Any]]:
        if name in self.sources:
            return self.sources[name].to_dict()
        return None
