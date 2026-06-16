CREATE TABLE IF NOT EXISTS raw_jobs (
    job_id        VARCHAR PRIMARY KEY,
    source        VARCHAR NOT NULL,
    url           VARCHAR,
    title         VARCHAR,
    company       VARCHAR,
    location      VARCHAR,
    salary_text   VARCHAR,
    description   VARCHAR,
    posted_at     TIMESTAMP,
    scraped_at    TIMESTAMP,
    raw_payload   JSON
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id                 VARCHAR PRIMARY KEY,
    source                 VARCHAR,
    url                    VARCHAR,
    title_raw              VARCHAR,
    title_normalized       VARCHAR,
    role_family            VARCHAR,
    company_raw            VARCHAR,
    company_normalized     VARCHAR,
    location               VARCHAR,
    city                   VARCHAR,
    min_yoe                INTEGER,
    max_yoe                INTEGER,
    salary_min_monthly_twd INTEGER,
    salary_max_monthly_twd INTEGER,
    salary_currency        VARCHAR DEFAULT 'TWD',
    salary_period          VARCHAR DEFAULT 'monthly',
    salary_confidence      DOUBLE,
    skills                 VARCHAR[],
    posted_at              TIMESTAMP,
    ingested_at            TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ptt_salary_mentions (
    mention_id            VARCHAR PRIMARY KEY,
    board                 VARCHAR,
    post_url              VARCHAR,
    posted_at             TIMESTAMP,
    company               VARCHAR,
    role                  VARCHAR,
    yoe                   INTEGER,
    monthly_salary_twd    INTEGER,
    annual_salary_twd     INTEGER,
    raw_text              VARCHAR,
    extraction_confidence DOUBLE
);

CREATE TABLE IF NOT EXISTS skills_taxonomy (
    skill_id  VARCHAR PRIMARY KEY,
    name      VARCHAR,
    category  VARCHAR,
    aliases   VARCHAR[]
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id            VARCHAR PRIMARY KEY,
    source            VARCHAR,
    started_at        TIMESTAMP,
    finished_at       TIMESTAMP,
    records_ingested  INTEGER,
    status            VARCHAR,
    error_message     VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_jobs_role_yoe ON jobs(role_family, min_yoe);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_normalized);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_at);
