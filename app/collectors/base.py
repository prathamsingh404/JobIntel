import abc
import asyncio
from typing import Any, Dict, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config.settings import settings
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class BaseCollector(abc.ABC):
    """Abstract base class for all job collectors."""

    def __init__(self, name: str):
        self.name = name
        self.config = settings.pipeline_config.get("collectors", {})
        self.rate_limit_delay = self.config.get("rate_limit_delay_seconds", 1.0)
        self.max_retries = self.config.get("max_retries", 3)
        self.backoff_factor = self.config.get("backoff_factor", 2.0)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI Job Pipeline/1.0"}
        )

    @abc.abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch raw listings or items from the source (returns raw dicts/html/json)."""
        pass

    def parse(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw HTML/JSON response record into a structured job dictionary."""
        return raw_record

    def validate(self, parsed_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate required fields of the parsed job object. Returns (is_valid, reason)."""
        title = parsed_data.get("title")
        company = parsed_data.get("company")
        description = parsed_data.get("description")
        source_url = parsed_data.get("source_url")

        if not title:
            return False, "Missing title"
        if not company:
            return False, "Missing company"
        if not description or not description.strip():
            return False, "Empty description"
        if not source_url:
            return False, "Missing source URL"
        return True, None

    def normalize(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job titles, locations, and other text fields into standard form."""
        normalized = parsed_data.copy()
        if "title" in normalized and normalized["title"]:
            normalized["title"] = " ".join(normalized["title"].split())
        if "company" in normalized and normalized["company"]:
            normalized["company"] = " ".join(normalized["company"].split())
        
        location = normalized.get("location", "Remote")
        if not location or "remote" in location.lower():
            normalized["location"] = "Remote"
        else:
            normalized["location"] = location.strip()
            
        return normalized

    async def publish(self, normalized_data: Dict[str, Any]) -> None:
        """Publishes the job record to a queue or log broker."""
        logger.debug(f"Publishing parsed job record: {normalized_data.get('title')} at {normalized_data.get('company')}")

    async def close(self) -> None:
        """Close connection pools."""
        await self.client.aclose()

    async def _rate_limit(self) -> None:
        """Enforces a rate-limiting delay between requests."""
        if self.rate_limit_delay > 0:
            await asyncio.sleep(self.rate_limit_delay)

    async def get_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Fetch url using HTTP GET with exponential backoff retry logic."""
        
        # Define retry wrapper dynamically to leverage instance variables
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.backoff_factor, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
            reraise=True
        )
        async def _fetch():
            await self._rate_limit()
            logger.debug(f"Fetching: {url} (params: {params})")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response

        try:
            return await _fetch()
        except Exception as e:
            logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
            raise
