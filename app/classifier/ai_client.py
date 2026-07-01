import json
import httpx
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.utils.logger import logger
from app.models.schemas import AIServiceResult

class AICostTracker:
    """Tracks token consumption and API cost estimations in JobIntel V2."""
    total_input_tokens = 0
    total_output_tokens = 0
    total_estimated_cost = 0.0

    @classmethod
    def log_usage(cls, provider: str, input_tokens: int, output_tokens: int) -> None:
        cls.total_input_tokens += input_tokens
        cls.total_output_tokens += output_tokens
        
        # Estimate costs based on public pricing models ($ per million tokens)
        rate_input = 0.0
        rate_output = 0.0
        if provider == "gemini":
            rate_input = 0.075 / 1_000_000  # gemini-2.5-flash rates
            rate_output = 0.30 / 1_000_000
        elif provider == "openai":
            rate_input = 0.150 / 1_000_000  # gpt-4o-mini rates
            rate_output = 0.600 / 1_000_000
        elif provider == "groq":
            rate_input = 0.05 / 1_000_000   # llama3 rates
            rate_output = 0.10 / 1_000_000

        cost = (input_tokens * rate_input) + (output_tokens * rate_output)
        cls.total_estimated_cost += cost
        logger.info(f"API Cost Log: {provider} used {input_tokens} In, {output_tokens} Out. Cost: ${cost:.6f}")


class AIClient:
    """Unified client routing requests to the configured LLM provider in JobIntel V2."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY

    async def generate_json(self, prompt: str, schema_format: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates a structured JSON response from the configured LLM provider."""
        if self.provider == "gemini" and self.gemini_key:
            return await self._call_gemini(prompt)
        elif self.provider == "openai" and self.openai_key:
            return await self._call_openai(prompt)
        elif self.provider == "groq" and self.groq_key:
            return await self._call_groq(prompt)
        else:
            # Fallback mock JSON
            logger.warning(f"No valid API keys found for '{self.provider}'. Returning fallback mock classification JSON.")
            return self._get_mock_fallback()

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Calls Google Gemini API using structured JSON output."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Executing generation
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Track approximate tokens (Gemini prompt uses roughly 4 chars per token)
            input_tok = len(prompt) // 4
            output_tok = len(response.text) // 4
            AICostTracker.log_usage("gemini", input_tok, output_tok)

            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Calls OpenAI GPT-4o-mini API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Token tracking
                usage = data.get("usage", {})
                AICostTracker.log_usage(
                    "openai", 
                    usage.get("prompt_tokens", 0), 
                    usage.get("completion_tokens", 0)
                )

                content = data["choices"][0]["message"]["content"]
                return json.loads(content.strip())
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def _call_groq(self, prompt: str) -> Dict[str, Any]:
        """Calls Groq Cloud API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                usage = data.get("usage", {})
                AICostTracker.log_usage(
                    "groq", 
                    usage.get("prompt_tokens", 0), 
                    usage.get("completion_tokens", 0)
                )

                content = data["choices"][0]["message"]["content"]
                return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    def _get_mock_fallback(self) -> Dict[str, Any]:
        """Returns a baseline mock classification JSON structure."""
        return {
            "ai_label": "ml_engineer",
            "confidence": 0.9,
            "reason": "Mocked validation fallback. The listing matches machine learning requirements.",
            "evidence": "Extracted from job posting text details.",
            "decision": "accept"
        }
