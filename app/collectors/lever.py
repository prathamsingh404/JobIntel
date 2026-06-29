import json
from typing import List
from app.collectors.base import BaseCollector
from app.models.schemas import RawJobCreate
from app.utils.logger import logger

class LeverCollector(BaseCollector):
    """Lever Postings API Collector."""

    def __init__(self):
        super().__init__(name="lever")
        self.companies = self.config.get("lever_companies", ["figma"])

    async def collect(self) -> List[RawJobCreate]:
        raw_jobs = []
        for company in self.companies:
            url = f"https://api.lever.co/v0/postings/{company}"
            try:
                response = await self.get_with_retry(url)
                postings = response.json()
                
                logger.info(f"Fetched {len(postings)} jobs from Lever postings for company: {company}")
                
                for post in postings:
                    job_id = post.get("id")
                    source_url = post.get("hostedUrl") or f"https://jobs.lever.co/{company}/{job_id}"
                    
                    # Lever returns description, lists, and additional text separately
                    desc_parts = [
                        post.get("descriptionHtml", ""),
                        post.get("lists", {}),
                        post.get("additionalHtml", "")
                    ]
                    # Format lists into description string
                    lists_text = ""
                    for item in post.get("lists", []):
                        lists_text += f"<h3>{item.get('text', '')}</h3><ul>"
                        for bullet in item.get("content", []):
                            lists_text += f"<li>{bullet}</li>"
                        lists_text += "</ul>"
                        
                    full_html = f"{desc_parts[0]}\n{lists_text}\n{desc_parts[2]}"
                    
                    raw_jobs.append(
                        RawJobCreate(
                            source=self.name,
                            source_url=source_url,
                            company=company.capitalize(),
                            title=post.get("text", "Untitled Job"),
                            description=full_html,
                            raw_json=json.dumps(post),
                            raw_html=full_html
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Could not fetch live Lever data for {company} (network/API error: {e}). Using robust fallback mock jobs."
                )
                raw_jobs.extend(self._get_mock_jobs(company))
                
        return raw_jobs

    def _get_mock_jobs(self, company: str) -> List[RawJobCreate]:
        """Provides realistic mock data for local testing and dry-runs."""
        return [
            RawJobCreate(
                source=self.name,
                source_url=f"https://jobs.lever.co/{company}/mock-201",
                company=company.capitalize(),
                title="Generative AI Research Scientist",
                description="""
                <h1>Generative AI Research Scientist</h1>
                <p>We are searching for an AI Scientist to lead our efforts in pre-training large transformer models. You will design neural architectures using PyTorch and CUDA.</p>
                <h3>What you will do:</h3>
                <ul>
                    <li>Train and evaluate large language models and multi-modal neural nets.</li>
                    <li>Optimize distributed training scripts using PyTorch, DeepSpeed, and Megatron-LM.</li>
                </ul>
                <h3>Qualifications:</h3>
                <p>Ph.D. or equivalent in Computer Science with a focus on Deep Learning. Extensive experience with PyTorch and Python is required.</p>
                """,
                raw_json=json.dumps({"id": "mock-201", "text": "Generative AI Research Scientist", "company": company}),
                raw_html="<h1>Generative AI Research Scientist</h1><p>Description text...</p>"
            ),
            RawJobCreate(
                source=self.name,
                source_url=f"https://jobs.lever.co/{company}/mock-202",
                company=company.capitalize(),
                title="Technical Recruiter - Talent Acquisition",
                description="""
                <p>We are looking for a Technical Recruiter to join our HR team. You will handle sourcing, scheduling, and onboarding new staff.</p>
                <p>Skills: HR, communication, applicant tracking systems, LinkedIn Recruiter.</p>
                """,
                raw_json=json.dumps({"id": "mock-202", "text": "Technical Recruiter", "company": company}),
                raw_html="<p>Recruiting details...</p>"
            )
        ]
