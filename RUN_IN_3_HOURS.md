# 3-hour execution plan (no survey, no human in the loop)

The project deliberately gathers demand evidence from public data only --
no surveys, no Google Forms, no interviews. Everything below is shell
commands you copy-paste, plus one Overleaf upload and one `git push`.

| # | Step | Time | Notes |
|---|------|------|-------|
| 1 | Install deps + bootstrap pipeline | 10 min | `pip install -r requirements.txt && python scripts/run_pipeline.py --bootstrap` |
| 2 | Real PTT scrape (3 boards, 10 pages each, with bodies) | 5 min | `python -m src.ingestion.scrape_ptt --pages 10` |
| 3 | Mine PTT bodies for self-reported pay | 1 min | `python scripts/extract_ptt_pay.py` |
| 4 | Generate all `evidence/*.json` (PTT counts, competitors, revealed-preference WTP, ROI WTP) | 1 min | `python scripts/generate_evidence.py` |
| 5 | Inspect numbers and sanity-check §2 of the report | 15 min | Open each JSON, eyeball; the report quotes them verbatim |
| 6 | Compile PDF on Overleaf | 10 min | Upload `R14922020.tex`, Recompile (auto-picks XeLaTeX), download as `R14922020.pdf` |
| 7 | (Optional) Live deploy to Fly.io | 30 min | `fly launch` + `fly deploy`; update the live-URL line in the .tex and recompile |
| 8 | GitHub push | 10 min | `git init && git add . && git commit -m "TalentScope TW" && git remote add origin … && git push -u origin main` |
| 9 | Update GitHub + (optional) live URLs in the .tex, recompile, resubmit PDF | 5 min | Two `\url{}` lines near the top of `R14922020.tex` |

Realistic wall clock is **45–60 minutes for steps 1–6**; the deploy bonus
(step 7) is the only large optional block.

## Step 2 — real PTT scrape

```bash
rm -f data/raw/ptt/sample_ptt.parquet  # clear the synthetic seed
python -m src.ingestion.scrape_ptt --pages 10
# wrote ~150-200 PTT records to data/raw/ptt/ptt_YYYYMMDD_HHMMSS.parquet
```

`scrape_ptt.py` walks back ten index pages each from `Tech_Job`,
`Soft_Job`, and `Salary`, keeps posts tagged 薪資 / offer / 請益 / 心得
/ 徵才, hydrates the body of every kept post, and writes a single
Parquet file. The `over18` cookie and `上頁` link-following are
handled.

## Step 3 — body-text pay extraction

```bash
python scripts/extract_ptt_pay.py
# wrote N pay mentions -> evidence/ptt_pay_extractions.csv
# wrote summary       -> evidence/ptt_pay_summary.json
```

The script runs a small regex extractor over each post body, normalises
each match to monthly TWD, and emits both the per-mention CSV and a
summary JSON with p10/25/50/75/90 quantiles.

## Step 4 — generate WTP evidence

```bash
python scripts/generate_evidence.py
# writes evidence/ptt_keyword_analysis.json
#        evidence/competitor_pricing.json
#        evidence/revealed_preference_wtp.json
#        evidence/wtp_roi_estimate.json
```

`generate_evidence.py` does no surveys. It reads the existing PTT
parquet + the pay-summary from step 3, then computes:

- per-keyword unique-post hit rates,
- a revealed-preference WTP corridor by anchoring on five products
  Taiwanese knowledge workers already pay for,
- a value-based ROI ceiling derived from the median PTT-reported salary
  and published negotiation-gap literature,
- and the standing competitor pricing snapshot.

## Step 5 — eyeball the numbers in §2

The `.tex` quotes specific numbers from each JSON. If the new scrape
shifted them (e.g., the median monthly TWD moved from NT$83K to NT$90K),
update the corresponding cells in §2 of `R14922020.tex` before
recompiling.

## Step 6 — Overleaf compile

1. Pack into a zip (or upload just `R14922020.tex`; the architecture
   figure is inlined).
2. <https://www.overleaf.com> → New Project → Upload Project.
3. Overleaf reads the `% !TEX program = xelatex` magic comment in the
   first line and picks XeLaTeX automatically. If not, set
   **Menu → Compiler → XeLaTeX** manually.
4. Click **Recompile**. Download as `R14922020.pdf`.

## Step 8 — GitHub

```bash
git init -b main
git add .
git commit -m "TalentScope TW — NTU BDA final project"
git remote add origin https://github.com/<your-username>/talentscope-tw.git
git push -u origin main
```

Then open `R14922020.tex`, update the two `\url{...}` lines near the top
to your real GitHub URL (and Fly.io URL if you did step 7). Recompile on
Overleaf and resubmit.

## If you are tight on time

Drop step 7 (live deploy bonus, +10%). Everything else is still worth
~100% of base credit + 10% go-to-market bonus.
