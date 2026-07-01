import json
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

# Real career page URLs of companies known to post AI/ML/Engineering roles
CAREER_SITES = [
    # AI Companies
    {"url": "https://openai.com/careers/search", "company": "OpenAI"},
    {"url": "https://www.anthropic.com/careers", "company": "Anthropic"},
    {"url": "https://deepmind.google/about/careers/", "company": "DeepMind"},
    {"url": "https://jobs.netflix.com/search", "company": "Netflix"},
    {"url": "https://careers.google.com/jobs/results/", "company": "Google"},
    {"url": "https://www.metacareers.com/jobs", "company": "Meta"},
    {"url": "https://www.apple.com/careers/us/", "company": "Apple"},
    {"url": "https://amazon.jobs/en/search", "company": "Amazon"},
    {"url": "https://careers.microsoft.com/us/en/search-results", "company": "Microsoft"},
    # Growth-stage AI startups
    {"url": "https://stability.ai/careers", "company": "Stability AI"},
    {"url": "https://www.runway.ml/careers", "company": "Runway"},
    {"url": "https://jobs.ashbyhq.com/replicate", "company": "Replicate"},
    {"url": "https://www.together.ai/careers", "company": "Together AI"},
    {"url": "https://www.perplexity.ai/hub/careers", "company": "Perplexity"},
    # Infra & DevTools
    {"url": "https://www.cloudflare.com/careers/jobs/", "company": "Cloudflare"},
    {"url": "https://www.elastic.co/careers", "company": "Elastic"},
    {"url": "https://grafana.com/about/careers/open-positions/", "company": "Grafana Labs"},
    {"url": "https://temporal.io/careers", "company": "Temporal"},
]

SITES_PER_BATCH = 3


class CompanySiteCollector(BaseCollector):
    """Career Page Scraper — Real multi-site agent that extracts job listings from career pages."""

    def __init__(self):
        super().__init__(name="company_site")
        self.keywords: List[str] = []
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        total_sites = len(CAREER_SITES)
        start_idx = ((self._page - 1) * SITES_PER_BATCH) % total_sites
        batch_sites = []
        for i in range(SITES_PER_BATCH):
            batch_sites.append(CAREER_SITES[(start_idx + i) % total_sites])

        logger.info(
            f"[CareerSite Agent] Batch {self._page}: scraping sites "
            f"{[s['company'] for s in batch_sites]} (keywords: {self.keywords})"
        )

        for site in batch_sites:
            url = site["url"]
            company = site["company"]

            try:
                response = await self.get_with_retry(url)
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Strategy 1: Extract JSON-LD structured data (schema.org/JobPosting)
                script_tags = soup.find_all("script", type="application/ld+json")
                for script in script_tags:
                    try:
                        ld_data = json.loads(script.string)
                        postings = []
                        if isinstance(ld_data, dict) and ld_data.get("@type") == "JobPosting":
                            postings = [ld_data]
                        elif isinstance(ld_data, list):
                            postings = [d for d in ld_data if isinstance(d, dict) and d.get("@type") == "JobPosting"]
                        elif isinstance(ld_data, dict) and "@graph" in ld_data:
                            postings = [d for d in ld_data["@graph"] if isinstance(d, dict) and d.get("@type") == "JobPosting"]

                        for posting in postings:
                            title = posting.get("title", "")
                            if self.keywords and not self._title_matches(title):
                                continue

                            job_url = posting.get("url", url)
                            description = posting.get("description", "")

                            raw_jobs.append(
                                RawJobCreate(
                                    source=self.name,
                                    source_url=job_url,
                                    company=company,
                                    title=title,
                                    description=description,
                                    raw_json=json.dumps(posting, default=str),
                                    raw_html=description,
                                )
                            )
                    except (json.JSONDecodeError, TypeError):
                        continue

                # Strategy 2: Look for common job listing HTML patterns
                # Search for links that look like job postings
                job_links = soup.find_all("a", href=True)
                job_patterns = ["/jobs/", "/careers/", "/positions/", "/openings/", "/job/"]

                for link in job_links:
                    href = link.get("href", "")
                    text = link.get_text(strip=True)

                    if not text or len(text) < 5 or len(text) > 200:
                        continue

                    # Check if this looks like a job link
                    is_job_link = any(pattern in href.lower() for pattern in job_patterns)
                    if not is_job_link:
                        continue

                    # Skip navigation/generic links
                    skip_words = ["sign in", "log in", "apply", "learn more", "view all", "see all", "back to"]
                    if any(sw in text.lower() for sw in skip_words):
                        continue

                    if self.keywords and not self._title_matches(text):
                        continue

                    # Resolve relative URLs
                    if href.startswith("/"):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)

                    # Avoid duplicates within same batch
                    existing_urls = {j.source_url for j in raw_jobs}
                    if href in existing_urls:
                        continue

                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=href,
                            company=company,
                            title=text,
                            description=f"<p>{text} at {company}</p>",
                            raw_json=json.dumps({"title": text, "company": company, "url": href}),
                            raw_html=f"<p>{text} at {company}</p>",
                        )
                    )

                logger.info(f"[CareerSite] Scraped {company}: found {len([j for j in raw_jobs if j.company == company])} relevant postings")

            except Exception as e:
                logger.warning(f"[CareerSite] Skipping {company} ({url}): {e}")
                continue

        logger.info(f"[CareerSite Agent] Batch {self._page} complete: {len(raw_jobs)} jobs found")
        return raw_jobs

    def _title_matches(self, title: str) -> bool:
        """Check if a job title is relevant to any of the target keywords."""
        if not self.keywords:
            return True
        title_lower = title.lower()
        for kw in self.keywords:
            kw_parts = kw.lower().split()
            if all(part in title_lower for part in kw_parts):
                return True
            # Broad match on related terms
            related = {
                "ml engineer": ["machine learning", "ml ", "deep learning", "ai ", "nlp", "computer vision"],
                "data scientist": ["data science", "analytics", "machine learning"],
                "devops": ["sre", "site reliability", "infrastructure", "platform"],
                "backend": ["backend", "server", "api", "python"],
                "frontend": ["frontend", "front-end", "react", "ui"],
            }
            for key, terms in related.items():
                if key in kw.lower():
                    for term in terms:
                        if term in title_lower:
                            return True
        return False
