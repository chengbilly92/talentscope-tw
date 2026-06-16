from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.processing.aggregate import (
    company_pay_distribution,
    percentiles_by_role,
    trending_skills,
)
from src.storage.db import session

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(
    title="TalentScope TW",
    version="0.1.0",
    description="Salary intelligence for Taiwan tech talent.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    with session(read_only=True) as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        sources = conn.execute("SELECT DISTINCT source FROM jobs").fetchall()
    return {
        "status": "ok",
        "records": int(total),
        "sources": [r[0] for r in sources],
    }


@app.get("/api/benchmark")
def benchmark(
    role: str = Query(..., description="Normalised role title, e.g. 'Backend Engineer'"),
    yoe: Optional[int] = Query(None, ge=0, le=30),
    city: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
) -> dict:
    with session(read_only=True) as conn:
        result = percentiles_by_role(conn, role=role, min_yoe=yoe, city=city, skill=skill)
    if result.get("sample_size", 0) < 5:
        raise HTTPException(404, detail={
            "message": "sample too small for a reliable benchmark",
            "sample_size": result.get("sample_size", 0),
        })
    return {"role": role, "filters": {"yoe": yoe, "city": city, "skill": skill}, **result}


@app.get("/api/skills/trending")
def skills_trending(top: int = Query(15, ge=1, le=50)) -> dict:
    with session(read_only=True) as conn:
        return {"top": top, "skills": trending_skills(conn, top_n=top)}


@app.get("/api/companies/{company}")
def company(company: str) -> dict:
    with session(read_only=True) as conn:
        result = company_pay_distribution(conn, company)
    if result.get("sample_size", 0) == 0:
        raise HTTPException(404, detail={"message": f"no postings indexed for {company}"})
    return result


@app.get("/api/me/underpaid")
def underpaid(
    role: str,
    current_monthly_twd: int = Query(..., ge=20_000, le=2_000_000),
    yoe: Optional[int] = Query(None, ge=0, le=30),
    city: Optional[str] = Query(None),
) -> dict:
    with session(read_only=True) as conn:
        bench = percentiles_by_role(conn, role=role, min_yoe=yoe, city=city)
    if bench.get("sample_size", 0) < 5:
        raise HTTPException(404, detail={"message": "sample too small to compare"})
    p50 = bench["p50"]
    gap_pct = round((current_monthly_twd - p50) / p50 * 100, 1)
    if gap_pct >= 10:
        verdict = "above_market"
    elif gap_pct <= -10:
        verdict = "underpaid"
    else:
        verdict = "fair"
    return {
        "verdict": verdict,
        "your_pay_monthly_twd": current_monthly_twd,
        "market_median_monthly_twd": p50,
        "gap_pct": gap_pct,
        "benchmark": bench,
    }


@app.get("/api/roles")
def roles() -> dict:
    with session(read_only=True) as conn:
        rows = conn.execute("""
            SELECT title_normalized, role_family, COUNT(*) AS n
            FROM jobs
            WHERE title_normalized IS NOT NULL
            GROUP BY title_normalized, role_family
            ORDER BY n DESC
        """).fetchall()
    return {"roles": [{"title": t, "family": f, "postings": int(n)} for t, f, n in rows]}


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
