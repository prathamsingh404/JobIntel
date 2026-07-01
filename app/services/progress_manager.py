import datetime
from typing import Dict, Any, Optional

class ProgressManager:
    """Manages global real-time scraping and processing progress states for JobIntel V2."""
    
    # Global state dictionary
    _state = {
        "current_role": "",
        "is_running": False,
        "started_at": None,
        "batch_number": 0,
        "collectors": {},  # e.g., {"greenhouse": {"status": "pending", "count": 0, "total": 0}, ...}
        "processing_total": 0,
        "processing_current": 0,
        "processed_cleaned": 0,
        "processed_rejected": 0,
        "completed_at": None,
        "error_message": None
    }

    @classmethod
    def get_progress(cls) -> Dict[str, Any]:
        """Returns a snapshot of the current ingestion progress."""
        state_copy = cls._state.copy()
        # Deep copy collectors dict
        state_copy["collectors"] = {k: v.copy() for k, v in cls._state["collectors"].items()}
        if state_copy["started_at"] and isinstance(state_copy["started_at"], datetime.datetime):
            state_copy["started_at"] = state_copy["started_at"].isoformat()
        if state_copy["completed_at"] and isinstance(state_copy["completed_at"], datetime.datetime):
            state_copy["completed_at"] = state_copy["completed_at"].isoformat()
        return state_copy

    @classmethod
    def start_pipeline(cls, role: str):
        """Initializes or continues the progress state for an ingestion run.
        
        On the FIRST call (batch_number == 0 or role changed), resets everything.
        On subsequent calls (same role, pipeline running), accumulates counts.
        """
        is_continuation = (
            cls._state["is_running"] 
            and cls._state["current_role"] == role 
            and cls._state["batch_number"] > 0
        )
        
        if is_continuation:
            # Accumulating mode — keep totals, just reset per-batch collector status to "pending"
            cls._state["batch_number"] += 1
            for name in cls._state["collectors"]:
                cls._state["collectors"][name]["status"] = "pending"
                # Keep "total" (cumulative) but reset per-batch "count"
                cls._state["collectors"][name]["count"] = 0
        else:
            # Fresh start
            cls._state.update({
                "current_role": role,
                "is_running": True,
                "started_at": datetime.datetime.now(datetime.UTC),
                "batch_number": 1,
                "collectors": {
                    "greenhouse": {"status": "pending", "count": 0, "total": 0},
                    "lever": {"status": "pending", "count": 0, "total": 0},
                    "ashby": {"status": "pending", "count": 0, "total": 0},
                    "linkedin": {"status": "pending", "count": 0, "total": 0},
                    "indeed": {"status": "pending", "count": 0, "total": 0},
                    "naukri": {"status": "pending", "count": 0, "total": 0},
                    "company_site": {"status": "pending", "count": 0, "total": 0}
                },
                "processing_total": 0,
                "processing_current": 0,
                "processed_cleaned": 0,
                "processed_rejected": 0,
                "completed_at": None,
                "error_message": None
            })

    @classmethod
    def update_collector(cls, collector_name: str, status: str, count: int = 0):
        """Updates the status and scrape count of a specific collector.
        
        Accumulates the 'total' field across batches while 'count' shows per-batch results.
        """
        if collector_name in cls._state["collectors"]:
            prev_total = cls._state["collectors"][collector_name].get("total", 0)
            cls._state["collectors"][collector_name] = {
                "status": status,  # pending, scraping, completed, failed
                "count": count,  # This batch's count
                "total": prev_total + count  # Cumulative across all batches
            }

    @classmethod
    def start_processing(cls, total_jobs: int):
        """Prepares state for the AI processing and filtering phase.
        
        Accumulates processing_total across batches.
        """
        cls._state["processing_total"] += total_jobs
        # Don't reset processing_current, processed_cleaned, processed_rejected — they accumulate

    @classmethod
    def increment_processed(cls, is_cleaned: bool):
        """Increments the processing count and tracks cleaned vs rejected outcomes."""
        cls._state["processing_current"] += 1
        if is_cleaned:
            cls._state["processed_cleaned"] += 1
        else:
            cls._state["processed_rejected"] += 1

    @classmethod
    def complete_pipeline(cls):
        """Marks the current run as finished."""
        cls._state.update({
            "is_running": False,
            "completed_at": datetime.datetime.now(datetime.UTC)
        })

    @classmethod
    def fail_pipeline(cls, error_msg: str):
        """Marks the current run as failed with an error description."""
        cls._state.update({
            "is_running": False,
            "completed_at": datetime.datetime.now(datetime.UTC),
            "error_message": error_msg
        })
