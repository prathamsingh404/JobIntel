import re
from typing import Dict, Any, Optional, Tuple

class JobParserService:
    """Decoupled Parser & Validator Service for JobIntel V2."""

    @staticmethod
    def parse_raw_job(raw_job: Any) -> Dict[str, Any]:
        """Extracts structured fields from raw scraped job payloads."""
        title = getattr(raw_job, "title", "")
        company = getattr(raw_job, "company", "")
        description = getattr(raw_job, "description", "")
        source_url = getattr(raw_job, "source_url", "")
        
        # Deduce workplace type (remote, hybrid, onsite)
        workplace_type = "onsite"
        title_lower = title.lower()
        desc_lower = description.lower()
        if "remote" in title_lower or "remote" in desc_lower or "telecommute" in desc_lower:
            workplace_type = "remote"
        elif "hybrid" in title_lower or "hybrid" in desc_lower:
            workplace_type = "hybrid"

        # Deduce seniority
        seniority = "mid"
        if any(w in title_lower for w in ["senior", "sr.", "lead", "principal", "staff"]):
            seniority = "senior"
        elif any(w in title_lower for w in ["junior", "jr.", "associate", "entry", "intern"]):
            seniority = "junior"

        # Deduce currency
        currency = "USD"
        if "₹" in description or "lpa" in desc_lower or "inr" in desc_lower:
            currency = "INR"
        elif "£" in description or "gbp" in desc_lower:
            currency = "GBP"
        elif "€" in description or "eur" in desc_lower:
            currency = "EUR"

        # Attempt to parse recruiter contact info where publicly available
        recruiter_name = None
        recruiter_contact = None
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", description)
        if email_match:
            recruiter_contact = email_match.group(0)

        return {
            "title": title,
            "company": company,
            "description": description,
            "source_url": source_url,
            "workplace_type": workplace_type,
            "seniority": seniority,
            "salary_currency": currency,
            "recruiter_name": recruiter_name,
            "recruiter_contact": recruiter_contact,
            "raw_json": getattr(raw_job, "raw_json", None),
            "raw_html": getattr(raw_job, "raw_html", None),
            "source": getattr(raw_job, "source", "unknown")
        }

    @staticmethod
    def validate(parsed_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates that mandatory fields are present and not empty."""
        if not parsed_data.get("title"):
            return False, "Validation Error: Missing job title."
        if not parsed_data.get("company"):
            return False, "Validation Error: Missing company name."
        if not parsed_data.get("description") or not parsed_data.get("description").strip():
            return False, "Validation Error: Job description is empty."
        if not parsed_data.get("source_url"):
            return False, "Validation Error: Missing source url."
        return True, None
