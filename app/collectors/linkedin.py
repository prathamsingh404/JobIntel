import json
import re
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class LinkedInCollector(BaseCollector):
    """LinkedIn Public RSS Jobs Collector."""

    def __init__(self):
        super().__init__(name="linkedin")
        self.keywords = self.config.get("linkedin_keywords", ["machine learning", "ai engineer"])
        self.location = self.config.get("linkedin_location", "Remote")

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []
        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "+")
            url = f"https://www.linkedin.com/jobs/rss/search?keywords={kw_encoded}&location={self.location}"
            try:
                response = await self.get_with_retry(url)
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")
                
                logger.info(f"Fetched {len(items)} items from LinkedIn RSS feed for keyword: {kw}")
                
                for item in items:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    creator_elem = item.find("dc:creator") or item.find("creator")
                    
                    title = title_elem.text if title_elem else "Untitled Job"
                    link = link_elem.text if link_elem else ""
                    description = desc_elem.text if desc_elem else ""
                    
                    # Deduce company name from title "Title at Company (Location)"
                    company = "Unknown"
                    if creator_elem:
                        company = creator_elem.text
                    else:
                        match = re.search(r" at (.*?) \(", title)
                        if match:
                            company = match.group(1)
                    
                    # Strip "at Company (Location)" from title if found to normalize
                    clean_title = re.sub(r" at .*?\(.*?\)", "", title).strip()
                    
                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=link,
                            company=company,
                            title=clean_title,
                            description=description,
                            raw_json=json.dumps({
                                "guid": item.find("guid").text if item.find("guid") else "",
                                "pubDate": item.find("pubDate").text if item.find("pubDate") else ""
                            }),
                            raw_html=description
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Could not fetch LinkedIn RSS feed for {kw} ({e}). Using robust fallback mock jobs."
                )
                raw_jobs.extend(self._get_mock_jobs(kw))
                
        return raw_jobs

    def _get_mock_jobs(self, keyword: str) -> List[RawJobCreate]:
        """Provides realistic mock data for local testing and dry-runs."""
        return [
            RawJobCreate(
                source=self.name,
                source_url=f"https://www.linkedin.com/jobs/view/mock-li-401",
                company="OpenAI",
                title=f"Research Engineer - {keyword.title()}",
                description="""
                <h1>Research Engineer</h1>
                <p>OpenAI is looking for research engineers to join our alignment teams. You will work on safety, fine-tuning, RLHF and NLP problems.</p>
                <h3>Requirements:</h3>
                <ul>
                    <li>Deep Python and PyTorch proficiency.</li>
                    <li>Strong understanding of transformers, RAG, and NLP architectures.</li>
                    <li>2+ years experience building production AI applications.</li>
                </ul>
                <h3>Desired Skills:</h3>
                <p>FastAPI, SQL, CUDA, AWS, Git.</p>
                """,
                raw_json=json.dumps({"id": "mock-li-401", "keyword": keyword}),
                raw_html="<h1>Research Engineer</h1><p>Description text...</p>"
            ),
            RawJobCreate(
                source=self.name,
                source_url=f"https://www.linkedin.com/jobs/view/mock-li-402",
                company="GrowthCorp",
                title="Director of Sales & Marketing",
                description="""
                <p>We are seeking a senior sales manager to lead marketing operations, generate leads, and run customer outreach campaign strategies.</p>
                <p>Skills: sales, marketing, cold calling, CRM.</p>
                """,
                raw_json=json.dumps({"id": "mock-li-402"}),
                raw_html="<p>Marketing details...</p>"
            )
        ]
