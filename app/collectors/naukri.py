import json
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger


class NaukriCollector(BaseCollector):
    """Naukri Jobs Collector — Real HTML scraper with pagination."""

    def __init__(self):
        super().__init__(name="naukri")
        self.keywords: List[str] = ["machine learning"]
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "-")
            # Naukri URL pattern with page support
            url = f"https://www.naukri.com/{kw_encoded}-jobs-{self._page}"

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                response = await self.client.get(url, headers=headers, timeout=12.0)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Try to extract JSON-LD structured data (most reliable)
                script_tags = soup.find_all("script", type="application/ld+json")
                for script in script_tags:
                    try:
                        ld_data = json.loads(script.string)
                        # Naukri embeds JobPosting schema.org objects
                        if isinstance(ld_data, dict) and ld_data.get("@type") == "JobPosting":
                            raw_jobs.append(self._parse_jsonld_job(ld_data, kw))
                        elif isinstance(ld_data, list):
                            for item in ld_data:
                                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                                    raw_jobs.append(self._parse_jsonld_job(item, kw))
                    except (json.JSONDecodeError, TypeError):
                        continue

                # Fallback: try to parse job cards from HTML structure
                if not raw_jobs:
                    job_cards = soup.find_all("article", class_="jobTuple") or soup.find_all("div", class_="srp-jobtuple-wrapper")
                    for card in job_cards:
                        title_elem = card.find("a", class_="title")
                        company_elem = card.find("a", class_="subTitle")
                        link = title_elem.get("href", "") if title_elem else ""

                        if not title_elem or not link:
                            continue

                        title = title_elem.text.strip()
                        company = company_elem.text.strip() if company_elem else "Unknown"
                        desc_elem = card.find("div", class_="job-description")
                        description = desc_elem.text.strip() if desc_elem else title

                        raw_jobs.append(
                            RawJobCreate(
                                source=self.name,
                                source_url=link,
                                company=company,
                                title=title,
                                description=description,
                                raw_json=json.dumps({"keyword": kw, "page": self._page}),
                                raw_html=description,
                            )
                        )

                logger.info(f"[Naukri Agent] Fetched {len(raw_jobs)} jobs for '{kw}' (page {self._page})")

            except Exception as e:
                logger.warning(f"[Naukri Agent] Scraping failed for '{kw}': {e}")
                continue

        logger.info(f"[Naukri Agent] Batch {self._page} complete: {len(raw_jobs)} jobs found")
        return raw_jobs

    def _parse_jsonld_job(self, ld_data: dict, keyword: str) -> RawJobCreate:
        """Parse a schema.org JobPosting JSON-LD object into a RawJobCreate."""
        title = ld_data.get("title", "Untitled")
        company_data = ld_data.get("hiringOrganization", {})
        company = company_data.get("name", "Unknown") if isinstance(company_data, dict) else "Unknown"
        description = ld_data.get("description", "")
        url = ld_data.get("url", f"https://www.naukri.com/{keyword.replace(' ', '-')}-jobs")

        location_data = ld_data.get("jobLocation", {})
        if isinstance(location_data, dict):
            address = location_data.get("address", {})
            location = address.get("addressLocality", "India") if isinstance(address, dict) else "India"
        else:
            location = "India"

        return RawJobCreate(
            source=self.name,
            source_url=url,
            company=company,
            title=title,
            description=description,
            raw_json=json.dumps(ld_data, default=str),
            raw_html=description,
        )
