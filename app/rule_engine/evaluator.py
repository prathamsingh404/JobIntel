import re
from typing import Tuple
from app.config.settings import settings

class RuleEvaluator:
    """Evaluates jobs against weighted keyword criteria to filter out irrelevant postings."""

    def __init__(self):
        self.config = settings.pipeline_config.get("rule_engine", {})
        self.min_score_threshold = self.config.get("min_score_threshold", 10)
        self.positive_keywords = self.config.get("positive_keywords", {})
        self.negative_keywords = self.config.get("negative_keywords", {})

    def evaluate(self, title: str, description: str) -> Tuple[bool, int, str]:
        """
        Evaluates a job listing.
        Returns:
            (passed_bool, score, reason)
        """
        score = 0
        matched_positives = []
        matched_negatives = []
        
        text_to_check = f"{title}\n{description}".lower()

        # Check negative keywords first
        for keyword, weight in self.negative_keywords.items():
            # Use word boundaries for safety
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, text_to_check):
                score += weight
                matched_negatives.append(keyword)
                
                # Check for critical rejection keywords (e.g. weight of -100)
                if weight <= -100:
                    return False, score, f"Rejected: Critical negative keyword '{keyword}' matched."

        # Check positive keywords
        for keyword, weight in self.positive_keywords.items():
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, text_to_check):
                score += weight
                matched_positives.append(keyword)

        # Evaluate net score
        if score < self.min_score_threshold:
            reason = (
                f"Score {score} is below threshold {self.min_score_threshold}. "
                f"Matched positives: {matched_positives}. Matched negatives: {matched_negatives}."
            )
            return False, score, reason

        reason = (
            f"Passed rule filter with score {score}. "
            f"Matched positives: {matched_positives}. Matched negatives: {matched_negatives}."
        )
        return True, score, reason
