import abc
from app.models.schemas import AIServiceResult

class BaseClassifier(abc.ABC):
    """Abstract base class for LLM-based role classifiers."""

    @abc.abstractmethod
    async def classify(self, title: str, description: str, company: str) -> AIServiceResult:
        """
        Classifies a job using LLM.
        Returns:
            AIServiceResult containing the label, confidence, reason, evidence, and final decision.
        """
        pass
