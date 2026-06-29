from app.config.settings import settings
from app.classifier.base import BaseClassifier
from app.classifier.gemini_provider import GeminiClassifier
from app.classifier.mock_provider import MockClassifier
from app.utils.logger import logger

def get_classifier() -> BaseClassifier:
    """Returns the configured AI Classifier instance based on environment variables."""
    provider_name = settings.AI_PROVIDER.lower()
    
    if provider_name == "gemini":
        if settings.GEMINI_API_KEY:
            try:
                logger.info("Initializing Google Gemini Classifier.")
                return GeminiClassifier()
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Classifier: {e}. Falling back to Mock.")
        else:
            logger.warning("GEMINI_API_KEY is not set. Falling back to Mock Classifier.")
            
    # Default fallback
    logger.info("Initializing Local Mock Classifier.")
    return MockClassifier()
