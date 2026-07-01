import json
from typing import List
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

# Real companies using Ashby ATS
ASHBY_COMPANIES = [
    "ramp", "linear", "notion", "vercel", "retool",
    "runway", "replicate", "deepgram", "cohere", "labelbox",
    "anyscale", "modal", "baseten", "banana-dev", "cerebras",
    "together-ai", "perplexity", "cursor", "codeium",
    "sourcegraph", "gitpod", "dagger", "earthly",
    "prefect", "dagster", "flyte", "union-ai",
    "superblocks", "airplane", "windmill",
    "neon", "supabase", "turso", "planetscale",
    "cal-com", "twenty", "documenso", "hoppscotch",
]

COMPANIES_PER_BATCH = 5


class AshbyCollector(BaseCollector):
    """Ashby Job Board API Collector — Production agent that discovers real jobs."""

    def __init__(self):
        super().__init__(name="ashby")
        self.keywords: List[str] = []
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        total_companies = len(ASHBY_COMPANIES)
        start_idx = ((self._page - 1) * COMPANIES_PER_BATCH) % total_companies
        batch_companies = []
        for i in range(COMPANIES_PER_BATCH):
            batch_companies.append(ASHBY_COMPANIES[(start_idx + i) % total_companies])

        logger.info(
            f"[Ashby Agent] Batch {self._page}: scraping companies {batch_companies} "
            f"(keywords: {self.keywords})"
        )

        for company in batch_companies:
            # Ashby has two common API patterns
            urls_to_try = [
                f"https://api.ashbyhq.com/posting-api/job-board/{company}",
                f"https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams",
            ]

            for url in urls_to_try[:1]:  # Try primary endpoint
                try:
                    response = await self.get_with_retry(url)
                    data = response.json()

                    # Ashby returns jobs in different shapes depending on the endpoint
                    postings = data.get("jobs", []) or data.get("postings", []) or data.get("data", {}).get("jobBoard", {}).get("jobPostings", [])

                    if not postings:
                        continue

                    logger.info(f"[Ashby] Fetched {len(postings)} jobs from {company}")

                    for post in postings:
                        title = post.get("title", "") or post.get("name", "")

                        if self.keywords and not self._matches_keywords(title):
                            continue

                        job_id = post.get("id", "")
                        source_url = (
                            post.get("jobUrl")
                            or post.get("hostedUrl")
                            or f"https://jobs.ashbyhq.com/{company}/{job_id}"
                        )

                        description = (
                            post.get("descriptionHtml", "")
                            or post.get("description", "")
                            or post.get("content", "")
                        )

                        location = post.get("location", "Remote")
                        if isinstance(location, dict):
                            location = location.get("name", "Remote")

                        raw_jobs.append(
                            RawJobCreate(
                                source=self.name,
                                source_url=source_url,
                                company=company.replace("-", " ").title(),
                                title=title,
                                description=description,
                                raw_json=json.dumps(post, default=str),
                                raw_html=description,
                            )
                        )
                    break  # Success — don't try fallback URLs
                except Exception as e:
                    logger.warning(f"[Ashby] Skipping {company} ({url}): {e}")
                    continue

        logger.info(f"[Ashby Agent] Batch {self._page} complete: {len(raw_jobs)} relevant jobs found")
        return raw_jobs

    def _matches_keywords(self, title: str) -> bool:
        title_lower = title.lower()
        for kw in self.keywords:
            kw_parts = kw.lower().split()
            if all(part in title_lower for part in kw_parts):
                return True
            related = self._get_related_terms(kw.lower())
            for term in related:
                if term in title_lower:
                    return True
        return False

    @staticmethod
    def _get_related_terms(keyword: str) -> List[str]:
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
        return [keyword]
