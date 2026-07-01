import json
import re
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger


class LinkedInCollector(BaseCollector):
    """LinkedIn Public RSS Jobs Collector — Real keyword-driven agent with pagination."""

    def __init__(self):
        super().__init__(name="linkedin")
        self.keywords: List[str] = ["machine learning"]
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "+")
            # LinkedIn RSS supports pagination via 'start' parameter
            start_offset = (self._page - 1) * 25
            url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={kw_encoded}&location=Remote&start={start_offset}"
            )
            rss_url = (
                f"https://www.linkedin.com/jobs/rss/search"
                f"?keywords={kw_encoded}&location=Remote&start={start_offset}"
            )

            # Try RSS feed first, then HTML API
            for attempt_url in [rss_url, url]:
                try:
                    response = await self.get_with_retry(attempt_url)
                    content_type = response.headers.get("content-type", "")

                    if "xml" in content_type or attempt_url == rss_url:
                        # Parse as RSS/XML
                        soup = BeautifulSoup(response.content, "xml")
                        items = soup.find_all("item")

                        logger.info(
                            f"[LinkedIn Agent] Fetched {len(items)} RSS items for '{kw}' "
                            f"(page {self._page})"
                        )

                        for item in items:
                            title_elem = item.find("title")
                            link_elem = item.find("link")
                            desc_elem = item.find("description")
                            creator_elem = item.find("dc:creator") or item.find("creator")

                            title = title_elem.text.strip() if title_elem else "Untitled Job"
                            link = link_elem.text.strip() if link_elem else ""
                            description = desc_elem.text.strip() if desc_elem else ""

                            if not link:
                                continue

                            # Deduce company from creator element or title pattern
                            company = "Unknown"
                            if creator_elem:
                                company = creator_elem.text.strip()
                            else:
                                match = re.search(r" at (.*?)(?:\s*\(|$)", title)
                                if match:
                                    company = match.group(1).strip()

                            clean_title = re.sub(r"\s+at\s+.*?(?:\(.*?\))?$", "", title).strip()

                            raw_jobs.append(
                                RawJobCreate(
                                    source=self.name,
                                    source_url=link,
                                    company=company,
                                    title=clean_title,
                                    description=description,
                                    raw_json=json.dumps({
                                        "guid": item.find("guid").text if item.find("guid") else "",
                                        "pubDate": item.find("pubDate").text if item.find("pubDate") else "",
                                    }),
                                    raw_html=description,
                                )
                            )

                        if items:
                            break  # Got results, don't try next URL
                    else:
                        # Parse as HTML (LinkedIn jobs HTML API)
                        soup = BeautifulSoup(response.content, "html.parser")
                        job_cards = soup.find_all("li")

                        logger.info(
                            f"[LinkedIn Agent] Fetched {len(job_cards)} HTML cards for '{kw}' "
                            f"(page {self._page})"
                        )

                        for card in job_cards:
                            title_elem = card.find("h3", class_="base-search-card__title")
                            company_elem = card.find("h4", class_="base-search-card__subtitle")
                            link_elem = card.find("a", class_="base-card__full-link")
                            location_elem = card.find("span", class_="job-search-card__location")

                            if not title_elem:
                                continue

                            title = title_elem.text.strip()
                            company = company_elem.text.strip() if company_elem else "Unknown"
                            link = link_elem.get("href", "") if link_elem else ""
                            location = location_elem.text.strip() if location_elem else "Remote"

                            if not link:
                                continue

                            raw_jobs.append(
                                RawJobCreate(
                                    source=self.name,
                                    source_url=link,
                                    company=company,
                                    title=title,
                                    description=f"<p>{title} at {company} — {location}</p>",
                                    raw_json=json.dumps({
                                        "title": title,
                                        "company": company,
                                        "location": location,
                                    }),
                                    raw_html=f"<p>{title} at {company}</p>",
                                )
                            )

                        if job_cards:
                            break

                except Exception as e:
                    logger.warning(f"[LinkedIn Agent] Feed unavailable for '{kw}' ({attempt_url}): {e}")
                    continue

        logger.info(f"[LinkedIn Agent] Batch {self._page} complete: {len(raw_jobs)} jobs found")
        return raw_jobs
