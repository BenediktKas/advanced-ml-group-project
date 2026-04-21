-- db/init.sql

-- 1. Enable the vector extension for the playbook RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Layer 1: Relational Table for Rate Benchmarks
CREATE TABLE rate_benchmarks (
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

-- 3. Layer 1: Relational Table for Statute References
CREATE TABLE statute_references (
    id SERIAL PRIMARY KEY,
    clause_type TEXT NOT NULL,
    paragraph TEXT NOT NULL,
    text_excerpt TEXT NOT NULL,
    official_url TEXT
);

-- 4. Layer 3: Session Store for Analysis Tracking
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    contract_json JSONB, -- Stores LLM-extracted terms
    risk_flags JSONB,    -- Stores identified risks and redlines
    is_active BOOLEAN DEFAULT true
);