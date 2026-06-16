from __future__ import annotations

import duckdb


def percentiles_by_role(conn: duckdb.DuckDBPyConnection, role: str | None = None,
                        min_yoe: int | None = None, city: str | None = None,
                        skill: str | None = None) -> dict:
    where = ["salary_min_monthly_twd IS NOT NULL", "salary_max_monthly_twd IS NOT NULL"]
    params: list = []
    if role:
        where.append("title_normalized = ?")
        params.append(role)
    if city:
        where.append("city = ?")
        params.append(city)
    if min_yoe is not None:
        where.append("(min_yoe IS NULL OR min_yoe <= ?)")
        params.append(min_yoe)
        where.append("(max_yoe IS NULL OR max_yoe >= ?)")
        params.append(min_yoe)
    if skill:
        where.append("list_contains(skills, ?)")
        params.append(skill)

    sql = f"""
        SELECT
            COUNT(*) AS sample_size,
            quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.10) AS p10,
            quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.25) AS p25,
            quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.50) AS p50,
            quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.75) AS p75,
            quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.90) AS p90
        FROM jobs WHERE {' AND '.join(where)}
    """
    row = conn.execute(sql, params).fetchone()
    if not row or row[0] == 0:
        return {"sample_size": 0}
    return {
        "sample_size": int(row[0]),
        "p10": int(row[1]),
        "p25": int(row[2]),
        "p50": int(row[3]),
        "p75": int(row[4]),
        "p90": int(row[5]),
    }


def trending_skills(conn: duckdb.DuckDBPyConnection, top_n: int = 15) -> list[dict]:
    sql = """
        WITH exploded AS (
            SELECT unnest(skills) AS skill,
                   (salary_min_monthly_twd + salary_max_monthly_twd) / 2.0 AS mid_pay
            FROM jobs
            WHERE skills IS NOT NULL
        )
        SELECT skill,
               COUNT(*) AS postings,
               quantile_cont(mid_pay, 0.50) AS median_pay
        FROM exploded
        GROUP BY skill
        ORDER BY postings DESC
        LIMIT ?
    """
    return [
        {"skill": s, "postings": int(c), "median_pay_twd": int(p) if p else None}
        for s, c, p in conn.execute(sql, [top_n]).fetchall()
    ]


def company_pay_distribution(conn: duckdb.DuckDBPyConnection, company: str) -> dict:
    row = conn.execute(
        """
        SELECT COUNT(*),
               quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.25),
               quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.50),
               quantile_cont((salary_min_monthly_twd + salary_max_monthly_twd) / 2.0, 0.75)
        FROM jobs
        WHERE company_normalized = ?
          AND salary_min_monthly_twd IS NOT NULL
        """,
        [company],
    ).fetchone()
    return {
        "company": company,
        "sample_size": int(row[0]) if row else 0,
        "p25": int(row[1]) if row and row[1] else None,
        "p50": int(row[2]) if row and row[2] else None,
        "p75": int(row[3]) if row and row[3] else None,
    }
