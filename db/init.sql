-- db/init.sql
-- Consolidated Initialization Script for German Freelancer Contract Analyzer

-- 1. EXTENSIONS
-- Required for the Layer 2 Vector Playbook [cite: 170]
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. LAYER 1: RELATIONAL TABLES (EXACT FACTS) [cite: 108]
-- Stores hourly-rate percentiles by skill, region, and experience [cite: 112]
CREATE TABLE IF NOT EXISTS rate_benchmarks (
    id SERIAL PRIMARY KEY,
    skill_category TEXT NOT NULL,
    region TEXT,
    experience TEXT CHECK (experience IN ('junior', 'mid', 'senior')),
    p25_eur_per_h NUMERIC(6,2),
    median_eur_per_h NUMERIC(6,2),
    p75_eur_per_h NUMERIC(6,2),
    source TEXT NOT NULL,
    source_url TEXT,
    source_year INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Stores mappings from clause types to authoritative legal text [cite: 113]
CREATE TABLE IF NOT EXISTS statute_references (
    id SERIAL PRIMARY KEY,
    clause_type TEXT NOT NULL,
    paragraph TEXT NOT NULL,
    text_excerpt TEXT NOT NULL,
    official_url TEXT,
    UNIQUE (clause_type, paragraph)
);

-- 3. LAYER 2: VECTOR TABLE (THE PLAYBOOK) [cite: 170]
-- Stores risky clause patterns, legal reasoning, and suggested redlines [cite: 171]
-- Provenance fields (source_url, source_type) added 2026-04-27 to support the
-- defensibility audit: every entry must trace to a primary German legal source.
CREATE TABLE IF NOT EXISTS playbook (
    id TEXT PRIMARY KEY, -- e.g., 'PB-001'
    clause_type TEXT NOT NULL,
    risk_level TEXT CHECK (risk_level IN ('high', 'medium', 'low')),
    pattern_description TEXT NOT NULL,
    example_risky_wording TEXT,
    legal_reasoning TEXT NOT NULL,
    recommended_redline TEXT,
    statute_ref TEXT,
    source_url TEXT,
    source_type TEXT CHECK (source_type IN ('statute', 'case', 'agency', 'template', 'custom')),
    embedding vector(1536) -- Optimized for OpenAI text-embedding-3-small [cite: 191, 263]
);

-- Idempotent column additions for installs predating the 2026-04-27 schema bump.
-- Safe to run repeatedly; no-op when columns already exist.
ALTER TABLE playbook ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE playbook ADD COLUMN IF NOT EXISTS source_type TEXT;

-- 4. LAYER 3: SESSION STORE (TRANSIENT DATA) [cite: 204]
-- Holds temporary analysis results keyed by session ID [cite: 206]
-- NOTE: Reserved schema — no application code currently reads or writes this
-- table. Kept in place so UI/session persistence can be wired up without a
-- follow-up migration. Drop if not used before v1.
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    contract_json JSONB, -- Stores LLM-extracted terms from Step 1 [cite: 208]
    risk_flags JSONB,    -- Stores identified risks and pointers to playbook rows [cite: 209]
    is_active BOOLEAN DEFAULT true
);

-- 5. PLAYBOOK ENTRIES — moved to db/seed_playbook.sql (2026-04-27).
-- Run `psql -U postgres -d freelancer_analyzer -f db/seed_playbook.sql`
-- AFTER this script and BEFORE `python scripts/seed_vectors.py`.
-- Keeping schema (this file) and curated legal data (seed_playbook.sql)
-- in separate files mirrors the rate_benchmarks pattern (seed_rates.sql)
-- and lets the playbook be reviewed / re-seeded without touching schema.

-- 6. STATUTE REFERENCES (Layer 1 grounding for clause_analyzer)
-- clause_type values must match those produced by the playbook / LLM.
INSERT INTO statute_references (clause_type, paragraph, text_excerpt, official_url)
VALUES
    (
        'late_payment_interest',
        '§288 Abs. 2 BGB',
        'Bei Rechtsgeschäften, an denen ein Verbraucher nicht beteiligt ist, beträgt der Zinssatz für Entgeltforderungen neun Prozentpunkte über dem Basiszinssatz.',
        'https://www.gesetze-im-internet.de/bgb/__288.html'
    ),
    (
        'payment_terms',
        '§271a BGB',
        'Eine Vereinbarung, nach der der Gläubiger einer Entgeltforderung die Erfüllung erst nach mehr als 60 Tagen nach Empfang der Gegenleistung verlangen kann, ist nur wirksam, wenn sie ausdrücklich getroffen und im Hinblick auf die Belange des Gläubigers nicht grob unbillig ist.',
        'https://www.gesetze-im-internet.de/bgb/__271a.html'
    ),
    (
        'scheinselbstständigkeit',
        '§7 Abs. 1 SGB IV',
        'Beschäftigung ist die nichtselbständige Arbeit, insbesondere in einem Arbeitsverhältnis. Anhaltspunkte für eine Beschäftigung sind eine Tätigkeit nach Weisungen und eine Eingliederung in die Arbeitsorganisation des Weisungsgebers.',
        'https://www.gesetze-im-internet.de/sgb_4/__7.html'
    ),
    (
        'intellectual_property',
        '§31 UrhG',
        'Der Urheber kann einem anderen das Recht einräumen, das Werk auf einzelne oder alle Nutzungsarten zu nutzen (Nutzungsrecht). Das Nutzungsrecht kann als einfaches oder ausschließliches Recht sowie räumlich, zeitlich oder inhaltlich beschränkt eingeräumt werden.',
        'https://www.gesetze-im-internet.de/urhg/__31.html'
    ),
    (
        'liability',
        '§307 Abs. 1 BGB',
        'Bestimmungen in Allgemeinen Geschäftsbedingungen sind unwirksam, wenn sie den Vertragspartner des Verwenders entgegen den Geboten von Treu und Glauben unangemessen benachteiligen.',
        'https://www.gesetze-im-internet.de/bgb/__307.html'
    )
ON CONFLICT (clause_type, paragraph) DO NOTHING;
