from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_JOBS_DIR = DATA_DIR / "raw" / "jobs"
RAW_PTT_DIR = DATA_DIR / "raw" / "ptt"
CURATED_DIR = DATA_DIR / "curated"
DB_PATH = CURATED_DIR / "talentscope.duckdb"

USER_AGENT = "TalentScopeTW/0.1 (research; contact: r14922020@ntu.edu.tw)"
HTTP_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 1.5

for d in (RAW_JOBS_DIR, RAW_PTT_DIR, CURATED_DIR):
    d.mkdir(parents=True, exist_ok=True)
