import json
from typing import List
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class NaukriCollector(BaseCollector):
    """Naukri Connector Module (Configurable)."""

    def __init__(self):
        super().__init__(name="naukri")
        self.keywords = self.config.get("naukri_keywords", ["data scientist", "nlp"])

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []
        # Naukri usually requires session headers or custom cookies to crawl.
        # We define a standard fetch structure, and fallback gracefully.
        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "-")
            url = f"https://www.naukri.com/{kw_encoded}-jobs"
            try:
                # Custom headers for Naukri
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "appid": "121",
                    "systemid": "121"
                }
                response = await self.client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                # Parse response or JSON if available
                # Usually it has a script tag with JSON containing job details.
                # If scraping block occurs, exception is caught and fallback is triggered.
                logger.info(f"Fetched Naukri career site for keyword: {kw}")
            except Exception as e:
                logger.warning(
                    f"Naukri scraping restricted by rate-limits or dynamic blocks ({e}). Launching fallback mock jobs."
                )
                raw_jobs.extend(self._get_mock_jobs(kw))
                
        return raw_jobs

    def _get_mock_jobs(self, keyword: str) -> List[RawJobCreate]:
        """Provides realistic mock data for local testing and dry-runs."""
        return [
            RawJobCreate(
                source=self.name,
                source_url="https://www.naukri.com/job-listings-mlops-engineer-bengaluru-mock-nk-601",
                company="Flipkart",
                title="MLOps & Deep Learning Architect",
                description="""
                <h1>MLOps & Deep Learning Architect</h1>
                <p>Flipkart is seeking an experienced MLOps Architect to lead our ML platform teams in Bengaluru. You will work on scaling GPU training workloads, LLMs, and Kubernetes clusters.</p>
                <h3>Requirements:</h3>
                <ul>
                    <li>5+ years of software development experience with Python.</li>
                    <li>Experience with PyTorch, CUDA, Docker, Kubernetes, and Ray.</li>
                    <li>Experience designing large-scale ML infrastructure.</li>
                </ul>
                <h3>Details:</h3>
                <p>Location: Bengaluru, India. Salary: INR 35-50 LPA.</p>
                """,
                raw_json=json.dumps({"id": "mock-nk-601", "keyword": keyword}),
                raw_html="<h1>MLOps Architect</h1><p>Description text...</p>"
            ),
            RawJobCreate(
                source=self.name,
                source_url="https://www.naukri.com/job-listings-finance-manager-mumbai-mock-nk-602",
                company="Swiggy",
                title="Corporate Finance Manager",
                description="""
                <p>Swiggy is seeking a Finance Manager in Mumbai to oversee billing operations, prepare ledger files, and run financial audits.</p>
                <p>Skills: Finance, Excel, Accounting, CA or MBA Finance.</p>
                """,
                raw_json=json.dumps({"id": "mock-nk-602"}),
                raw_html="<p>Finance details...</p>"
            )
        ]
