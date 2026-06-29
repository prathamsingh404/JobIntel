import hashlib
from typing import List, Optional, Tuple
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config.settings import settings
from app.models.database import CleanedJob
from app.utils.logger import logger

class DuplicateDetector:
    """Detects duplicate job listings based on hashing, text, and metadata similarity."""

    def __init__(self):
        self.config = settings.pipeline_config.get("deduplication", {})
        self.title_threshold = self.config.get("title_similarity_threshold", 0.85)
        self.company_threshold = self.config.get("company_similarity_threshold", 0.90)
        self.desc_threshold = self.config.get("description_similarity_threshold", 0.85)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Returns the MD5 hash of normalized, lowercased text."""
        # Strip all whitespaces to prevent formatting-only differences
        normalized = "".join(text.lower().split())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def is_duplicate(
        self,
        new_title: str,
        new_company: str,
        new_desc: str,
        existing_jobs: List[CleanedJob]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates a new job against a list of active cleaned jobs.
        Returns:
            (is_duplicate_bool, reason_string_or_none)
        """
        if not existing_jobs:
            return False, None

        # 1. Quick exact hash match on clean descriptions (must also be at a similar company)
        new_hash = self.compute_hash(new_desc)
        for job in existing_jobs:
            existing_hash = self.compute_hash(job.clean_description)
            if new_hash == existing_hash:
                company_sim = fuzz.ratio(new_company.lower(), job.company.lower()) / 100.0
                if company_sim >= self.company_threshold:
                    return True, f"Exact description hash match with job ID {job.id}"

        # 2. Extract texts for TF-IDF cosine similarity
        descriptions = [job.clean_description for job in existing_jobs]
        descriptions.append(new_desc)

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(descriptions)
            
            # Compute cosine similarities between the last item (new_desc) and all others
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
        except Exception as e:
            logger.warning(f"TF-IDF Vectorization failed (possibly empty text): {e}")
            similarities = [0.0] * len(existing_jobs)

        # 3. Combined heuristics check (Title + Company + Description Cosine Similarity)
        for idx, job in enumerate(existing_jobs):
            similarity_score = similarities[idx]
            
            # If description similarity is high
            if similarity_score >= self.desc_threshold:
                # Validate if company and title match thresholds
                company_sim = fuzz.ratio(new_company.lower(), job.company.lower()) / 100.0
                title_sim = fuzz.token_sort_ratio(new_title.lower(), job.title.lower()) / 100.0
                
                if company_sim >= self.company_threshold and title_sim >= self.title_threshold:
                    reason = (
                        f"High similarity duplicate found (Job ID: {job.id}). "
                        f"Title Sim: {title_sim:.2f}, Company Sim: {company_sim:.2f}, Desc Sim: {similarity_score:.2f}"
                    )
                    return True, reason

        return False, None
