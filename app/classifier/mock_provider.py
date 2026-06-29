import asyncio
from app.classifier.base import BaseClassifier
from app.models.schemas import AIServiceResult
from app.utils.logger import logger

class MockClassifier(BaseClassifier):
    """Local heuristic classifier simulating LLM analysis for local testing."""

    async def classify(self, title: str, description: str, company: str) -> AIServiceResult:
        logger.info(f"Using Local Mock Classifier to analyze: '{title}' at {company}")
        # Simulate slight network delay
        await asyncio.sleep(0.1)

        title_lower = title.lower()
        desc_lower = description.lower()

        # Simple classification heuristics matching our config
        if any(w in title_lower or w in desc_lower for w in ["machine learning", "pytorch", "tensorflow", "ml engineer", "mle"]):
            return AIServiceResult(
                ai_label="ml_engineer",
                confidence=0.92,
                reason="The job posting explicitly mentions training deep learning networks or PyTorch development.",
                evidence="Matched core keywords: machine learning/pytorch/ml engineer.",
                decision="accept"
            )
        elif any(w in title_lower or w in desc_lower for w in ["generative ai", "llm", "rag", "langchain", "prompt engineer"]):
            return AIServiceResult(
                ai_label="llm_engineer",
                confidence=0.95,
                reason="The posting describes building systems using Large Language Models, Retrieval-Augmented Generation, or agents.",
                evidence="Matched core keywords: llm/rag/langchain.",
                decision="accept"
            )
        elif any(w in title_lower or w in desc_lower for w in ["artificial intelligence", "ai engineer", "ai developer"]):
            return AIServiceResult(
                ai_label="ai_engineer",
                confidence=0.88,
                reason="Identified as general artificial intelligence software engineering position.",
                evidence="Matched core keywords: artificial intelligence/ai engineer.",
                decision="accept"
            )
        elif any(w in title_lower or w in desc_lower for w in ["data scientist", "data science", "statistics"]):
            return AIServiceResult(
                ai_label="data_scientist",
                confidence=0.85,
                reason="Position involves statistical analysis, database querying, and model prototyping.",
                evidence="Matched core keywords: data scientist/statistics.",
                decision="accept"
            )
        elif any(w in title_lower or w in desc_lower for w in ["data engineer", "data pipeline"]):
            return AIServiceResult(
                ai_label="data_engineer",
                confidence=0.87,
                reason="Position focuses on ETL pipelines, data warehouses, and scaling databases.",
                evidence="Matched core keywords: data engineer/data pipeline.",
                decision="accept"
            )
        else:
            return AIServiceResult(
                ai_label="non_ai",
                confidence=0.90,
                reason="No prominent Artificial Intelligence or Machine Learning skills or responsibilities identified.",
                evidence="Description contains generic software development or non-technical tasks.",
                decision="reject"
            )
        
        return result
