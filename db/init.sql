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
CREATE TABLE IF NOT EXISTS playbook (
    id TEXT PRIMARY KEY, -- e.g., 'PB-001'
    clause_type TEXT NOT NULL,
    risk_level TEXT CHECK (risk_level IN ('high', 'medium', 'low')),
    pattern_description TEXT NOT NULL,
    example_risky_wording TEXT,
    legal_reasoning TEXT NOT NULL,
    recommended_redline TEXT,
    statute_ref TEXT,
    embedding vector(1536) -- Optimized for OpenAI text-embedding-3-small [cite: 191, 263]
);

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

-- 5. INITIAL "GOLD" PLAYBOOK DATA [cite: 52, 200]
-- Expert-curated entries based on German statutory law [cite: 35]

-- Late Payment Interest (Medium Risk)
INSERT INTO playbook (id, clause_type, risk_level, pattern_description, legal_reasoning, recommended_redline, statute_ref)
VALUES (
    'PB-001', 
    'late_payment_interest', 
    'medium', 
    'Contract specifies a late-payment interest rate below the B2B statutory default.', 
    '§288 Abs. 2 BGB sets the default statutory interest rate for B2B transactions at 9 percentage points above the base rate. Agreeing to a fixed lower rate (e.g., 4%) reduces legal entitlement.', 
    'Bei Zahlungsverzug werden Verzugszinsen in gesetzlicher Höhe gemäß §288 Abs. 2 BGB berechnet.', 
    '§288 Abs. 2 BGB'
) ON CONFLICT (id) DO NOTHING;

-- Payment Terms (Medium Risk)
INSERT INTO playbook (id, clause_type, risk_level, pattern_description, legal_reasoning, recommended_redline, statute_ref)
VALUES (
    'PB-002', 
    'payment_terms', 
    'medium', 
    'Payment term exceeds 30 days without clear justification.', 
    'Standard industry norms are 14–30 days. While §271a BGB allows up to 60 days in B2B, terms longer than 30 days impact liquidity.', 
    'Invoices shall be settled within 14 calendar days of receipt.', 
    '§271a BGB'
) ON CONFLICT (id) DO NOTHING;

-- Disguised Employment / Scheinselbstständigkeit (High Risk)
INSERT INTO playbook (id, clause_type, risk_level, pattern_description, legal_reasoning, recommended_redline, statute_ref)
VALUES (
    'PB-003', 
    'scheinselbstständigkeit', 
    'high', 
    'Clause requires freelancer to follow daily instructions or work at fixed times.', 
    'Subjecting a freelancer to instructions is a primary indicator of disguised employment under §7 SGB IV, posing social security risks.', 
    'Der Auftragnehmer ist in der Ausgestaltung seiner Tätigkeit frei und unterliegt keinen Weisungen des Auftraggebers.', 
    '§7 SGB IV'
) ON CONFLICT (id) DO NOTHING;

-- IP Assignment (Medium Risk)
INSERT INTO playbook (id, clause_type, risk_level, pattern_description, legal_reasoning, recommended_redline, statute_ref)
VALUES (
    'PB-004', 
    'intellectual_property', 
    'medium', 
    'Contract transfers Background IP or tools developed prior to the project.', 
    'Under UrhG, transferring pre-existing background IP without specific compensation is detrimental. Rights should be limited to project-specific foreground IP.', 
    'The transfer of rights is limited to results created specifically under this agreement. Pre-existing tools and background IP remain the property of the freelancer.', 
    '§31 UrhG'
) ON CONFLICT (id) DO NOTHING;

-- Liability (High Risk)
INSERT INTO playbook (id, clause_type, risk_level, pattern_description, legal_reasoning, recommended_redline, statute_ref)
VALUES (
    'PB-005',
    'liability',
    'high',
    'Contract specifies unlimited liability for simple negligence.',
    'Under German B2B standard terms (§307 BGB), unlimited liability for simple negligence is often invalid. Liability should be capped at contract value or insurance coverage.',
    'Die Haftung für einfache Fahrlässigkeit wird auf die Deckungssumme der Berufshaftpflichtversicherung des Auftragnehmers begrenzt.',
    '§307 BGB'
) ON CONFLICT (id) DO NOTHING;

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