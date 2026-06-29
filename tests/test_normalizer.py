import pytest
from app.normalizer.title_normalizer import TitleNormalizer

def test_normalize_title_direct():
    normalizer = TitleNormalizer()
    
    assert normalizer.normalize("Senior Machine Learning Engineer") == "ml_engineer"
    assert normalizer.normalize("Sr. Machine-Learning Engineer") == "ml_engineer"
    assert normalizer.normalize("Junior Generative AI Engineer") == "ai_engineer"
    assert normalizer.normalize("Natural Language Processing (NLP) Specialist") == "llm_engineer"
    assert normalizer.normalize("Lead Data Scientist") == "data_scientist"
    assert normalizer.normalize("Principal DevOps Infrastructure Architect") == "devops_engineer"

def test_normalize_title_fallback():
    normalizer = TitleNormalizer()
    
    # Matches via token heuristics
    assert normalizer.normalize("Staff ML Software Developer") == "ml_engineer"
    
    # Matches via custom slug fallback
    assert normalizer.normalize("Office Coordinator Assistant") == "office_coordinator_assistant"
