import json
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger


class IndeedCollector(BaseCollector):
    """Indeed Public RSS Jobs Collector — Real keyword-driven agent with pagination."""

    def __init__(self):
        super().__init__(name="indeed")
        self.keywords: List[str] = ["machine learning"]
        self._page = 1

    def set_page(self, page: int):
        self._page = page

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []

        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "+")
            # Indeed RSS supports pagination via 'start' parameter (0, 10, 20, ...)
            start_offset = (self._page - 1) * 25
            url = f"https://rss.indeed.com/rss?q={kw_encoded}&l=Remote&sort=date&start={start_offset}"

            try:
                response = await self.get_with_retry(url)
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")

                logger.info(
                    f"[Indeed Agent] Fetched {len(items)} items for keyword '{kw}' "
                    f"(page {self._page}, offset {start_offset})"
                )

                for item in items:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    source_elem = item.find("source")
                    pub_date_elem = item.find("pubDate")

                    title = title_elem.text.strip() if title_elem else "Untitled Job"
                    link = link_elem.text.strip() if link_elem else ""
                    description = desc_elem.text.strip() if desc_elem else ""

                    if not link:
                        continue

                    # Indeed RSS titles are "Title - Company - Location"
                    parts = title.split(" - ")
                    clean_title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else (
                        source_elem.text.strip() if source_elem else "Unknown"
                    )
                    location = parts[2].strip() if len(parts) > 2 else "Remote"

                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=link,
                            company=company,
                            title=clean_title,
                            description=description,
                            raw_json=json.dumps({
                                "guid": item.find("guid").text if item.find("guid") else "",
                                "pubDate": pub_date_elem.text if pub_date_elem else "",
                                "location": location,
                            }),
                            raw_html=description,
                        )
                    )
            except Exception as e:
                logger.warning(f"[Indeed Agent] RSS feed unavailable for '{kw}': {e}")
                continue

        logger.info(f"[Indeed Agent] Batch {self._page} complete: {len(raw_jobs)} jobs found")
        return raw_jobs
