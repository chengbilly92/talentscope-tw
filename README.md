# TalentScope TW

> Salary intelligence for Taiwan tech talent — know what you're worth before
> you sign that offer.

This is the implementation that accompanies the final-project report for **NTU
Big Data Systems, Spring 2026**. The system ingests public job postings
(104.com.tw) and PTT salary discussions, normalises them, and serves
percentile benchmarks via a REST API and a small web dashboard.

## Architecture (one-liner)

```
[scrapy / requests] → [Parquet raw lake] → [DuckDB curated warehouse]
                                                    │
                                       [FastAPI]──┤
                                       [Web UI]   │
                                       [Alerts]   ┘
```

A diagram and detailed write-up are in `R14922020.tex`.

## Running locally

Tested with Python 3.9–3.11.

```bash
pip install -r requirements.txt

# 1. Generate a realistic Taiwan-tech sample dataset and load it into DuckDB
python scripts/run_pipeline.py --bootstrap

# 2. Scrape PTT for real salary discussions, then mine the bodies for
#    explicit pay numbers and produce the demand-evidence artefacts
python -m src.ingestion.scrape_ptt --pages 10
python scripts/extract_ptt_pay.py
python scripts/generate_evidence.py

# 3. Run the API + dashboard
uvicorn src.api.main:app --reload --port 8000
```

Then open <http://localhost:8000/> in a browser.

Run the tests with `pytest tests/ -q`. There is also a `Makefile` that wraps the
common targets (`make bootstrap`, `make serve`, `make test`).

## Live data

The bootstrap dataset is deliberate — it lets the system run end-to-end without
hitting 104 or PTT every time, and keeps grading reproducible. The real
scrapers are in `src/ingestion/scrape_104.py` and `src/ingestion/scrape_ptt.py`
and respect rate limits and `over18` requirements. To run them against the live
sources:

```bash
python -m src.ingestion.scrape_104
python -m src.ingestion.scrape_ptt
python -m src.ingestion.load_to_warehouse
```

## Deployment

Three free-tier paths are supported out of the box. Pick one:

### Fly.io (recommended — Tokyo region, closest to Taipei)
```bash
fly launch --copy-config --name talentscope-tw   # uses fly.toml
fly volumes create ts_data --size 1
fly deploy
```

### Render
Push the repo to GitHub, then "New + → Blueprint" pointing at `render.yaml`.
Render will detect the Dockerfile and provision the free tier.

### Local Docker
```bash
docker compose up --build
```

## Repository layout

```
src/
  ingestion/      requests-based scrapers (104, PTT) + warehouse loader
  processing/     salary parser, skill extractor, normalisation, aggregations
  storage/        DuckDB schema + connection helper
  api/            FastAPI app and static-file mount
web/              vanilla-JS single-page dashboard
scripts/          bootstrap_sample_data.py, run_pipeline.py, generate_evidence.py
tests/            unit tests
data/raw/         Parquet "raw lake"
data/curated/     talentscope.duckdb
evidence/         PTT keyword counts, body-text pay extractions, revealed-preference
                  WTP and ROI WTP ceiling, competitor pricing benchmark
report/           LaTeX figures (architecture diagram, etc.)
R14922020.tex     final-project report
```

## Data ethics

- 104 listings are fetched through the same public AJAX endpoint that the
  website itself uses; the listing pages are not blocked by `robots.txt`. We
  identify ourselves in the `User-Agent` and rate-limit to <1 req/s.
- PTT requires an `over18` cookie on a few boards; the boards we touch
  (`Tech_Job`, `Soft_Job`, `Salary`) are not age-restricted. We only persist
  post titles and metadata by default; full post bodies are fetched only when
  explicitly requested.
- Survey responses in `evidence/` are deidentified (no name, email, company).

## Licence

MIT for the code in this repository. Job posting data and PTT post titles
remain the property of their respective publishers.
