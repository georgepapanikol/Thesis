-- ============================================================
-- ESCO Normalized Database Schema for PostgreSQL
-- ============================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS skill_collection_relations CASCADE;
DROP TABLE IF EXISTS skill_collections CASCADE;
DROP TABLE IF EXISTS occupation_collection_relations CASCADE;
DROP TABLE IF EXISTS occupation_collections CASCADE;
DROP TABLE IF EXISTS occupation_broader CASCADE;
DROP TABLE IF EXISTS skill_broader CASCADE;           
DROP TABLE IF EXISTS skill_broader_groups CASCADE;
DROP TABLE IF EXISTS skill_skill_relations CASCADE;
DROP TABLE IF EXISTS occupation_skill_relations CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS skill_groups CASCADE;
DROP TABLE IF EXISTS occupations CASCADE;
DROP TABLE IF EXISTS isco_groups CASCADE;

-- Drop enum types
DROP TYPE IF EXISTS skill_type_enum CASCADE;
DROP TYPE IF EXISTS reuse_level_enum CASCADE;
DROP TYPE IF EXISTS relation_type_enum CASCADE;

-- Enum types
CREATE TYPE skill_type_enum AS ENUM ('knowledge', 'skill/competence');
CREATE TYPE reuse_level_enum AS ENUM ('cross-sector', 'occupation-specific', 'sector-specific', 'transversal');
CREATE TYPE relation_type_enum AS ENUM ('essential', 'optional');

-- ============================================================
-- ENTITY TABLES
-- ============================================================

-- 1. ISCO Groups
CREATE TABLE isco_groups (
    id              VARCHAR(10) PRIMARY KEY,
    url             TEXT UNIQUE NOT NULL,
    preferred_label TEXT NOT NULL,
    status          VARCHAR(20),
    alt_labels      TEXT,
    description     TEXT,
    broader_isco_group_id VARCHAR(10) REFERENCES isco_groups(id) DEFERRABLE INITIALLY DEFERRED,
    green_share     NUMERIC
);

-- 2. Occupations
CREATE TABLE occupations (
    id                        SERIAL PRIMARY KEY,
    url                       TEXT UNIQUE NOT NULL,
    preferred_label           TEXT NOT NULL,
    alt_labels                TEXT,
    hidden_labels             TEXT,
    status                    VARCHAR(20),
    modified_date             DATE,
    isco_group_id             VARCHAR(10) REFERENCES isco_groups(id),
    regulated_profession_note TEXT,
    scope_note                TEXT,
    definition                TEXT,
    description               TEXT,
    code                      VARCHAR(20),
    nace_code                 TEXT,
    green_share               NUMERIC
);

-- 3. Skill Groups
CREATE TABLE skill_groups (
    id              SERIAL PRIMARY KEY,
    url             TEXT UNIQUE NOT NULL,
    preferred_label TEXT NOT NULL,
    alt_labels      TEXT,
    hidden_labels   TEXT,
    status          VARCHAR(20),
    modified_date   DATE,
    scope_note      TEXT,
    description     TEXT,
    code            VARCHAR(20),
    broader_skill_group_id INTEGER REFERENCES skill_groups(id) DEFERRABLE INITIALLY DEFERRED
);

-- 4. Skills / Competences / Knowledge
CREATE TABLE skills (
    id              SERIAL PRIMARY KEY,
    url             TEXT UNIQUE NOT NULL,
    type            skill_type_enum,
    reuse_level     reuse_level_enum,
    preferred_label TEXT NOT NULL,
    alt_labels      TEXT,
    hidden_labels   TEXT,
    status          VARCHAR(20),
    modified_date   DATE,
    scope_note      TEXT,
    definition      TEXT,
    description     TEXT
);

-- ============================================================
-- RELATIONSHIP TABLES
-- ============================================================

-- 5. Occupation <-> Skill relations
CREATE TABLE occupation_skill_relations (
    id              SERIAL PRIMARY KEY,
    occupation_id   INTEGER NOT NULL REFERENCES occupations(id),
    skill_id        INTEGER NOT NULL REFERENCES skills(id),
    type            VARCHAR(50),
    UNIQUE (occupation_id, skill_id)
);

-- 6. Skill <-> Skill relations
CREATE TABLE skill_skill_relations (
    id                  SERIAL PRIMARY KEY,
    original_skill_id   INTEGER NOT NULL REFERENCES skills(id),
    related_skill_id    INTEGER NOT NULL REFERENCES skills(id),
    type                relation_type_enum,
    UNIQUE (original_skill_id, related_skill_id, type)
);

-- 7. Skill -> Skill Group broader
CREATE TABLE skill_broader_groups (
    skill_id        INTEGER NOT NULL REFERENCES skills(id),
    skill_group_id  INTEGER NOT NULL REFERENCES skill_groups(id),
    PRIMARY KEY (skill_id, skill_group_id)
);

-- 8. Occupation -> Occupation broader
CREATE TABLE occupation_broader (
    occupation_id         INTEGER NOT NULL REFERENCES occupations(id),
    broader_occupation_id INTEGER NOT NULL REFERENCES occupations(id),
    PRIMARY KEY (occupation_id, broader_occupation_id)
);

-- 9. Skill -> Skill broader
CREATE TABLE skill_broader (
    skill_id         INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    broader_skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (skill_id, broader_skill_id)
);

-- ============================================================
-- SKILL COLLECTION TABLES
-- ============================================================

-- 10. Skill Collections (one row per collection)
CREATE TABLE skill_collections (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL  -- e.g. 'green', 'digital', 'language'
);

-- 11. Skill Collection Relations (which skills belong to which collection)
CREATE TABLE skill_collection_relations (
    collection_id   INTEGER NOT NULL REFERENCES skill_collections(id) ON DELETE CASCADE,
    skill_id        INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, skill_id)
);

-- ============================================================
-- OCCUPATION COLLECTION TABLES
-- ============================================================

-- 12. Occupation Collections (one row per collection)
CREATE TABLE occupation_collections (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL  -- e.g. 'research_occupations'
);

-- 13. Occupation Collection Relations (which occupations belong to which collection)
CREATE TABLE occupation_collection_relations (
    collection_id   INTEGER NOT NULL REFERENCES occupation_collections(id) ON DELETE CASCADE,
    occupation_id   INTEGER NOT NULL REFERENCES occupations(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, occupation_id)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Entity lookups
CREATE INDEX idx_isco_broader      ON isco_groups(broader_isco_group_id);
CREATE INDEX idx_occ_label         ON occupations(preferred_label);
CREATE INDEX idx_occ_code          ON occupations(code);
CREATE INDEX idx_sg_broader        ON skill_groups(broader_skill_group_id);
CREATE INDEX idx_sg_label          ON skill_groups(preferred_label);
CREATE INDEX idx_skills_type       ON skills(type);
CREATE INDEX idx_skills_label      ON skills(preferred_label);
CREATE INDEX idx_skills_reuse      ON skills(reuse_level);

-- Relation lookups
CREATE INDEX idx_osr_occ           ON occupation_skill_relations(occupation_id);
CREATE INDEX idx_osr_skill         ON occupation_skill_relations(skill_id);
CREATE INDEX idx_ssr_original      ON skill_skill_relations(original_skill_id);
CREATE INDEX idx_ssr_related       ON skill_skill_relations(related_skill_id);
CREATE INDEX idx_sbg_skill         ON skill_broader_groups(skill_id);
CREATE INDEX idx_sbg_group         ON skill_broader_groups(skill_group_id);
CREATE INDEX idx_sb_skill          ON skill_broader(skill_id);
CREATE INDEX idx_sb_broader        ON skill_broader(broader_skill_id);

-- Collection lookups
CREATE INDEX idx_scr_collection    ON skill_collection_relations(collection_id);
CREATE INDEX idx_scr_skill         ON skill_collection_relations(skill_id);
CREATE INDEX idx_ocr_collection    ON occupation_collection_relations(collection_id);
CREATE INDEX idx_ocr_occupation    ON occupation_collection_relations(occupation_id);

-- ============================================================