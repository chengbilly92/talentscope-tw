"""End-to-end pipeline runner: bootstrap -> load -> verify."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import bootstrap_sample_data
from src.ingestion.load_to_warehouse import discover_raw_jobs, load_jobs
from src.storage.db import session


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TalentScope TW pipeline runner")
    p.add_argument("--bootstrap", action="store_true",
                   help="regenerate the sample dataset before loading")
    p.add_argument("--n-jobs", type=int, default=8_000)
    p.add_argument("--n-ptt", type=int, default=0,
                   help="synthetic PTT rows; default 0 because real scrape is preferred")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.bootstrap or not list(discover_raw_jobs()):
        bootstrap_sample_data.main(n_jobs=args.n_jobs, n_ptt=args.n_ptt)

    loaded = load_jobs(discover_raw_jobs())
    print(f"curated jobs loaded: {loaded}")

    with session(read_only=True) as conn:
        total, parsed = conn.execute(
            "SELECT COUNT(*), COUNT(salary_min_monthly_twd) FROM jobs"
        ).fetchone()
        print(f"verification: {parsed}/{total} rows have parseable salary "
              f"({(parsed / total * 100):.1f}% coverage)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
