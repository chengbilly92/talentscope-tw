from __future__ import annotations

import re
from dataclasses import dataclass

SKILL_TAXONOMY: dict[str, dict] = {
    "python":      {"category": "language",  "aliases": ["python3"]},
    "java":        {"category": "language",  "aliases": []},
    "golang":      {"category": "language",  "aliases": ["go"]},
    "typescript":  {"category": "language",  "aliases": ["ts"]},
    "javascript":  {"category": "language",  "aliases": ["js", "es6"]},
    "rust":        {"category": "language",  "aliases": []},
    "scala":       {"category": "language",  "aliases": []},
    "cpp":         {"category": "language",  "aliases": ["c++"]},
    "react":       {"category": "framework", "aliases": ["reactjs", "react.js"]},
    "vue":         {"category": "framework", "aliases": ["vuejs", "vue.js"]},
    "nextjs":      {"category": "framework", "aliases": ["next.js"]},
    "django":      {"category": "framework", "aliases": []},
    "fastapi":     {"category": "framework", "aliases": []},
    "spring":      {"category": "framework", "aliases": ["spring boot", "springboot"]},
    "postgres":    {"category": "data",      "aliases": ["postgresql"]},
    "mysql":       {"category": "data",      "aliases": []},
    "mongodb":     {"category": "data",      "aliases": ["mongo"]},
    "redis":       {"category": "data",      "aliases": []},
    "elasticsearch": {"category": "data",    "aliases": ["elastic"]},
    "kafka":       {"category": "data",      "aliases": []},
    "spark":       {"category": "data",      "aliases": ["pyspark"]},
    "hadoop":      {"category": "data",      "aliases": ["hdfs"]},
    "flink":       {"category": "data",      "aliases": []},
    "airflow":     {"category": "data",      "aliases": []},
    "dbt":         {"category": "data",      "aliases": []},
    "snowflake":   {"category": "data",      "aliases": []},
    "bigquery":    {"category": "data",      "aliases": ["bq"]},
    "aws":         {"category": "cloud",     "aliases": ["amazon web services"]},
    "gcp":         {"category": "cloud",     "aliases": ["google cloud"]},
    "azure":       {"category": "cloud",     "aliases": []},
    "kubernetes":  {"category": "cloud",     "aliases": ["k8s"]},
    "docker":      {"category": "cloud",     "aliases": []},
    "terraform":   {"category": "cloud",     "aliases": []},
    "pytorch":     {"category": "ml",        "aliases": []},
    "tensorflow":  {"category": "ml",        "aliases": ["tf"]},
    "huggingface": {"category": "ml",        "aliases": ["hugging face", "transformers"]},
    "llm":         {"category": "ml",        "aliases": ["large language model"]},
    "cuda":        {"category": "ml",        "aliases": []},
}


def _build_pattern() -> tuple[re.Pattern, dict[str, str]]:
    alias_to_skill: dict[str, str] = {}
    for skill, meta in SKILL_TAXONOMY.items():
        alias_to_skill[skill.lower()] = skill
        for alias in meta["aliases"]:
            alias_to_skill[alias.lower()] = skill
    sorted_aliases = sorted(alias_to_skill.keys(), key=len, reverse=True)
    escaped = [re.escape(a) for a in sorted_aliases]
    pattern = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(escaped) + r")(?![A-Za-z0-9])", re.IGNORECASE)
    return pattern, alias_to_skill


_PATTERN, _ALIAS_MAP = _build_pattern()


@dataclass
class SkillHit:
    skill: str
    category: str


def extract_skills(text: str | None) -> list[str]:
    if not text:
        return []
    found: set[str] = set()
    for match in _PATTERN.finditer(text):
        token = match.group(0).lower()
        if token in _ALIAS_MAP:
            found.add(_ALIAS_MAP[token])
    return sorted(found)


def skill_category(skill: str) -> str:
    return SKILL_TAXONOMY.get(skill, {}).get("category", "other")
