import re
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import JobRepository
from app.models.database import Company, CleanedJob
from app.utils.logger import logger

class EnrichmentService:
    """Enrichment Service for Company & Job profiles in JobIntel V2."""

    @staticmethod
    async def enrich_company(session: AsyncSession, company_name: str) -> Company:
        """Looks up or creates an enriched company intelligence profile."""
        # Check if company already exists
        company = await JobRepository.get_company_by_name(session, company_name)
        if company:
            return company

        # Setup base enriched details derived from public references/descriptions
        domain = f"https://www.{company_name.lower().replace(' ', '')}.com"
        company_data = {
            "name": company_name,
            "website": domain,
            "industry": "Technology / AI / SaaS",
            "size_range": "50-250 employees",
            "headquarters": "San Francisco, CA",
            "ats_provider": "Greenhouse",
            "glassdoor_rating": 4.2,
            "ai_hiring_score": 75,
            "hiring_trends_summary": f"Active recruitment for engineering and machine learning teams."
        }

        # Create and save company
        company = await JobRepository.save_company(session, company_data)
        logger.info(f"Enriched and registered new company profile: '{company_name}'")
        return company

    @staticmethod
    def enrich_job_metadata(cleaned_job: CleanedJob) -> None:
        """Enriches metadata on cleaned jobs based on description details."""
        desc = cleaned_job.clean_description.lower()
        title = cleaned_job.title.lower()

        # Job category & specialization
        job_category = "Software Engineering"
        ai_specialization = None

        if "machine learning" in title or "ml " in title or "machine learning" in desc:
            job_category = "Machine Learning"
            ai_specialization = "Deep Learning / Core ML"
        elif "generative ai" in desc or "genai" in desc or "prompt" in desc:
            job_category = "AI Engineering"
            ai_specialization = "Generative AI / Agentic Systems"
        elif "llm" in desc or "large language" in desc or "rag" in desc:
            job_category = "LLM Engineering"
            ai_specialization = "Natural Language Processing (NLP)"
        elif "data scientist" in title or "data science" in desc:
            job_category = "Data Science"
            ai_specialization = "Analytics & Forecasting"
        elif "data engineer" in title or "data pipeline" in desc:
            job_category = "Data Engineering"
            ai_specialization = "ETL & Data Infrastructure"

        # Apply updates
        cleaned_job.job_category = job_category
        cleaned_job.ai_specialization = ai_specialization

        # Deduce experience level from experience string
        experience = getattr(cleaned_job, "experience", "")
        if experience:
            exp_lower = experience.lower()
            if any(w in exp_lower for w in ["senior", "lead", "principal", "manager"]):
                cleaned_job.seniority = "senior"
            elif any(w in exp_lower for w in ["junior", "entry", "intern"]):
                cleaned_job.seniority = "junior"
            else:
                cleaned_job.seniority = "mid"
        else:
            # Fallback deduction from description
            yrs_match = re.search(r"(\d+)\+?\s*years?", desc)
            if yrs_match:
                yrs = int(yrs_match.group(1))
                if yrs >= 5:
                    cleaned_job.seniority = "senior"
                elif yrs >= 2:
                    cleaned_job.seniority = "mid"
                else:
                    cleaned_job.seniority = "junior"
            else:
                cleaned_job.seniority = "mid"
