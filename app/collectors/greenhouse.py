import json
from typing import List, Optional
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

# Large curated pool of real companies using Greenhouse ATS
GREENHOUSE_COMPANIES = [
    # Tier 1 — Major tech companies
    "airbnb", "coinbase", "discord", "figma", "gitlab", "notion", "datadog",
    "cloudflare", "stripe", "vercel", "hashicorp", "twilio", "hubspot",
    "databricks", "snowflake", "airtable", "brex", "plaid", "ramp",
    "gusto", "cockroachlabs", "dbt", "fivetran", "clickup", "webflow",
    # Tier 2 — AI/ML focused
    "openai", "anthropic", "cohere", "huggingface", "scaleai", "weights-and-biases",
    "replit", "anyscale", "modular", "adept", "inflection", "mistral",
    "pinecone", "weaviate", "qdrant", "chromadb", "langchain",
    # Tier 3 — Growth-stage tech
    "retool", "linear", "cal-com", "resend", "neon", "supabase",
    "fly", "render", "railway", "planetscale", "turso", "upstash",
    "axiom", "tinybird", "motherduck", "duckdb", "polarsignals",
    # Tier 4 — Enterprise & infra
    "elastic", "grafana", "temporal", "pulumi", "spacelift", "env0",
    "launchdarkly", "split", "statsig", "eppo", "amplitude",
    "segment", "rudderstack", "hightouch", "census", "airbyte",
    # Tier 5 — Fintech & healthtech
    "deel", "rippling", "carta", "mercury", "moderntreasury", "column",
    "benchling", "tempus", "flatiron", "veracyte", "recursion",
    # Tier 6 — Security & DevTools
    "snyk", "lacework", "orca-security", "wiz", "semgrep",
    "sentry", "sourcegraph", "codeium", "tabnine", "pieces",
]

COMPANIES_PER_BATCH = 6  # How many companies to scrape per loop iteration


class GreenhouseCollector(BaseCollector):
    """Greenhouse Jobs Board API Collector — Production agent that discovers real jobs."""

    def __init__(self):
        super().__init__(name="greenhouse")
        self.keywords: List[str] = []
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        # Rotate through company pool based on current page/batch number
        total_companies = len(GREENHOUSE_COMPANIES)
        start_idx = ((self._page - 1) * COMPANIES_PER_BATCH) % total_companies
        batch_companies = []
        for i in range(COMPANIES_PER_BATCH):
            batch_companies.append(GREENHOUSE_COMPANIES[(start_idx + i) % total_companies])

        logger.info(
            f"[Greenhouse Agent] Batch {self._page}: scraping companies {batch_companies} "
            f"(keywords: {self.keywords})"
        )

        for company in batch_companies:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            try:
                response = await self.get_with_retry(url, params={"content": "true"})
                data = response.json()
                jobs_list = data.get("jobs", [])

                logger.info(f"[Greenhouse] Fetched {len(jobs_list)} jobs from {company}")

                for job in jobs_list:
                    title = job.get("title", "")

                    # Keyword filtering — only keep jobs relevant to the target role
                    if self.keywords and not self._matches_keywords(title):
                        continue

                    job_id = job.get("id")
                    source_url = (
                        job.get("absolute_url")
                        or f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
                    )
                    location_data = job.get("location", {})
                    location = location_data.get("name", "Remote") if isinstance(location_data, dict) else "Remote"

                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=source_url,
                            company=company.replace("-", " ").title(),
                            title=title,
                            description=job.get("content", ""),
                            raw_json=json.dumps(job, default=str),
                            raw_html=job.get("content", ""),
                        )
                    )
            except Exception as e:
                logger.warning(f"[Greenhouse] Skipping {company}: {e}")
                continue

        logger.info(f"[Greenhouse Agent] Batch {self._page} complete: {len(raw_jobs)} relevant jobs found")
        return raw_jobs

    def _matches_keywords(self, title: str) -> bool:
        """Check if a job title is relevant to any of the target keywords."""
        title_lower = title.lower()
        for kw in self.keywords:
            kw_parts = kw.lower().split()
            # Match if all keyword parts appear in the title
            if all(part in title_lower for part in kw_parts):
                return True
            # Also match on common related terms
            related = self._get_related_terms(kw.lower())
            for term in related:
                if term in title_lower:
                    return True
        return False

    @staticmethod
    def _get_related_terms(keyword: str) -> List[str]:
        """Expand a keyword to related job title terms for broader matching."""
        expansions = {
            "ml engineer": ["machine learning", "ml ", "deep learning", "ai engineer", "artificial intelligence", "nlp", "computer vision", "data scientist"],
            "data scientist": ["data science", "analytics", "machine learning", "statistician", "quantitative"],
            "devops": ["sre", "site reliability", "infrastructure", "platform engineer", "cloud engineer"],
            "backend": ["backend", "server", "api engineer", "python developer", "systems engineer"],
            "frontend": ["frontend", "front-end", "react", "ui engineer", "web developer"],
            "fullstack": ["full stack", "full-stack", "software engineer"],
        }
        for key, terms in expansions.items():
            if key in keyword:
                return terms
        # Generic fallback — just use the keyword itself
        return [keyword]
