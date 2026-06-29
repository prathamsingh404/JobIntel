import pytest
from app.rule_engine.evaluator import RuleEvaluator

def test_rule_evaluator_pass():
    evaluator = RuleEvaluator()
    
    title = "Machine Learning Infrastructure Architect"
    desc = "You will write clean Python scripts and build deep learning models with PyTorch. Experience with MLOps pipelines and SQL databases is highly desired."
    
    passed, score, reason = evaluator.evaluate(title, desc)
    assert passed is True
    assert score >= 10
    assert "PyTorch" in reason or "pytorch" in reason.lower()

def test_rule_evaluator_critical_reject():
    evaluator = RuleEvaluator()
    
    title = "Technical Recruiter"
    desc = "We need an HR lead to search for Python and PyTorch engineers. You will coordinate pipeline schedules and run talent onboarding campaigns."
    
    passed, score, reason = evaluator.evaluate(title, desc)
    # Even though Python and PyTorch are mentioned, "Recruiter" has -100 weight, triggering instant failure
    assert passed is False
    assert "Critical negative keyword" in reason

def test_rule_evaluator_low_score_reject():
    evaluator = RuleEvaluator()
    
    title = "Java Web Developer"
    desc = "Write java code and SQL statements to configure client websites. Help debug AWS deployment issues."
    
    passed, score, reason = evaluator.evaluate(title, desc)
    # SQL (3) + AWS (3) = 6, which is below the minimum threshold of 10
    assert passed is False
    assert "below threshold" in reason
