import json
import re
from typing import Dict, Any, Tuple
from app.config.settings import settings
from app.models.database import CleanedJob

class RelevanceScorer:
    """Calculates job-candidate profile alignment score (0-100) and rank category."""

    def __init__(self):
        self.profile = settings.pipeline_config.get("candidate_profile", {})
        self.preferred_titles = self.profile.get("preferred_titles", [])
        self.skills = [s.lower() for s in self.profile.get("skills", [])]
        self.preferred_locations = [l.lower() for l in self.profile.get("preferred_locations", [])]
        self.min_exp = self.profile.get("min_experience_years", 2)
        self.max_exp = self.profile.get("max_experience_years", 8)

    def _extract_experience_years(self, text: str) -> Tuple[int, int]:
        """Attempts to parse experience range (min/max years) from text using regex."""
        # Search for patterns like: "3-5 years", "3 to 5 years", "5+ years", "minimum 3 years"
        text_lower = text.lower()
        
        # Pattern 1: Range "3-5 years"
        range_match = re.search(r"\b(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years|yr|y\.o\.)\b", text_lower)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))

        # Pattern 2: Single value "+ / minimum" "5+ years", "min 5 years", "5 years experience"
        single_match = re.search(r"\b(\d+)\s*(?:\+|plus|years?|\s*min|\s*minimum)\b", text_lower)
        if single_match:
            val = int(single_match.group(1))
            # Assume no upper bound if it's "X+ years", or set arbitrarily
            return val, val + 5
            
        return 0, 999  # Default if not specified

    def calculate_score(self, job: CleanedJob) -> Tuple[int, str, str]:
        """
        Calculates the relevance score and maps it to a rank.
        Returns:
            (score, rank, match_details_json_string)
        """
        score = 0
        details = {}

        # 1. Title Match (Max 30 points)
        title_score = 0
        if job.normalized_title in self.preferred_titles:
            title_score = 30
        elif any(t in job.title.lower() for t in ["engineer", "developer", "scientist"]):
            title_score = 15
        score += title_score
        details["title_score"] = title_score
        details["normalized_title"] = job.normalized_title

        # 2. Skills Match (Max 40 points)
        desc_lower = job.clean_description.lower()
        matched_skills = []
        for skill in self.skills:
            # Word boundary check for skill keywords
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, desc_lower) or (job.skills and skill in job.skills.lower()):
                matched_skills.append(skill)
        
        if self.skills:
            skills_ratio = len(matched_skills) / len(self.skills)
            skills_score = int(skills_ratio * 40)
        else:
            skills_score = 0
        score += skills_score
        details["skills_score"] = skills_score
        details["matched_skills"] = matched_skills

        # 3. Location Alignment (Max 15 points)
        loc_score = 0
        job_loc_lower = job.location.lower()
        if "remote" in job_loc_lower or "anywhere" in job_loc_lower:
            loc_score = 15
        else:
            for loc in self.preferred_locations:
                if loc in job_loc_lower:
                    loc_score = 15
                    break
        score += loc_score
        details["location_score"] = loc_score
        details["job_location"] = job.location

        # 4. Experience Fit (Max 15 points)
        exp_score = 0
        job_min_exp, job_max_exp = self._extract_experience_years(job.clean_description)
        details["job_parsed_experience"] = f"{job_min_exp}-{job_max_exp} years"
        
        # If no specific experience mentioned, give default 10 points
        if job_min_exp == 0 and job_max_exp == 999:
            exp_score = 10
        # If job requirements overlap with candidate preference range
        elif self.min_exp <= job_min_exp <= self.max_exp or self.min_exp <= job_max_exp <= self.max_exp:
            exp_score = 15
        else:
            # Out of bounds but close
            exp_score = 5
        score += exp_score
        details["experience_score"] = exp_score

        # Map total score to Rank
        # 0-30 reject, 31-50 weak, 51-70 moderate, 71-85 good, 86-100 excellent
        if score <= 30:
            rank = "reject"
        elif score <= 50:
            rank = "weak"
        elif score <= 70:
            rank = "moderate"
        elif score <= 85:
            rank = "good"
        else:
            rank = "excellent"

        return score, rank, json.dumps(details)
