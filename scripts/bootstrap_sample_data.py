"""Generate a realistic Taiwan tech jobs dataset for local development and demo.

Real scraping against 104/PTT requires either a live internet connection or
saved fixtures, and the live targets sometimes change their HTML/JSON. This
script produces a deterministic, plausible dataset shaped exactly like a real
ingestion would produce, so the rest of the pipeline can be exercised end-to-
end without depending on network access.

Salary brackets are anchored to publicly visible 104 ranges and PTT offer
reports that the author surveyed during 2025-Q2.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import RAW_JOBS_DIR, RAW_PTT_DIR

SEED = 20260616
random.seed(SEED)

COMPANIES_BY_TIER: dict[str, list[tuple[str, list[tuple[str, float]], float]]] = {
    # (display_name, [(city, weight), ...], tier_pay_multiplier)
    # Weighted city lists approximate where each company actually has
    # engineering headcount in Taiwan.
    "global_top": [
        ("Google",    [("Taipei", 1.0)], 1.55),
        ("AWS",       [("Taipei", 1.0)], 1.40),
        ("Microsoft", [("Taipei", 1.0)], 1.35),
        ("Apple",     [("Taipei", 0.6), ("Hsinchu", 0.4)], 1.45),
        ("LINE",      [("Taipei", 1.0)], 1.20),
    ],
    "semi_giants": [
        ("TSMC",      [("Hsinchu", 0.50), ("Tainan", 0.30), ("Taichung", 0.20)], 1.10),
        ("MediaTek",  [("Hsinchu", 0.80), ("Taipei", 0.15), ("Tainan", 0.05)], 1.15),
        ("Realtek",   [("Hsinchu", 0.85), ("Tainan", 0.15)], 0.95),
        ("UMC",       [("Hsinchu", 0.55), ("Tainan", 0.45)], 1.00),
        ("ASE Group", [("Kaohsiung", 0.55), ("Taichung", 0.25), ("Hsinchu", 0.20)], 0.90),
        ("Mercuries", [("Taipei", 0.70), ("Hsinchu", 0.30)], 0.85),
    ],
    "unicorns": [
        ("Appier",   [("Taipei", 1.0)], 1.10),
        ("iKala",    [("Taipei", 1.0)], 1.00),
        ("KKBOX",    [("Taipei", 0.65), ("Kaohsiung", 0.35)], 0.90),
        ("91APP",    [("Taipei", 0.65), ("Taichung", 0.35)], 0.95),
        ("SHOPLINE", [("Taipei", 0.80), ("Taichung", 0.20)], 0.95),
        ("Dcard",    [("Taipei", 1.0)], 0.90),
        ("Pinkoi",   [("Taipei", 1.0)], 0.85),
        ("MaiCoin",  [("Taipei", 1.0)], 0.95),
    ],
    "domestic": [
        ("E.SUN",       [("Taipei", 0.55), ("Taichung", 0.25), ("Kaohsiung", 0.20)], 0.80),
        ("Cathay",      [("Taipei", 0.55), ("Taichung", 0.25), ("Kaohsiung", 0.20)], 0.80),
        ("Trend Micro", [("Taipei", 0.80), ("Taichung", 0.20)], 1.00),
        ("Synology",    [("New Taipei", 1.0)], 0.95),
        ("Pchome",      [("Taipei", 0.60), ("New Taipei", 0.40)], 0.75),
        ("Acer",        [("Taipei", 0.35), ("New Taipei", 0.40), ("Taichung", 0.25)], 0.75),
        ("ASUS",        [("Taipei", 0.55), ("New Taipei", 0.30), ("Taichung", 0.15)], 0.80),
        ("Foxconn",     [("New Taipei", 0.40), ("Taoyuan", 0.25),
                         ("Kaohsiung", 0.20), ("Taichung", 0.15)], 0.70),
    ],
}

ROLES = [
    # (display_title, role_family, base_monthly_twd, yoe_range, skill_pool)
    ("Backend Engineer", "Engineering", 52_000, (1, 5),
     ["python", "golang", "java", "postgres", "redis", "docker", "aws", "gcp"]),
    ("Senior Backend Engineer", "Engineering", 92_000, (5, 12),
     ["python", "golang", "java", "kafka", "spark", "postgres", "kubernetes", "aws", "terraform"]),
    ("Frontend Engineer", "Engineering", 48_000, (1, 5),
     ["typescript", "javascript", "react", "nextjs", "vue"]),
    ("Senior Frontend Engineer", "Engineering", 88_000, (5, 12),
     ["typescript", "react", "nextjs", "vue", "javascript"]),
    ("Full-Stack Engineer", "Engineering", 58_000, (2, 7),
     ["typescript", "react", "python", "postgres", "docker", "aws"]),
    ("Data Engineer", "Data", 62_000, (2, 6),
     ["python", "spark", "airflow", "kafka", "dbt", "snowflake", "bigquery", "postgres"]),
    ("Senior Data Engineer", "Data", 105_000, (6, 12),
     ["python", "spark", "kafka", "airflow", "snowflake", "dbt", "terraform", "aws"]),
    ("Data Scientist", "Data", 68_000, (2, 7),
     ["python", "pytorch", "tensorflow", "spark", "snowflake", "bigquery"]),
    ("ML Engineer", "ML", 78_000, (2, 7),
     ["python", "pytorch", "tensorflow", "huggingface", "kubernetes", "cuda", "aws"]),
    ("Research Engineer", "ML", 115_000, (3, 12),
     ["python", "pytorch", "cuda", "huggingface", "llm"]),
    ("DevOps/SRE", "Infra", 68_000, (2, 8),
     ["kubernetes", "docker", "terraform", "aws", "gcp", "azure"]),
    ("Mobile Engineer", "Engineering", 55_000, (2, 7),
     ["typescript", "javascript", "react"]),
    ("Security Engineer", "Infra", 78_000, (3, 10),
     ["python", "aws", "kubernetes"]),
    ("Product Manager", "Product", 72_000, (3, 10),
     ["python"]),
]

POSTING_BLURBS = (
    "We are looking for a {role} to join our team. Strong fundamentals in {skills} required. "
    "{exp_str} of professional experience preferred.",
    "Join {company} as a {role}. You will work with {skills} to scale our platform. "
    "{exp_str}.",
    "{company} is hiring a {role}. Tech stack: {skills}. Required experience: {exp_str}.",
)


def _salary_text(min_v: int, max_v: int) -> str:
    style = random.choice(["chinese_monthly", "chinese_yearly", "english_monthly", "english_yearly", "k_notation"])
    if style == "chinese_monthly":
        return f"月薪 {min_v:,} ~ {max_v:,} 元"
    if style == "chinese_yearly":
        return f"年薪 {min_v*14:,} ~ {max_v*14:,} 元"
    if style == "english_monthly":
        return f"Monthly NT${min_v:,} - NT${max_v:,}"
    if style == "english_yearly":
        return f"Annual NT${min_v*14:,} - NT${max_v*14:,}"
    return f"{min_v // 1000}K ~ {max_v // 1000}K (月薪)"


def _sample_postings(n: int) -> list[dict]:
    rows: list[dict] = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    for i in range(n):
        tier = random.choices(
            list(COMPANIES_BY_TIER.keys()),
            weights=[15, 25, 25, 35],
        )[0]
        company, city_weights, tier_mult = random.choice(COMPANIES_BY_TIER[tier])
        city = random.choices(
            [c for c, _ in city_weights],
            weights=[w for _, w in city_weights],
        )[0]
        role_title, family, base, (yoe_lo, yoe_hi), skill_pool = random.choice(ROLES)
        yoe = random.randint(yoe_lo, yoe_hi)
        yoe_multiplier = 1 + 0.045 * (yoe - yoe_lo)
        noise = random.uniform(0.88, 1.15)
        mid = base * tier_mult * yoe_multiplier * noise
        low = int(mid * 0.85 / 1000) * 1000
        high = int(mid * 1.15 / 1000) * 1000
        if random.random() < 0.07:
            low = high = 0
            salary_text = "面議"
        else:
            salary_text = _salary_text(low, high)
        skills_chosen = random.sample(skill_pool, k=min(len(skill_pool), random.randint(3, 6)))
        description = random.choice(POSTING_BLURBS).format(
            role=role_title,
            company=company,
            skills=", ".join(skills_chosen),
            exp_str=f"{yoe}+ years" if yoe >= 3 else "Entry to mid-level",
        )
        posted_at = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        rows.append({
            "job_id": f"104:demo{i:06d}",
            "source": "104",
            "url": f"https://www.104.com.tw/job/demo{i:06d}",
            "title": role_title,
            "company": company,
            "location": f"{city}市" if city in (
                "Taipei", "New Taipei", "Hsinchu", "Taichung",
                "Tainan", "Kaohsiung", "Taoyuan",
            ) else city,
            "salary_text": salary_text,
            "description": description,
            "posted_at": posted_at.isoformat(),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload": json.dumps({"synthetic": True}, ensure_ascii=False),
        })
    return rows


PTT_OFFER_TEMPLATES = (
    "[薪資] {company} {role} {yoe}年 offer",
    "[請益] {company} {role} 薪資合理嗎？",
    "[offer] 請益 {company} {role} package",
    "[薪資] 想離職換 {company} {role} 求建議",
)


def _sample_ptt(n: int) -> list[dict]:
    base = datetime.now(timezone.utc) - timedelta(days=60)
    rows: list[dict] = []
    boards = ("Tech_Job", "Soft_Job", "Salary")
    for i in range(n):
        company, _, _ = random.choice(sum(COMPANIES_BY_TIER.values(), []))
        role_title, _, base_pay, (yoe_lo, yoe_hi), _ = random.choice(ROLES)
        yoe = random.randint(yoe_lo, yoe_hi)
        salary = int(base_pay * (1 + 0.10 * yoe) * random.uniform(0.85, 1.20) / 1000) * 1000
        title = random.choice(PTT_OFFER_TEMPLATES).format(company=company, role=role_title, yoe=yoe)
        rows.append({
            "board": random.choice(boards),
            "title": title,
            "post_url": f"https://www.ptt.cc/bbs/Tech_Job/demo{i}.html",
            "author": f"user{random.randint(1000,9999)}",
            "date_index": (base + timedelta(days=random.randint(0, 60))).strftime("%m/%d"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "body": (
                f"想請教各位前輩，目前手上有 {company} 的 {role_title} offer，{yoe} 年經驗，"
                f"開的月薪約 {salary:,}，請問這個數字在板上算合理嗎？"
            ),
        })
    return rows


def main(n_jobs: int = 8_000, n_ptt: int = 0) -> None:
    """Generate the synthetic 104 sample. PTT data should come from the
    real scraper (``src.ingestion.scrape_ptt``); we no longer ship a
    synthetic PTT bootstrap because mixing it with the real scrape
    contaminates the unique-post counts and pay extractions used in the
    report. Pass ``n_ptt > 0`` only if you genuinely need a stand-in
    PTT file for offline pipeline testing.
    """
    RAW_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PTT_DIR.mkdir(parents=True, exist_ok=True)

    jobs = pd.DataFrame(_sample_postings(n_jobs))
    out_jobs = RAW_JOBS_DIR / "sample_104.parquet"
    jobs.to_parquet(out_jobs, index=False)
    print(f"wrote {len(jobs)} job postings -> {out_jobs}")

    if n_ptt > 0:
        ptt = pd.DataFrame(_sample_ptt(n_ptt))
        out_ptt = RAW_PTT_DIR / "sample_ptt.parquet"
        ptt.to_parquet(out_ptt, index=False)
        print(f"wrote {len(ptt)} synthetic PTT entries -> {out_ptt}")
    else:
        print("(skipping synthetic PTT; use src.ingestion.scrape_ptt for real data)")


if __name__ == "__main__":
    main()
