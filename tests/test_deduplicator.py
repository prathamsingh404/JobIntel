import pytest
from app.deduplicator.detector import DuplicateDetector
from app.models.database import CleanedJob

def test_compute_hash():
    detector = DuplicateDetector()
    hash1 = detector.compute_hash("  Hello World  \n  ")
    hash2 = detector.compute_hash("helloworld")
    assert hash1 == hash2

def test_is_duplicate_hash():
    detector = DuplicateDetector()
    existing = [
        CleanedJob(
            id="job-1",
            title="Software Engineer",
            company="OpenAI",
            location="Remote",
            clean_description="Build RAG pipelines using python.",
            normalized_title="backend_engineer"
        )
    ]
    
    # Exact text match
    is_dup, reason = detector.is_duplicate(
        "Software Engineer",
        "OpenAI",
        "Build RAG pipelines using python.",
        existing
    )
    assert is_dup is True
    assert "Exact description hash" in reason

def test_is_duplicate_fuzzy():
    detector = DuplicateDetector()
    existing = [
        CleanedJob(
            id="job-1",
            title="Senior ML Engineer",
            company="Google",
            location="Remote",
            clean_description="We are seeking an experienced Machine Learning Engineer with 5 years experience in PyTorch and LLMs.",
            normalized_title="ml_engineer"
        )
    ]
    
    # Fuzzy description and matching metadata
    is_dup, reason = detector.is_duplicate(
        "Senior ML Engineer",
        "Google",
        "We are seeking an experienced Machine Learning Engineer with 5 years experience in PyTorch and LLMs. Apply now!",
        existing
    )
    assert is_dup is True
    assert "High similarity duplicate found" in reason

def test_not_duplicate_different_company():
    detector = DuplicateDetector()
    existing = [
        CleanedJob(
            id="job-1",
            title="Senior ML Engineer",
            company="Google",
            location="Remote",
            clean_description="We are seeking an experienced ML engineer to train deep language models and design optimization techniques with PyTorch.",
            normalized_title="ml_engineer"
        )
    ]
    
    # Same description, different company
    is_dup, reason = detector.is_duplicate(
        "Senior ML Engineer",
        "Stripe",
        "We are seeking an experienced ML engineer to train deep language models and design optimization techniques with PyTorch.",
        existing
    )
    # Cosine similarity is high, but company name similarity is low, so not duplicate!
    assert is_dup is False
