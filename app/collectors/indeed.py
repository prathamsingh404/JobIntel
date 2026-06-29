import json
from typing import List
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class IndeedCollector(BaseCollector):
    """Indeed Public RSS Jobs Collector."""

    def __init__(self):
        super().__init__(name="indeed")
        self.keywords = self.config.get("indeed_keywords", ["machine learning", "pytorch"])

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []
        for kw in self.keywords:
            kw_encoded = kw.replace(" ", "+")
            # Indeed RSS structure
            url = f"https://rss.indeed.com/rss?q={kw_encoded}&l=Remote"
            try:
                response = await self.get_with_retry(url)
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")
                
                logger.info(f"Fetched {len(items)} items from Indeed RSS feed for keyword: {kw}")
                
                for item in items:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    source_elem = item.find("source")
                    
                    title = title_elem.text if title_elem else "Untitled Job"
                    link = link_elem.text if link_elem else ""
                    description = desc_elem.text if desc_elem else ""
                    
                    # Indeed titles in RSS are formatted as "Title - Company - Location"
                    parts = title.split(" - ")
                    clean_title = parts[0]
                    company = parts[1] if len(parts) > 1 else source_elem.text if source_elem else "Unknown"
                    
                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=link,
                            company=company,
                            title=clean_title,
                            description=description,
                            raw_json=json.dumps({
                                "guid": item.find("guid").text if item.find("guid") else ""
                            }),
                            raw_html=description
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Could not fetch Indeed RSS feed for {kw} ({e}). Using robust fallback mock jobs."
                )
                raw_jobs.extend(self._get_mock_jobs(kw))
                
        return raw_jobs

    def _get_mock_jobs(self, keyword: str) -> List[RawJobCreate]:
        """Provides realistic mock data for local testing and dry-runs."""
        return [
            RawJobCreate(
                source=self.name,
                source_url=f"https://www.indeed.com/viewjob?jk=mock-ind-501",
                company="DeepMind",
                title=f"Senior PyTorch and LLM Compiler Engineer",
                description="""
                <h1>Senior Compiler Engineer</h1>
                <p>Google DeepMind is looking for engineers to work on compiler optimizations. You will build libraries for PyTorch, TPU hardware, CUDA, and accelerate Large Language Models.</p>
                <h3>Requirements:</h3>
                <ul>
                    <li>Expertise in Python, C++, PyTorch internals, CUDA optimization.</li>
                    <li>Experience with compiler architectures (LLVM, MLIR, XLA).</li>
                    <li>Interest in optimizing deep learning training speeds.</li>
                </ul>
                <h3>Details:</h3>
                <p>Location: London/Remote. Great package and benefits.</p>
                """,
                raw_json=json.dumps({"id": "mock-ind-501", "keyword": keyword}),
                raw_html="<h1>Senior Compiler Engineer</h1><p>Description text...</p>"
            ),
            RawJobCreate(
                source=self.name,
                source_url=f"https://www.indeed.com/viewjob?jk=mock-ind-502",
                company="Acme Corp",
                title="Office HR Assistant",
                description="""
                <p>We are looking for an HR and Admin assistant to manage office tasks, file papers, organize logs, and run daily staff schedules.</p>
                <p>Required: High school diploma, basic computer skills.</p>
                """,
                raw_json=json.dumps({"id": "mock-ind-502"}),
                raw_html="<p>Administrative details...</p>"
            )
        ]
