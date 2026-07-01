import re
import json
from typing import Dict, Any, List, Optional
from app.classifier.ai_client import AIClient
from app.utils.logger import logger

class SkillExtractor:
    """Extracts, normalizes, and classifies candidate or job skills in JobIntel V2."""

    # Pre-defined mapping of common technical synonyms to their canonical normalized terms
    CANONICAL_SKILL_MAP = {
        "python3": "Python",
        "python": "Python",
        "py": "Python",
        "tensor flow": "TensorFlow",
        "tensorflow": "TensorFlow",
        "tf": "TensorFlow",
        "pytorch": "PyTorch",
        "torch": "PyTorch",
        "scikit-learn": "Scikit-Learn",
        "scikit learn": "Scikit-Learn",
        "sklearn": "Scikit-Learn",
        "keras": "Keras",
        "fastapi": "FastAPI",
        "fast api": "FastAPI",
        "sql": "SQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "GCP",
        "google cloud": "GCP",
        "azure": "Azure",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "docker": "Docker",
        "terraform": "Terraform",
        "git": "Git",
        "github": "Git",
        "langchain": "LangChain",
        "llama index": "LlamaIndex",
        "llamaindex": "LlamaIndex",
        "huggingface": "Hugging Face",
        "hugging face": "Hugging Face",
        "hf": "Hugging Face"
    }

    def __init__(self):
        self.ai_client = AIClient()

    def extract_skills_regex(self, text: str) -> List[str]:
        """Performs rapid regex-based dictionary matching for common skills."""
        text_lower = f" {text.lower()} "
        found_skills = set()
        
        for synonym, canonical in self.CANONICAL_SKILL_MAP.items():
            # Use boundaries to prevent matching subsets (e.g. 'git' in 'digital')
            pattern = rf"\b{re.escape(synonym)}\b"
            if re.search(pattern, text_lower):
                found_skills.add(canonical)
                
        return sorted(list(found_skills))

    async def extract_skills_llm(self, text: str) -> Dict[str, List[str]]:
        """Uses LLM to extract categorised and structured skills from unstructured text."""
        prompt = f"""
        You are an expert recruitment parser. Analyze the text below and extract all professional skills.
        Group the skills into these exact categories:
        - programming_languages
        - frameworks
        - cloud_platforms
        - databases
        - libraries
        - tools
        - soft_skills

        Text:
        {text}

        You must return a JSON object with this exact structure:
        {{
          "programming_languages": ["list", "of", "languages"],
          "frameworks": ["list", "of", "frameworks"],
          "cloud_platforms": ["list", "of", "platforms"],
          "databases": ["list", "of", "databases"],
          "libraries": ["list", "of", "libraries"],
          "tools": ["list", "of", "tools"],
          "soft_skills": ["list", "of", "soft_skills"]
        }}
        """
        try:
            result = await self.ai_client.generate_json(prompt)
            # Normalize the extracted skill lists
            normalized_result = {}
            for category, skills in result.items():
                if isinstance(skills, list):
                    normalized_result[category] = self._normalize_skills_list(skills)
                else:
                    normalized_result[category] = []
            return normalized_result
        except Exception as e:
            logger.error(f"LLM skill extraction failed: {e}. Falling back to regex matches.")
            # Fallback to regex output placed in libraries category
            regex_skills = self.extract_skills_regex(text)
            return {
                "programming_languages": [s for s in regex_skills if s in ["Python", "SQL"]],
                "frameworks": [s for s in regex_skills if s in ["FastAPI"]],
                "cloud_platforms": [s for s in regex_skills if s in ["AWS", "GCP", "Azure"]],
                "databases": [s for s in regex_skills if s in ["PostgreSQL", "MySQL", "MongoDB", "Redis"]],
                "libraries": [s for s in regex_skills if s not in ["Python", "SQL", "FastAPI", "AWS", "GCP", "Azure", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kubernetes", "Docker", "Terraform", "Git"]],
                "tools": [s for s in regex_skills if s in ["Kubernetes", "Docker", "Terraform", "Git"]],
                "soft_skills": []
            }

    def _normalize_skills_list(self, skills: List[str]) -> List[str]:
        normalized = set()
        for skill in skills:
            skill_clean = skill.strip().lower()
            if skill_clean in self.CANONICAL_SKILL_MAP:
                normalized.add(self.CANONICAL_SKILL_MAP[skill_clean])
            else:
                # Retain title-cased custom skill if not in dictionary
                normalized.add(skill.strip().title())
        return sorted(list(normalized))
