from src.processing.skill_extractor import extract_skills


def test_extracts_canonical_skills():
    skills = extract_skills("Looking for a backend engineer fluent in Python, Go, and Kafka.")
    assert "python" in skills
    assert "golang" in skills
    assert "kafka" in skills


def test_aliases_map_to_canonical():
    skills = extract_skills("We use K8s, TS and React.js on AWS.")
    assert "kubernetes" in skills
    assert "typescript" in skills
    assert "react" in skills
    assert "aws" in skills


def test_no_skills_returns_empty():
    assert extract_skills("Looking for a great teammate.") == []


def test_word_boundaries_avoid_substring_matches():
    assert "java" not in extract_skills("Senior Engineer for JavaScript")
    assert "javascript" in extract_skills("Senior Engineer for JavaScript")


def test_case_insensitive():
    assert "pytorch" in extract_skills("Experience with PYTORCH required.")
