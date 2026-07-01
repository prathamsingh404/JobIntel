import asyncio
import json
import google.generativeai as genai
from app.classifier.base import BaseClassifier
from app.models.schemas import AIServiceResult
from app.config.settings import settings
from app.utils.logger import logger

class GeminiClassifier(BaseClassifier):
    """Google Gemini AI service provider for structuring and classifying job listings."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def classify(self, title: str, description: str, company: str) -> AIServiceResult:
        logger.info(f"Submitting job classification to Gemini API: '{title}' at {company}")
        
        prompt = f"""
        You are an expert technical recruiter and AI Architect.
        Analyze this job listing and classify it into the most accurate canonical role.

        Job Title: {title}
        Company: {company}
        Description:
        {description}

        Choose the best fit category:
        - ml_engineer (Machine Learning, deep learning, training pipelines, PyTorch/Tensorflow, CUDA)
        - ai_engineer (Generative AI developer, API integrations, prompt engineering, agentic setups)
        - llm_engineer (NLP, Large Language Models, RAG, vector DBs, LangChain/LlamaIndex)
        - data_scientist (notebook analysis, statistical modelling, data science experiments, SQL/Python)
        - data_engineer (data ingestion, ETL, Spark, database schema, pipelines)
        - devops_engineer (MLOps, Kubernetes clusters, Docker, CI/CD, AWS)
        - backend_engineer (web services, Python/Java API development, systems engineering)
        - fullstack_engineer (frontend + backend engineering, web applications)
        - non_ai (any role not involving AI, machine learning, data engineering or core backend programming)

        You must return a JSON object with this structure:
        {{
          "ai_label": "one of the category names above",
          "confidence": 0.0 to 1.0,
          "reason": "brief explanation of why this category matches the job description",
          "evidence": "exact sentence quote from the description supporting this classification",
          "decision": "accept" or "reject"
        }}

        Set decision to 'accept' if the job falls into 'ml_engineer', 'ai_engineer', 'llm_engineer', or 'data_scientist'. Set decision to 'reject' otherwise.
        """

        try:
            # Wrap the blocking sync SDK call in an async threadpool
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            result_json = json.loads(response.text.strip())
            
            # Map JSON to Pydantic object
            return AIServiceResult(
                ai_label=result_json.get("ai_label", "non_ai"),
                confidence=float(result_json.get("confidence", 0.5)),
                reason=result_json.get("reason", "Parsed from LLM response"),
                evidence=result_json.get("evidence"),
                decision=result_json.get("decision", "reject")
            )
        except Exception as e:
            logger.error(f"Gemini API classification failed: {e}. Falling back to mock classifier.", exc_info=True)
            # Safe runtime fallback if API keys expire or network times out
            from app.classifier.mock_provider import MockClassifier
            fallback = MockClassifier()
            return await fallback.classify(title, description, company)
