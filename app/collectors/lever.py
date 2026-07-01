import json
from typing import List
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

# Large curated pool of real companies using Lever ATS
LEVER_COMPANIES = [
    # Tier 1 — Major tech
    "netflix", "spotify", "figma", "palantir", "lyft", "postman",
    "netlify", "vercel", "supabase", "prisma", "planetscale",
    # Tier 2 — AI/ML focused
    "openai", "anthropic", "huggingface", "cohere", "assemblyai",
    "deepmind", "runway", "stability", "jasper", "copy-ai",
    "midjourney", "synthesia", "descript", "elevenlabs",
    # Tier 3 — Growth stage
    "linear", "cal-com", "resend", "neon", "turso", "upstash",
    "tinybird", "inngest", "trigger-dev", "knock", "novu",
    "buildkite", "depot", "flightcontrol", "zeet",
    # Tier 4 — Enterprise & SaaS
    "notion", "airtable", "coda", "clickup", "monday",
    "asana", "smartsheet", "miro", "loom", "pitch",
    # Tier 5 — Fintech
    "plaid", "brex", "ramp", "mercury", "moderntreasury",
    "column", "unit", "alloy", "sardine", "persona",
    # Tier 6 — Security & Infra
    "snyk", "orca-security", "wiz", "lacework", "chainguard",
    "sigstore", "stackhawk", "detectify",
]

COMPANIES_PER_BATCH = 5


class LeverCollector(BaseCollector):
    """Lever Postings API Collector — Production agent that discovers real jobs."""

    def __init__(self):
        super().__init__(name="lever")
        self.keywords: List[str] = []
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        total_companies = len(LEVER_COMPANIES)
        start_idx = ((self._page - 1) * COMPANIES_PER_BATCH) % total_companies
        batch_companies = []
        for i in range(COMPANIES_PER_BATCH):
            batch_companies.append(LEVER_COMPANIES[(start_idx + i) % total_companies])

        logger.info(
            f"[Lever Agent] Batch {self._page}: scraping companies {batch_companies} "
            f"(keywords: {self.keywords})"
        )

        for company in batch_companies:
            url = f"https://api.lever.co/v0/postings/{company}"
            try:
                response = await self.get_with_retry(url)
                postings = response.json()

                if not isinstance(postings, list):
                    logger.warning(f"[Lever] Unexpected response format for {company}")
                    continue

                logger.info(f"[Lever] Fetched {len(postings)} jobs from {company}")

                for post in postings:
                    title = post.get("text", "")

                    if self.keywords and not self._matches_keywords(title):
                        continue

                    job_id = post.get("id")
                    source_url = post.get("hostedUrl") or f"https://jobs.lever.co/{company}/{job_id}"

                    # Build full description from Lever's structured fields
                    desc_parts = [post.get("descriptionHtml", "")]
                    for item in post.get("lists", []):
                        desc_parts.append(f"<h3>{item.get('text', '')}</h3><ul>")
                        for bullet in item.get("content", []):
                            desc_parts.append(f"<li>{bullet}</li>")
                        desc_parts.append("</ul>")
                    desc_parts.append(post.get("additionalHtml", ""))
                    full_html = "\n".join(desc_parts)

                    # Extract location from categories
                    categories = post.get("categories", {})
                    location = categories.get("location", "Remote") if isinstance(categories, dict) else "Remote"

                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=source_url,
                            company=company.replace("-", " ").title(),
                            title=title,
                            description=full_html,
                            raw_json=json.dumps(post, default=str),
                            raw_html=full_html,
                        )
                    )
            except Exception as e:
                logger.warning(f"[Lever] Skipping {company}: {e}")
                continue

        logger.info(f"[Lever Agent] Batch {self._page} complete: {len(raw_jobs)} relevant jobs found")
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
