import pytest
from app.cleaner.pipeline import JobCleaner

def test_clean_html():
    cleaner = JobCleaner()
    html = "<div><h1>Job Description</h1><p>Join us <script>alert(1)</script> today!</p></div>"
    text = cleaner.clean_html(html)
    assert "Job Description" in text
    assert "Join us" in text
    assert "alert" not in text

def test_clean_url():
    cleaner = JobCleaner()
    url = "https://boards.greenhouse.io/company/jobs/123?utm_source=linkedin&ref=career_page&q=nlp"
    cleaned = cleaner.clean_url(url)
    assert "utm_source" not in cleaned
    assert "ref" not in cleaned
    assert "q=nlp" in cleaned

def test_normalize_unicode():
    cleaner = JobCleaner()
    raw = "Google\u2019s AI is \u201cawesome\u201d\u2013let\u00a0us build it."
    normalized = cleaner.normalize_unicode(raw)
    assert "Google's" in normalized
    assert '"awesome"' in normalized
    assert "let us" in normalized or "let-us" in normalized or "let - us" in normalized

def test_remove_emojis():
    cleaner = JobCleaner()
    raw = "We are hiring! 🚀 Apply now! ✨"
    cleaned = cleaner.clean(raw)
    assert "🚀" not in cleaned
    assert "✨" not in cleaned
    assert "We are hiring! Apply now!" in cleaned

def test_is_english():
    cleaner = JobCleaner()
    english_text = "We are seeking a senior machine learning engineer with 5 years of experience using Python and PyTorch to train Large Language Models."
    french_text = "Nous recherchons un ingénieur en apprentissage automatique expérimenté pour rejoindre notre équipe de développement d'API."
    
    assert cleaner.is_english(english_text) is True
    assert cleaner.is_english(french_text) is False
