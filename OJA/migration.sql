-- ============================================================
-- ADDITIONS ONLY – existing tables/indexes are untouched
-- ============================================================

-- 2. Salary + currency + expiry (new columns on existing table)
ALTER TABLE job_postings
    ADD COLUMN IF NOT EXISTS min_salary     NUMERIC,
    ADD COLUMN IF NOT EXISTS max_salary     NUMERIC,
    ADD COLUMN IF NOT EXISTS currency       TEXT DEFAULT 'EUR',
    ADD COLUMN IF NOT EXISTS date_expires   TIMESTAMPTZ;

-- 3. Seniority levels  (e.g. "Senior", "Mid-level", "Entry-level")
CREATE TABLE seniority_levels (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_seniority (
    job_posting_id  INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    seniority_id    INTEGER NOT NULL REFERENCES seniority_levels (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, seniority_id)
);

-- 4. Categories  (e.g. "Security-Engineering", "DevSecOps")
CREATE TABLE categories (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_categories (
    job_posting_id  INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, category_id)
);

-- 5. Parent categories  (e.g. "Human Resources", "Marketing")
CREATE TABLE parent_categories (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_parent_categories (
    job_posting_id      INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    parent_category_id  INTEGER NOT NULL REFERENCES parent_categories (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, parent_category_id)
);

-- 6. Location restrictions  (e.g. "United States", "Germany")
CREATE TABLE location_restrictions (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_posting_location_restrictions (
    job_posting_id          INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    location_restriction_id INTEGER NOT NULL REFERENCES location_restrictions (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, location_restriction_id)
);

-- 7. Timezone restrictions  (numeric UTC offsets, e.g. -5, 1, 5.5)
CREATE TABLE timezone_restrictions (
    id          SERIAL PRIMARY KEY,
    utc_offset  NUMERIC NOT NULL UNIQUE   -- e.g. -10, -5.5, 5.5, 14
);

CREATE TABLE job_posting_timezone_restrictions (
    job_posting_id          INTEGER NOT NULL REFERENCES job_postings (id) ON DELETE CASCADE,
    timezone_restriction_id INTEGER NOT NULL REFERENCES timezone_restrictions (id) ON DELETE CASCADE,
    PRIMARY KEY (job_posting_id, timezone_restriction_id)
);

-- ============================================================
-- Additional indexes for the new columns
-- ============================================================
CREATE INDEX idx_job_postings_currency    ON job_postings (currency);
CREATE INDEX idx_job_postings_expires     ON job_postings (date_expires);
CREATE INDEX idx_job_postings_min_salary  ON job_postings (min_salary);