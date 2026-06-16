"""Load raw Parquet files into DuckDB and produce the curated ``jobs`` table."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import RAW_JOBS_DIR
from src.processing.normalize import (
    extract_city,
    extract_yoe,
    normalize_company,
    normalize_title,
)
from src.processing.salary_parser import parse_salary_text
from src.processing.skill_extractor import extract_skills
from src.storage.db import init_schema, session

log = logging.getLogger(__name__)


def _curate(row: pd.Series) -> dict:
    title, family = normalize_title(row.get("title"))
    salary = parse_salary_text(row.get("salary_text"))
    yoe_lo, yoe_hi = extract_yoe(f"{row.get('title','')} {row.get('description','')}")
    skills = extract_skills(f"{row.get('title','')} {row.get('description','')}")
    return {
        "job_id": row["job_id"],
        "source": row.get("source"),
        "url": row.get("url"),
        "title_raw": row.get("title"),
        "title_normalized": title,
        "role_family": family,
        "company_raw": row.get("company"),
        "company_normalized": normalize_company(row.get("company")),
        "location": row.get("location"),
        "city": extract_city(row.get("location")),
        "min_yoe": yoe_lo,
        "max_yoe": yoe_hi,
        "salary_min_monthly_twd": salary.min_monthly_twd,
        "salary_max_monthly_twd": salary.max_monthly_twd,
        "salary_currency": "TWD",
        "salary_period": salary.period_detected,
        "salary_confidence": salary.confidence,
        "skills": skills,
        "posted_at": row.get("posted_at") or None,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def load_jobs(parquet_paths: Iterable[Path]) -> int:
    init_schema()
    frames = [pd.read_parquet(p) for p in parquet_paths]
    if not frames:
        return 0
    raw = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["job_id"])
    curated = pd.DataFrame([_curate(row) for _, row in raw.iterrows()])

    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc).isoformat()

    with session() as conn:
        conn.register("raw_df", raw)
        conn.execute("DELETE FROM raw_jobs WHERE job_id IN (SELECT job_id FROM raw_df)")
        conn.execute("INSERT INTO raw_jobs SELECT * FROM raw_df")
        conn.unregister("raw_df")

        conn.register("curated_df", curated)
        conn.execute("DELETE FROM jobs WHERE job_id IN (SELECT job_id FROM curated_df)")
        conn.execute("INSERT INTO jobs SELECT * FROM curated_df")
        conn.unregister("curated_df")

        conn.execute(
            "INSERT INTO ingestion_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            [run_id, "jobs", started, datetime.now(timezone.utc).isoformat(),
             len(curated), "success", None],
        )
    log.info("loaded %d curated job records (run=%s)", len(curated), run_id)
    return len(curated)


def discover_raw_jobs(folder: Path = RAW_JOBS_DIR) -> list[Path]:
    return sorted(folder.glob("*.parquet"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_jobs(discover_raw_jobs())
