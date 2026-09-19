-- Genetic Profile Database Schema
-- SQLite database for storing genetic profile data

-- App settings: small key/value state that belongs with the database
-- (for example when first-run setup was completed).
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Genes table
CREATE TABLE IF NOT EXISTS genes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_symbol TEXT NOT NULL UNIQUE,
    gene_name TEXT NOT NULL,
    chromosome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SNPs table
CREATE TABLE IF NOT EXISTS snps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rs_number TEXT NOT NULL UNIQUE,
    gene_id INTEGER,
    position TEXT,
    reference_allele TEXT,
    alternate_allele TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Genotypes table (user-specific)
CREATE TABLE IF NOT EXISTS genotypes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    genotype TEXT NOT NULL,
    phenotype TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Trait associations table
CREATE TABLE IF NOT EXISTS trait_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    trait_name TEXT NOT NULL,
    association_direction TEXT, -- e.g., "increased", "decreased", "protective"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Health condition associations table
CREATE TABLE IF NOT EXISTS health_condition_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    condition_name TEXT NOT NULL,
    association_type TEXT, -- e.g., "risk", "protection", "susceptibility"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Citations table (references is a reserved keyword)
CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_number INTEGER UNIQUE,
    authors TEXT,
    year INTEGER,
    title TEXT,
    journal TEXT,
    volume TEXT,
    pages TEXT,
    doi TEXT,
    pubmed_id TEXT,
    url TEXT,
    reference_type TEXT, -- e.g., "journal", "website", "database"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gene-trait-citation mapping (many-to-many)
CREATE TABLE IF NOT EXISTS gene_trait_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trait_association_id INTEGER,
    citation_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trait_association_id) REFERENCES trait_associations(id),
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

-- Gene-health-citation mapping (many-to-many)
CREATE TABLE IF NOT EXISTS gene_health_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    health_condition_association_id INTEGER,
    citation_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (health_condition_association_id) REFERENCES health_condition_associations(id),
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

-- Gene-gene interactions table
CREATE TABLE IF NOT EXISTS gene_gene_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene1_id INTEGER NOT NULL,
    gene2_id INTEGER NOT NULL,
    interaction_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene1_id) REFERENCES genes(id),
    FOREIGN KEY (gene2_id) REFERENCES genes(id)
);

-- Pharmacogenomic data (drug metabolism) tables.
-- Defined here, not only in database_manager._ensure_pharmacogenomic_tables():
-- the indexes at the end of this file reference them, so a fresh database
-- failed schema initialisation before the compatibility code could run.
CREATE TABLE IF NOT EXISTS pharmacogenomic_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    metabolism_status TEXT NOT NULL,
    genotype_phenotype TEXT,
    citation_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id),
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

CREATE TABLE IF NOT EXISTS gene_pharmacogenomic_drugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacogenomic_data_id INTEGER NOT NULL,
    drug_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pharmacogenomic_data_id) REFERENCES pharmacogenomic_data(id)
);

-- Medication guidance as a genetic test report states it: each medication
-- the report lists, in the report's own category (use as directed, moderate
-- or significant gene-drug interaction). Replaced whole per source by
-- scripts/import_pharmacogenomics.py.
CREATE TABLE IF NOT EXISTS medication_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_source_id INTEGER NOT NULL,
    drug_name TEXT NOT NULL,
    brand_name TEXT,
    category TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_source_id) REFERENCES primary_sources(id)
);

-- Research findings table
CREATE TABLE IF NOT EXISTS research_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    finding_title TEXT,
    finding_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Research finding citations mapping
CREATE TABLE IF NOT EXISTS research_finding_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_finding_id INTEGER NOT NULL,
    citation_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (research_finding_id) REFERENCES research_findings(id),
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

-- Database sources table
CREATE TABLE IF NOT EXISTS database_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    source_type TEXT NOT NULL, -- e.g., "SNPedia", "GWAS Catalog", "GTR", "PubMed"
    source_url TEXT,
    key_information TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(id)
);

-- Research references table (for research papers, studies, etc.)
CREATE TABLE IF NOT EXISTS research_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number INTEGER UNIQUE,
    authors TEXT,
    year INTEGER,
    title TEXT,
    journal TEXT,
    volume TEXT,
    pages TEXT,
    doi TEXT,
    pubmed_id TEXT,
    url TEXT,
    reference_type TEXT, -- e.g., "journal", "conference", "preprint", "book"
    abstract TEXT,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Primary sources table (for healthcare data, medical records, test results, etc.)
CREATE TABLE IF NOT EXISTS primary_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL, -- e.g., "health_log", "health_issue", "lab_result", "medical_record", "test_report"
    institution TEXT,
    patient_name TEXT,
    document_date DATE,
    file_path TEXT,
    file_name TEXT,
    extracted_text TEXT,
    metadata TEXT, -- JSON string for additional metadata
    citation_id INTEGER, -- Link to citations table if also added as citation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

-- Primary source findings table (key findings extracted from primary sources)
CREATE TABLE IF NOT EXISTS primary_source_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_source_id INTEGER NOT NULL,
    finding_type TEXT, -- e.g., "diagnosis", "symptom", "test_result", "treatment", "observation", "sick_visit", "routine_visit"
    finding_text TEXT NOT NULL,
    finding_date DATE,
    related_gene_id INTEGER, -- If finding is related to a specific gene
    related_condition TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_source_id) REFERENCES primary_sources(id),
    FOREIGN KEY (related_gene_id) REFERENCES genes(id)
);

-- Health metrics table (vitals, measurements, lab values)
-- CRITICAL: Links to visit_type to ensure averages exclude sick visits
CREATE TABLE IF NOT EXISTS health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_source_id INTEGER NOT NULL,
    finding_id INTEGER, -- Optional link to specific finding
    metric_type TEXT NOT NULL, -- e.g., "temperature", "blood_pressure", "heart_rate", "weight", "bmi", "lab_value"
    metric_name TEXT, -- Specific name if metric_type is "lab_value" (e.g., "CRP", "Glucose")
    metric_value REAL, -- Numeric value
    metric_value_text TEXT, -- Text value for non-numeric (e.g., "NEGATIVE", "POSITIVE")
    unit TEXT, -- e.g., "F", "C", "mmHg", "bpm", "lbs", "kg", "mg/dL"
    collection_date DATE NOT NULL, -- When the metric was collected
    collection_time TIME, -- Optional time of day
    visit_type TEXT, -- "sick_visit", "routine_visit", "emergency_visit", "unknown" - CRITICAL for filtering
    is_abnormal BOOLEAN DEFAULT 0, -- Whether value is outside normal range
    normal_range_min REAL, -- Lower bound of normal range
    normal_range_max REAL, -- Upper bound of normal range
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_source_id) REFERENCES primary_sources(id),
    FOREIGN KEY (finding_id) REFERENCES primary_source_findings(id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_genes_symbol ON genes(gene_symbol);
CREATE INDEX IF NOT EXISTS idx_snps_rs_number ON snps(rs_number);
CREATE INDEX IF NOT EXISTS idx_snps_gene_id ON snps(gene_id);
CREATE INDEX IF NOT EXISTS idx_genotypes_gene_id ON genotypes(gene_id);
CREATE INDEX IF NOT EXISTS idx_trait_associations_gene_id ON trait_associations(gene_id);
CREATE INDEX IF NOT EXISTS idx_health_condition_associations_gene_id ON health_condition_associations(gene_id);
CREATE INDEX IF NOT EXISTS idx_citations_citation_number ON citations(citation_number);
CREATE INDEX IF NOT EXISTS idx_citations_pubmed_id ON citations(pubmed_id);
CREATE INDEX IF NOT EXISTS idx_database_sources_gene_id ON database_sources(gene_id);
CREATE INDEX IF NOT EXISTS idx_research_references_reference_number ON research_references(reference_number);
CREATE INDEX IF NOT EXISTS idx_research_references_pubmed_id ON research_references(pubmed_id);
CREATE INDEX IF NOT EXISTS idx_primary_sources_source_type ON primary_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_primary_sources_document_date ON primary_sources(document_date);
CREATE INDEX IF NOT EXISTS idx_primary_source_findings_source_id ON primary_source_findings(primary_source_id);
CREATE INDEX IF NOT EXISTS idx_primary_source_findings_gene_id ON primary_source_findings(related_gene_id);
CREATE INDEX IF NOT EXISTS idx_pharmacogenomic_data_gene_id ON pharmacogenomic_data(gene_id);
CREATE INDEX IF NOT EXISTS idx_gene_pharmacogenomic_drugs_pg_id ON gene_pharmacogenomic_drugs(pharmacogenomic_data_id);
CREATE INDEX IF NOT EXISTS idx_medication_interactions_source ON medication_interactions(primary_source_id);
CREATE INDEX IF NOT EXISTS idx_primary_source_findings_type ON primary_source_findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_health_metrics_source_id ON health_metrics(primary_source_id);
CREATE INDEX IF NOT EXISTS idx_health_metrics_type ON health_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_health_metrics_date ON health_metrics(collection_date);
CREATE INDEX IF NOT EXISTS idx_health_metrics_visit_type ON health_metrics(visit_type);

-- Views for easier querying

-- View: Genes with their trait associations
CREATE VIEW IF NOT EXISTS v_genes_with_traits AS
SELECT 
    g.id as gene_id,
    g.gene_symbol,
    g.gene_name,
    ta.id as trait_id,
    ta.trait_name,
    ta.association_direction,
    GROUP_CONCAT(c.citation_number) as citation_numbers
FROM genes g
LEFT JOIN trait_associations ta ON g.id = ta.gene_id
LEFT JOIN gene_trait_citations gtc ON ta.id = gtc.trait_association_id
LEFT JOIN citations c ON gtc.citation_id = c.id
GROUP BY g.id, ta.id;

-- View: Genes with their health conditions
CREATE VIEW IF NOT EXISTS v_genes_with_conditions AS
SELECT 
    g.id as gene_id,
    g.gene_symbol,
    g.gene_name,
    hca.id as condition_id,
    hca.condition_name,
    hca.association_type,
    GROUP_CONCAT(c.citation_number) as citation_numbers
FROM genes g
LEFT JOIN health_condition_associations hca ON g.id = hca.gene_id
LEFT JOIN gene_health_citations ghc ON hca.id = ghc.health_condition_association_id
LEFT JOIN citations c ON ghc.citation_id = c.id
GROUP BY g.id, hca.id;

-- View: Gene-gene interactions with gene names
CREATE VIEW IF NOT EXISTS v_gene_interactions AS
SELECT 
    ggi.id as interaction_id,
    g1.id as gene1_id,
    g1.gene_symbol as gene1_symbol,
    g1.gene_name as gene1_name,
    g2.id as gene2_id,
    g2.gene_symbol as gene2_symbol,
    g2.gene_name as gene2_name,
    ggi.interaction_description
FROM gene_gene_interactions ggi
JOIN genes g1 ON ggi.gene1_id = g1.id
JOIN genes g2 ON ggi.gene2_id = g2.id;

-- View: Complete gene summary
CREATE VIEW IF NOT EXISTS v_gene_summary AS
SELECT 
    g.id,
    g.gene_symbol,
    g.gene_name,
    g.chromosome,
    COUNT(DISTINCT ta.id) as trait_count,
    COUNT(DISTINCT hca.id) as condition_count,
    COUNT(DISTINCT s.id) as snp_count,
    COUNT(DISTINCT ggi.id) as interaction_count
FROM genes g
LEFT JOIN trait_associations ta ON g.id = ta.gene_id
LEFT JOIN health_condition_associations hca ON g.id = hca.gene_id
LEFT JOIN snps s ON g.id = s.gene_id
LEFT JOIN gene_gene_interactions ggi ON (g.id = ggi.gene1_id OR g.id = ggi.gene2_id)
GROUP BY g.id;

-- View: Health metrics with routine visits only (for calculating averages)
CREATE VIEW IF NOT EXISTS v_health_metrics_routine_only AS
SELECT 
    hm.*,
    ps.source_name,
    ps.institution
FROM health_metrics hm
JOIN primary_sources ps ON hm.primary_source_id = ps.id
WHERE hm.visit_type IN ('routine_visit', 'checkup', 'well_visit', 'preventive', 'screening', 'baseline', 'follow-up')
   OR (hm.visit_type IS NULL AND hm.finding_id IS NOT NULL 
       AND EXISTS (
           SELECT 1 FROM primary_source_findings psf 
           WHERE psf.id = hm.finding_id 
           AND psf.finding_type IN ('routine_visit', 'checkup', 'well_visit')
       ))
   OR (hm.visit_type IS NULL AND hm.finding_id IS NULL 
       AND NOT EXISTS (
           SELECT 1 FROM primary_source_findings psf 
           WHERE psf.primary_source_id = hm.primary_source_id 
           AND psf.finding_type = 'sick_visit'
           AND psf.finding_date = hm.collection_date
       ));

-- View: Health metrics statistics (routine visits only)
CREATE VIEW IF NOT EXISTS v_health_metrics_stats AS
SELECT 
    metric_type,
    metric_name,
    unit,
    COUNT(*) as measurement_count,
    AVG(metric_value) as average_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    AVG(CASE WHEN is_abnormal = 1 THEN 1.0 ELSE 0.0 END) * 100 as abnormal_percentage
FROM v_health_metrics_routine_only
WHERE metric_value IS NOT NULL
GROUP BY metric_type, metric_name, unit;


-- ============================================================
-- Consumer DNA raw data (23andMe, AncestryDNA, MyHeritage, ...)
-- ============================================================

-- One row per imported file
CREATE TABLE IF NOT EXISTS dna_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    provider TEXT,
    reference_build TEXT,
    variant_count INTEGER NOT NULL DEFAULT 0,
    no_call_count INTEGER NOT NULL DEFAULT 0,
    matched_count INTEGER NOT NULL DEFAULT 0, -- variants in genes the ledger tracks
    primary_source_id INTEGER,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_source_id) REFERENCES primary_sources(id)
);

-- The person's genotype at each variant. Keyed by rs number, not by snps.id:
-- raw data lists hundreds of thousands of variants and only a few are in
-- `snps`. `genotypes` (one phenotype per gene) is untouched by this.
CREATE TABLE IF NOT EXISTS snp_genotypes (
    rsid TEXT PRIMARY KEY,
    chromosome TEXT,
    position TEXT,
    genotype TEXT NOT NULL,
    import_id INTEGER NOT NULL,
    FOREIGN KEY (import_id) REFERENCES dna_imports(id)
);

CREATE INDEX IF NOT EXISTS idx_snp_genotypes_import ON snp_genotypes(import_id);
