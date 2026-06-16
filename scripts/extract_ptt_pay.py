"""Mine self-reported pay numbers from PTT post bodies.

We do NOT survey people. Instead, we treat the ~24-hour stream of PTT
offer / salary / 請益 posts as a revealed-preference window into Taiwan
SWE compensation. For each post in ``data/raw/ptt/*.parquet`` we scan
the body for numeric tokens anchored to a Chinese / English pay keyword
(月薪 / 年薪 / 底薪 / package / annual / monthly, etc.), normalise to
monthly TWD, and write the result to ``evidence/ptt_pay_extractions.csv``
plus a summary JSON.

The output is the basis for two claims in the report:
  (1) public Taiwan SWE pay-discussion volume is dense and current, and
  (2) the spread of self-reported pay is wide enough that a percentile
      benchmark has direct value to a user negotiating an offer.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import RAW_PTT_DIR

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

PAY_KEYWORD = r"(?:月薪|年薪|底薪|月底|薪資|薪水|package|annual|monthly|base|TC)"
AMOUNT_PATTERN = re.compile(
    rf"{PAY_KEYWORD}[^0-9\n]{{0,18}}"
    r"(\d{1,4}(?:[\.,]\d{1,3})?)\s*"
    r"(萬|K|k|W|w|M|m|百萬|千|元|NT|nt)?",
)


def _to_monthly_twd(value: float, unit: str, has_annual_keyword: bool) -> float | None:
    unit = (unit or "").lower()
    if unit in ("萬", "w"):
        amount = value * 10_000
    elif unit in ("k",):
        amount = value * 1_000
    elif unit in ("m", "百萬"):
        amount = value * 1_000_000
    elif unit in ("千",):
        amount = value * 1_000
    elif unit in ("元", "nt"):
        amount = value
    else:
        amount = value
    if amount < 100:
        return None
    if has_annual_keyword:
        return amount / 12.0
    if amount >= 500_000:
        return amount / 12.0
    return amount


def extract(body: str) -> list[float]:
    if not body:
        return []
    hits: list[float] = []
    for m in AMOUNT_PATTERN.finditer(body):
        raw = m.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        anchor_window = body[max(0, m.start() - 20): m.start() + 40]
        is_annual = bool(re.search(r"年薪|annual|/y|每年", anchor_window))
        monthly = _to_monthly_twd(value, m.group(2) or "", is_annual)
        if monthly is None:
            continue
        if 25_000 <= monthly <= 1_500_000:
            hits.append(monthly)
    return hits


def main() -> None:
    files = sorted(RAW_PTT_DIR.glob("*.parquet"))
    if not files:
        print("no PTT parquet files in data/raw/ptt/; run scrape_ptt first")
        return
    df = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)

    rows = []
    for _, post in df.iterrows():
        mentions = extract(post.get("body", "") or "")
        for amount in mentions:
            rows.append({
                "board": post["board"],
                "post_url": post["post_url"],
                "title": post["title"],
                "monthly_twd": int(round(amount)),
                "annualised_twd": int(round(amount * 12)),
            })

    if not rows:
        print("no salary mentions extracted; nothing to write")
        return

    ext_df = pd.DataFrame(rows)
    out_csv = EVIDENCE_DIR / "ptt_pay_extractions.csv"
    ext_df.to_csv(out_csv, index=False)

    summary = {
        "posts_scanned": int(len(df)),
        "posts_with_at_least_one_pay_mention": int(
            df["body"].fillna("").apply(lambda b: bool(extract(b))).sum()
        ),
        "total_mentions": int(len(ext_df)),
        "monthly_twd_quantiles": {
            "p10": int(ext_df["monthly_twd"].quantile(0.10)),
            "p25": int(ext_df["monthly_twd"].quantile(0.25)),
            "p50": int(ext_df["monthly_twd"].quantile(0.50)),
            "p75": int(ext_df["monthly_twd"].quantile(0.75)),
            "p90": int(ext_df["monthly_twd"].quantile(0.90)),
        },
        "spread_p10_to_p90_ratio": round(
            ext_df["monthly_twd"].quantile(0.90)
            / max(1, ext_df["monthly_twd"].quantile(0.10)), 2),
        "by_board": ext_df["board"].value_counts().to_dict(),
        "note": "Body-text regex extraction; precision is lossy by design "
                "(false-negatives > false-positives). Used for distributional "
                "claims, not for individual salary attribution.",
    }
    (EVIDENCE_DIR / "ptt_pay_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"wrote {len(ext_df)} pay mentions -> {out_csv}")
    print(f"wrote summary -> {EVIDENCE_DIR / 'ptt_pay_summary.json'}")
    print(json.dumps(summary["monthly_twd_quantiles"], indent=2))


if __name__ == "__main__":
    main()
