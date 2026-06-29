import json
from typing import List
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class AshbyCollector(BaseCollector):
    """Ashby Job Board API Collector."""

    def __init__(self):
        super().__init__(name="ashby")
        self.companies = self.config.get("ashby_companies", ["linear"])

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []
        for company in self.companies:
            # Ashby job board endpoints typically look like:
            # POST or GET to https://api.ashbyhq.com/v1/job-board/{company_id}
            url = f"https://api.ashbyhq.com/v1/job-board/{company}"
            try:
                response = await self.get_with_retry(url)
                data = response.json()
                postings = data.get("jobs", []) or data.get("postings", [])
                
                logger.info(f"Fetched {len(postings)} jobs from Ashby postings for company: {company}")
                
                for post in postings:
                    job_id = post.get("id")
                    source_url = post.get("jobUrl") or f"https://jobs.ashbyhq.com/{company}/{job_id}"
                    
                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=source_url,
                            company=company.capitalize(),
                            title=post.get("title", "Untitled Job"),
                            description=post.get("descriptionHtml", "") or post.get("description", ""),
                            raw_json=json.dumps(post),
                            raw_html=post.get("descriptionHtml", "")
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Could not fetch live Ashby data for {company} (network/API error: {e}). Using robust fallback mock jobs."
                )
                raw_jobs.extend(self._get_mock_jobs(company))
                
        return raw_jobs

    def _get_mock_jobs(self, company: str) -> List[RawJobCreate]:
        """Provides realistic mock data for local testing and dry-runs."""
        return [
            RawJobCreate(
                source=self.name,
                source_url=f"https://jobs.ashbyhq.com/{company}/mock-301",
                company=company.capitalize(),
                title="Lead MLOps Engineer",
                description="""
                <h1>Lead MLOps Engineer</h1>
                <p>We are searching for a Lead MLOps Engineer to maintain our ML training and deployment pipelines. You will orchestrate GPU clusters and set up Kubernetes, PyTorch models, and CUDA environments.</p>
                <h3>Core Technologies:</h3>
                <ul>
                    <li>Kubernetes, Docker, Helm</li>
                    <li>Python, PyTorch, CUDA</li>
                    <li>AWS SageMaker, Terraform, MLflow</li>
                </ul>
                <h3>Responsibilities:</h3>
                <p>Build infrastructure to deploy LLMs and generative AI tools in production. Automate model evaluation and testing.</p>
                """,
                raw_json=json.dumps({"id": "mock-301", "title": "Lead MLOps Engineer", "company": company}),
                raw_html="<h1>Lead MLOps Engineer</h1><p>Description text...</p>"
            ),
            RawJobCreate(
                source=self.name,
                source_url=f"https://jobs.ashbyhq.com/{company}/mock-302",
                company=company.capitalize(),
                title="Visual Content & Graphic Designer",
                description="""
                <p>We are looking for a Graphic Designer to create visuals for our marketing campaigns. You will work on layouts, vector files, branding, and video elements.</p>
                <p>Experience: Adobe Photoshop, Illustrator, Figma, Premiere Pro.</p>
                """,
                raw_json=json.dumps({"id": "mock-302", "title": "Graphic Designer", "company": company}),
                raw_html="<p>Graphic Design role details...</p>"
            )
        ]
