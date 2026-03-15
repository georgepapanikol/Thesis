-- Online Job Advertisements (OJA) Database Schema

CREATE TABLE companies (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    website_url     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE job_postings (
    id                  SERIAL PRIMARY KEY,
    company_id          INTEGER REFERENCES companies (id) ON DELETE SET NULL,

    -- Source metadata
    source_url          TEXT NOT NULL UNIQUE,
    source_id           TEXT,                          -- e.g. "284909" from kariera.gr
    source_name         TEXT,                          -- e.g. "kariera.gr"

    -- Core fields
    title               TEXT NOT NULL,
    description_html    TEXT,                          -- raw HTML description
    description_text    TEXT,                          -- plain-text version
    meta_description    TEXT,                          -- og:description / meta description
    employment_type     TEXT,                          -- e.g. FULL_TIME, SEASONAL, PART_TIME
    location            TEXT,                          -- free-text location string

    -- Salary
    min_salary          NUMERIC,
    max_salary          NUMERIC,
    currency            TEXT DEFAULT 'EUR',

    -- Dates
    date_posted         TIMESTAMPTZ,
    date_expires        TIMESTAMPTZ,
    date_added          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seniority levels  (e.g. "Senior", "Mid-level", "Entry-level")
CREATE TABLE seniority_levels (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_seniority (
    job_posting_id  INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    seniority_id    INTEGER NOT NULL REFERENCES seniority_levels (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, seniority_id)
);

-- Categories  (e.g. "Security-Engineering", "DevSecOps")
CREATE TABLE categories (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_categories (
    job_posting_id  INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, category_id)
);

-- Parent categories  (e.g. "Human Resources", "Marketing")
CREATE TABLE parent_categories (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_parent_categories (
    job_posting_id      INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    parent_category_id  INTEGER NOT NULL REFERENCES parent_categories (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, parent_category_id)
);

-- Location restrictions  (e.g. "United States", "Germany")
CREATE TABLE location_restrictions (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_location_restrictions (
    job_posting_id          INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    location_restriction_id INTEGER NOT NULL REFERENCES location_restrictions (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, location_restriction_id)
);

-- Timezone restrictions  (numeric UTC offsets, e.g. -5, 1, 5.5)
CREATE TABLE timezone_restrictions (
    id          SERIAL PRIMARY KEY,
    utc_offset  NUMERIC NOT NULL UNIQUE
);

CREATE TABLE job_posting_timezone_restrictions (
    job_posting_id          INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    timezone_restriction_id INTEGER NOT NULL REFERENCES timezone_restrictions (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, timezone_restriction_id)
);

-- Tags / skills attached to a posting (many-to-many)
CREATE TABLE tags (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_tags (
    job_posting_id  INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    tag_id          INTEGER NOT NULL REFERENCES tags (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, tag_id)
);

-- Indexes
CREATE INDEX idx_job_postings_company    ON job_postings (company_id);
CREATE INDEX idx_job_postings_posted     ON job_postings (date_posted);
CREATE INDEX idx_job_postings_name       ON job_postings (source_name);
CREATE INDEX idx_job_postings_location   ON job_postings (location);
CREATE INDEX idx_job_postings_emp_type   ON job_postings (employment_type);
CREATE INDEX idx_job_postings_currency   ON job_postings (currency);
CREATE INDEX idx_job_postings_expires    ON job_postings (date_expires);
CREATE INDEX idx_job_postings_min_salary ON job_postings (min_salary);
