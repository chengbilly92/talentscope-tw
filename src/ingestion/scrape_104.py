"""Fetch public job listings from 104.com.tw.

NOTE (2026-06): As of mid-2026 the public-looking AJAX list endpoint
(``/jobs/search/list``) has been moved behind Cloudflare's Bot Management
challenge. Plain ``requests`` calls return 403; even ``cloudscraper``
silently degrades to the SPA shell HTML rather than the underlying JSON.
The realistic production paths are (a) a Playwright/Chromium headless
worker that solves the JS challenge before issuing the XHR, or (b) 104's
paid B2B "Job-Bank Data Service" (NT\$50k--200k/yr). The MVP repository
uses a deterministic, plausibly-shaped synthetic dataset
(``scripts/bootstrap_sample_data.py``) for end-to-end demo, and the
report is explicit about that. This file is retained so the request /
parse shape is documented for the Playwright migration.

If you re-enable this scraper, respect ``robots.txt`` (the listing pages
are not explicitly disallowed) and rate-limit to <1 req/s.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd

from src.config import RAW_JOBS_DIR
from src.ingestion.http_client import PoliteClient

log = logging.getLogger(__name__)

LIST_URL = "https://www.104.com.tw/jobs/search/list"
DEFAULT_KEYWORDS = (
    "backend engineer", "frontend engineer", "data engineer",
    "machine learning", "devops", "ios", "android", "software engineer",
)


def fetch_listings(keyword: str, max_pages: int = 5, area: str = "6001001000",
                   client: PoliteClient | None = None) -> Iterator[dict]:
    client = client or PoliteClient(headers={"Referer": "https://www.104.com.tw/jobs/main/"})
    for page in range(1, max_pages + 1):
        params = {
            "ro": "1",
            "keyword": keyword,
            "area": area,
            "order": "15",
            "asc": "0",
            "page": str(page),
            "mode": "s",
        }
        try:
            resp = client.get(LIST_URL, params=params)
        except Exception as exc:
            log.warning("104 fetch failed at page %d for %r: %s", page, keyword, exc)
            return
        payload = resp.json()
        rows = payload.get("data", {}).get("list", []) or []
        if not rows:
            return
        for row in rows:
            yield _row_to_record(row, keyword)


def _row_to_record(row: dict, query: str) -> dict:
    job_no = row.get("jobNo") or row.get("jobLink", "").split("/job/")[-1].split("?")[0]
    salary_low = row.get("salaryLow") or 0
    salary_high = row.get("salaryHigh") or 0
    salary_text = row.get("salaryDesc") or ""
    if salary_low and salary_high and not salary_text:
        salary_text = f"月薪 {salary_low:,} ~ {salary_high:,} 元"
    return {
        "job_id": f"104:{job_no}",
        "source": "104",
        "url": "https:" + row.get("link", {}).get("job", ""),
        "title": row.get("jobName") or "",
        "company": row.get("custName") or "",
        "location": row.get("jobAddrNoDesc") or row.get("jobAddress") or "",
        "salary_text": salary_text,
        "description": row.get("description") or "",
        "posted_at": row.get("appearDate") or "",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "raw_payload": json.dumps({"query": query, **row}, ensure_ascii=False),
    }


def run(keywords: Iterable[str] = DEFAULT_KEYWORDS, max_pages: int = 5,
        output_dir: Path = RAW_JOBS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    client = PoliteClient(headers={"Referer": "https://www.104.com.tw/jobs/main/"})
    records: list[dict] = []
    for kw in keywords:
        log.info("ingesting 104 keyword: %s", kw)
        records.extend(fetch_listings(kw, max_pages=max_pages, client=client))
    if not records:
        raise RuntimeError("no records ingested from 104")
    df = pd.DataFrame(records).drop_duplicates(subset=["job_id"])
    out = output_dir / f"104_{datetime.utcnow():%Y%m%d_%H%M%S}.parquet"
    df.to_parquet(out, index=False)
    log.info("wrote %d records to %s", len(df), out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
