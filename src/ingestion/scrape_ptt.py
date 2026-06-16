"""Fetch self-reported salary discussions from PTT (Tech_Job, Soft_Job, Salary).

PTT is public and unauthenticated except for an ``over18`` cookie on a few
boards; the boards we touch are not restricted. We only read post titles and
metadata from index pages, which is enough to count salary-related volume
for demand evidence. Full post bodies are fetched on demand for the records
that look like offer reports.

PTT's pagination uses absolute page numbers (``indexN.html``) where the
latest page is the one with the highest ``N`` and ``index.html`` redirects
to it. We follow the ``上頁`` ("previous page") link from ``index.html`` to
walk backwards through the last ``pages`` pages.
"""
from __future__ import annotations

import argparse
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd
from bs4 import BeautifulSoup

from src.config import RAW_PTT_DIR
from src.ingestion.http_client import PoliteClient

log = logging.getLogger(__name__)

PTT_BASE = "https://www.ptt.cc"
BOARDS = ("Tech_Job", "Soft_Job", "Salary")
OFFER_TAG_PATTERN = re.compile(r"\[(薪資|offer|請益|心得|徵才)\]", re.IGNORECASE)
_INDEX_NUMBER_RE = re.compile(r"index(\d+)\.html")


def _latest_index_number(client: PoliteClient, board: str) -> Optional[int]:
    """Find the latest absolute page number by reading the ``上頁`` link
    on ``index.html`` and adding one (since ``上頁`` points one back)."""
    resp = client.get(f"{PTT_BASE}/bbs/{board}/index.html")
    soup = BeautifulSoup(resp.text, "lxml")
    for a in soup.select("div.btn-group-paging a.btn"):
        if a.get_text(strip=True) == "‹ 上頁":
            m = _INDEX_NUMBER_RE.search(a.get("href", ""))
            if m:
                return int(m.group(1)) + 1
    return None


def _board_index_urls(client: PoliteClient, board: str, pages: int) -> list[str]:
    latest = _latest_index_number(client, board)
    if latest is None:
        return [f"{PTT_BASE}/bbs/{board}/index.html"]
    start = max(1, latest - pages + 1)
    return [f"{PTT_BASE}/bbs/{board}/index{n}.html" for n in range(latest, start - 1, -1)]


def fetch_board(board: str, pages: int = 3) -> Iterator[dict]:
    client = PoliteClient(headers={"Cookie": "over18=1"})
    urls = _board_index_urls(client, board, pages)
    log.info("ptt %s -> %d pages: %s", board, len(urls), urls[0])
    for url in urls:
        try:
            resp = client.get(url)
        except Exception as exc:
            log.warning("ptt fetch failed %s: %s", url, exc)
            continue
        soup = BeautifulSoup(resp.text, "lxml")
        for entry in soup.select("div.r-ent"):
            title_node = entry.select_one("div.title a")
            if not title_node:
                continue
            title = title_node.get_text(strip=True)
            href = title_node.get("href")
            if not OFFER_TAG_PATTERN.search(title):
                continue
            yield {
                "board": board,
                "title": title,
                "post_url": f"{PTT_BASE}{href}" if href else "",
                "author": entry.select_one("div.author").get_text(strip=True) if entry.select_one("div.author") else "",
                "date_index": entry.select_one("div.date").get_text(strip=True) if entry.select_one("div.date") else "",
            }


def fetch_post_body(url: str, client: Optional[PoliteClient] = None) -> str:
    client = client or PoliteClient(headers={"Cookie": "over18=1"})
    try:
        resp = client.get(url)
    except Exception as exc:
        log.warning("ptt body fetch failed %s: %s", url, exc)
        return ""
    soup = BeautifulSoup(resp.text, "lxml")
    main = soup.select_one("#main-content")
    return main.get_text("\n", strip=True) if main else ""


def run(boards: tuple[str, ...] = BOARDS, pages: int = 3,
        output_dir: Path = RAW_PTT_DIR, hydrate_bodies: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    body_client = PoliteClient(headers={"Cookie": "over18=1"}) if hydrate_bodies else None
    for board in boards:
        log.info("ingesting PTT board: %s", board)
        for r in fetch_board(board, pages=pages):
            r["scraped_at"] = datetime.now(timezone.utc).isoformat()
            if hydrate_bodies and r.get("post_url"):
                r["body"] = fetch_post_body(r["post_url"], client=body_client)
            else:
                r["body"] = ""
            rows.append(r)
    if not rows:
        raise RuntimeError("no records ingested from PTT")
    df = pd.DataFrame(rows)
    out = output_dir / f"ptt_{datetime.utcnow():%Y%m%d_%H%M%S}.parquet"
    df.to_parquet(out, index=False)
    log.info("wrote %d PTT records to %s", len(df), out)
    return out


def _cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape PTT salary discussions")
    p.add_argument("--pages", type=int, default=5,
                   help="number of pages per board to walk back (default: 5)")
    p.add_argument("--no-bodies", action="store_true",
                   help="skip fetching individual post bodies (faster)")
    p.add_argument("--boards", nargs="+", default=list(BOARDS))
    return p.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _cli()
    run(boards=tuple(args.boards), pages=args.pages,
        hydrate_bodies=not args.no_bodies)
