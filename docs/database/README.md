# Database reference

This file is the reference for the SQLite database: every table, index and view in
`genetic_profile_db_schema.sql`, and how to use the `GeneticProfileDB` class in
`database_manager.py`. For what the tables are for and how they relate, see
[OVERVIEW.md](OVERVIEW.md). When this file and the code disagree, the code is right.

## Opening the database

```python
from database_manager import GeneticProfileDB

db = GeneticProfileDB()                    # opens config.DB_PATH
db = GeneticProfileDB("/path/to/test.db")  # or any file

with GeneticProfileDB() as db:             # closes on exit
    genes = db.get_all_genes()
```

- With no argument the class opens `config.DB_PATH`: `genetic_profile.db` inside the
  data folder (`HEALTH_LEDGER_DATA_DIR`), or the file named by `HEALTH_LEDGER_DB_PATH`
  when that is set. The data folder is outside the repository.
- On every connection the class runs `genetic_profile_db_schema.sql`
  (`config.DB_SCHEMA_PATH`). Everything in it is `CREATE ... IF NOT EXISTS`, so an
  existing database is left alone and a new file gets all tables.
- The connection uses WAL journal mode and `sqlite3.Row` rows. Query methods return
  plain dicts, or lists of dicts.
- `PRAGMA foreign_keys` is never switched on, so SQLite does not enforce the
  `FOREIGN KEY` clauses below. They document intent only.
- No trigger or method updates `updated_at` after a row is inserted.
- Always call `close()` (or use `with`).

## Tables

Types and constraints are as written in the schema. `FK` means a declared foreign key.

### app_settings

Small key/value state kept with the database. The patient details are stored here under
keys `patient.<field>`.

| Column | Type | Constraints |
| --- | --- | --- |
| `key` | TEXT | PRIMARY KEY |
| `value` | TEXT | |

### genes

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_symbol` | TEXT | NOT NULL, UNIQUE |
| `gene_name` | TEXT | NOT NULL |
| `chromosome` | TEXT | |
| `created_at`, `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### snps

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `rs_number` | TEXT | NOT NULL, UNIQUE |
| `gene_id` | INTEGER | FK genes(id); nullable |
| `position`, `reference_allele`, `alternate_allele` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### genotypes

One phenotype note per gene. Not the same as `snp_genotypes`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `genotype` | TEXT | NOT NULL |
| `phenotype` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### dna_imports

One row per consumer raw-DNA file imported (see `raw_dna.py`).

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `file_name` | TEXT | NOT NULL |
| `provider`, `reference_build` | TEXT | |
| `variant_count`, `no_call_count`, `matched_count` | INTEGER | NOT NULL, DEFAULT 0 (`matched_count` is variants in genes the ledger tracks) |
| `primary_source_id` | INTEGER | FK primary_sources(id) |
| `imported_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### snp_genotypes

The person's genotype at each variant a raw-data file called. Keyed by rs number, not
by `snps.id`, because a raw file lists far more variants than `snps` holds. Index:
`idx_snp_genotypes_import` on `import_id`.

| Column | Type | Constraints |
| --- | --- | --- |
| `rsid` | TEXT | PRIMARY KEY |
| `chromosome`, `position` | TEXT | |
| `genotype` | TEXT | NOT NULL |
| `import_id` | INTEGER | NOT NULL, FK dna_imports(id) |

### trait_associations

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `trait_name` | TEXT | NOT NULL |
| `association_direction` | TEXT | for example "increased", "decreased", "protective" |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### health_condition_associations

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `condition_name` | TEXT | NOT NULL |
| `association_type` | TEXT | for example "risk", "protection", "susceptibility" |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### citations

The table is called `citations` because `references` is a reserved word. Saved journal
articles are rows here too.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `citation_number` | INTEGER | UNIQUE |
| `authors`, `title`, `journal`, `volume`, `pages`, `doi`, `pubmed_id`, `url` | TEXT | |
| `year` | INTEGER | |
| `reference_type` | TEXT | for example "journal", "website", "database" |
| `created_at`, `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `idx_citations_citation_number`, `idx_citations_pubmed_id`.

**There is no `pdf_file_path` column in the schema.** A one-off script
(`scripts/migrate_schema_for_research_papers.py`) adds it to databases that ran it.
`add_reference` checks `PRAGMA table_info(citations)` and writes `pdf_file_path` only
when the column exists; otherwise the argument is silently dropped. Do not select or
insert that column in code that has to work on a fresh database.

### citation_abstracts

| Column | Type | Constraints |
| --- | --- | --- |
| `citation_id` | INTEGER | PRIMARY KEY, FK citations(id) |
| `abstract` | TEXT | NOT NULL |
| `fetched_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### citation_excerpts

Passages selected from an abstract. Index: `idx_citation_excerpts_citation`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `citation_id` | INTEGER | NOT NULL, FK citations(id) |
| `excerpt_text` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### citation_excerpt_specialties

The specialists an excerpt is for. Index: `idx_citation_excerpt_specialties_specialty`.

| Column | Type | Constraints |
| --- | --- | --- |
| `excerpt_id` | INTEGER | NOT NULL, FK citation_excerpts(id) |
| `specialty` | TEXT | NOT NULL |

`UNIQUE (excerpt_id, specialty)`.

### gene_trait_citations

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `trait_association_id` | INTEGER | FK trait_associations(id); nullable |
| `citation_id` | INTEGER | NOT NULL, FK citations(id) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### gene_health_citations

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `health_condition_association_id` | INTEGER | FK health_condition_associations(id); nullable |
| `citation_id` | INTEGER | NOT NULL, FK citations(id) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### gene_gene_interactions

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene1_id`, `gene2_id` | INTEGER | NOT NULL, FK genes(id) |
| `interaction_description` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### pharmacogenomic_data

Nothing makes `gene_id` unique; `replace_pharmacogenomic_data_for_gene` keeps it to one
row per gene.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `metabolism_status` | TEXT | NOT NULL |
| `genotype_phenotype` | TEXT | |
| `citation_id` | INTEGER | FK citations(id) |
| `created_at`, `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Index: `idx_pharmacogenomic_data_gene_id`.

### gene_pharmacogenomic_drugs

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `pharmacogenomic_data_id` | INTEGER | NOT NULL, FK pharmacogenomic_data(id) |
| `drug_name` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Index: `idx_gene_pharmacogenomic_drugs_pg_id`.

### medication_interactions

A genetic test report's own medication guidance, replaced whole per source by
`scripts/import_pharmacogenomics.py`. Index: `idx_medication_interactions_source`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `primary_source_id` | INTEGER | NOT NULL, FK primary_sources(id) |
| `drug_name` | TEXT | NOT NULL |
| `brand_name`, `notes` | TEXT | |
| `category` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### research_findings

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `finding_title`, `finding_text` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

`finding_text` is nullable in the schema; `add_research_finding` always supplies it.

### research_finding_citations

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `research_finding_id` | INTEGER | NOT NULL, FK research_findings(id) |
| `citation_id` | INTEGER | NOT NULL, FK citations(id) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### database_sources

Index: `idx_database_sources_gene_id`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `gene_id` | INTEGER | NOT NULL, FK genes(id) |
| `source_type` | TEXT | NOT NULL (for example "SNPedia", "GWAS Catalog", "GTR", "PubMed") |
| `source_url`, `key_information` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### research_references

A second reference table, separate from `citations`. Indexes:
`idx_research_references_reference_number`, `idx_research_references_pubmed_id`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `reference_number` | INTEGER | UNIQUE |
| `authors`, `title`, `journal`, `volume`, `pages`, `doi`, `pubmed_id`, `url`, `reference_type`, `abstract`, `keywords` | TEXT | |
| `year` | INTEGER | |
| `created_at`, `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Like `citations`, this table has no `pdf_file_path` column in the schema, but
`add_research_reference` always includes it in its INSERT, with no column check. On a
database that has not had the migration script run, it raises `sqlite3.OperationalError`.

### primary_sources

Imported documents. Indexes: `idx_primary_sources_source_type`,
`idx_primary_sources_document_date`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `source_name` | TEXT | NOT NULL |
| `source_type` | TEXT | NOT NULL (for example "health_log", "lab_result", "medical_record", "test_report") |
| `institution`, `patient_name`, `file_path`, `file_name`, `extracted_text` | TEXT | |
| `document_date` | DATE | |
| `metadata` | TEXT | JSON string |
| `citation_id` | INTEGER | FK citations(id) |
| `created_at`, `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### primary_source_findings

Indexes: `idx_primary_source_findings_source_id`, `idx_primary_source_findings_gene_id`
(on `related_gene_id`), `idx_primary_source_findings_type`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `primary_source_id` | INTEGER | NOT NULL, FK primary_sources(id) |
| `finding_type` | TEXT | nullable (for example "diagnosis", "test_result", "medication", "sick_visit", "routine_visit") |
| `finding_text` | TEXT | NOT NULL |
| `finding_date` | DATE | |
| `related_gene_id` | INTEGER | FK genes(id) |
| `related_condition`, `notes` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### health_metrics

Indexes: `idx_health_metrics_source_id`, `idx_health_metrics_type`,
`idx_health_metrics_date`, `idx_health_metrics_visit_type`.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `primary_source_id` | INTEGER | NOT NULL, FK primary_sources(id) |
| `finding_id` | INTEGER | FK primary_source_findings(id) |
| `metric_type` | TEXT | NOT NULL (for example "temperature", "blood_pressure", "lab_value") |
| `metric_name` | TEXT | the analyte name when `metric_type` is "lab_value" |
| `metric_value` | REAL | |
| `metric_value_text` | TEXT | for non-numeric results |
| `unit` | TEXT | |
| `collection_date` | DATE | NOT NULL |
| `collection_time` | TIME | |
| `visit_type` | TEXT | "sick_visit", "routine_visit", "emergency_visit", "unknown"; the statistics views filter on it |
| `is_abnormal` | BOOLEAN | DEFAULT 0 |
| `normal_range_min`, `normal_range_max` | REAL | |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### Other indexes

`idx_genes_symbol`, `idx_snps_rs_number`, `idx_snps_gene_id`, `idx_genotypes_gene_id`,
`idx_trait_associations_gene_id`, `idx_health_condition_associations_gene_id`.

## Views

| View | Columns |
| --- | --- |
| `v_genes_with_traits` | `gene_id`, `gene_symbol`, `gene_name`, `trait_id`, `trait_name`, `association_direction`, `citation_numbers` (comma-joined). One row per gene and trait; genes with no trait appear once with NULLs. |
| `v_genes_with_conditions` | The same for conditions: `condition_id`, `condition_name`, `association_type`, `citation_numbers`. |
| `v_gene_interactions` | `interaction_id`, `gene1_id`, `gene1_symbol`, `gene1_name`, `gene2_id`, `gene2_symbol`, `gene2_name`, `interaction_description` |
| `v_gene_summary` | `id`, `gene_symbol`, `gene_name`, `chromosome`, `trait_count`, `condition_count`, `snp_count`, `interaction_count` |
| `v_health_metrics_routine_only` | Every `health_metrics` column plus `source_name` and `institution`, limited to routine readings: a routine-type `visit_type`; or no `visit_type` and a routine linked finding; or no `visit_type`, no finding, and no sick-visit finding from the same source on that date. The list of accepted `visit_type` values is in the schema. |
| `v_health_metrics_stats` | `metric_type`, `metric_name`, `unit`, `measurement_count`, `average_value`, `min_value`, `max_value`, `abnormal_percentage`, over the routine-only view and non-null values |

`sqlite_sequence` is SQLite's own table for AUTOINCREMENT.

## Python API

All methods are on `GeneticProfileDB`. Writes commit immediately. Parameters are
listed in order; "=None" means optional. Examples use made-up data.

### Genes, variants, genotypes

| Method | Returns |
| --- | --- |
| `add_gene(gene_symbol, gene_name, chromosome=None)` | new id. Raises `sqlite3.IntegrityError` for a duplicate symbol. |
| `get_gene_by_symbol(gene_symbol)` | dict or None |
| `get_all_genes()` | list, ordered by symbol |
| `add_snp(rs_number, gene_id, position=None, reference_allele=None, alternate_allele=None)` | new id |
| `ensure_snp(rs_number, gene_id)` | id of the existing row, or of a new one |
| `get_snps_for_gene(gene_id)` | list, ordered by rs number |
| `add_genotype(gene_id, genotype, phenotype=None)` | new id |
| `get_genotypes_for_gene(gene_id)` | list |
| `get_variant_genotypes_for_gene(gene_symbol)` | list of `{rsid, genotype, description}`: the well-known variants for that gene (from `variant_reference.py`) that a DNA import called. Empty when there are none. |

```python
gene_id = db.add_gene("TEST", "Test Gene", "1")
db.add_snp("rs0000001", gene_id)
db.add_genotype(gene_id, "A/G", "Heterozygous")
gene = db.get_gene_by_symbol("TEST")
```

### Raw DNA imports

| Method | Returns |
| --- | --- |
| `add_dna_import(file_name, provider, build, variant_count, no_call_count, matched_count, primary_source_id=None)` | new id. `provider` and `build` are required positionals (may be None). |
| `replace_snp_genotypes(import_id, rows)` | number written. `rows` is an iterable of `(rsid, chromosome, position, genotype)`; an rs number already on file is replaced. |
| `get_dna_imports()` | list, newest first |
| `count_snp_genotypes()` | int |
| `get_snp_genotypes(rsids)` | `{rsid: genotype}` for those on file |

```python
import_id = db.add_dna_import("sample.txt", "Sample Provider", "GRCh37", 1, 0, 0)
db.replace_snp_genotypes(import_id, [("rs0000001", "1", "1000", "AG")])
db.get_snp_genotypes(["rs0000001"])   # {'rs0000001': 'AG'}
```

### Citations

| Method | Returns |
| --- | --- |
| `check_citation_exists(pubmed_id=None, doi=None, citation_number=None)` | the first match, tried in that order, or None |
| `add_reference(citation_number, authors=None, year=None, title=None, journal=None, volume=None, pages=None, doi=None, pubmed_id=None, url=None, reference_type="journal", pdf_file_path=None)` | new id. See the `pdf_file_path` note under `citations`. |
| `add_reference_if_not_exists(...)` | same arguments; the id of the existing match instead of adding a duplicate (a unique-constraint clash also returns the existing id) |
| `get_all_references()` | all citations, by citation number |
| `get_references_for_gene(gene_id)` | citations reached through the gene's traits, conditions and research findings |

```python
ref_id = db.add_reference(1, authors="Person, S.", year=2024,
                          title="A test article", reference_type="journal")
```

### Saved journal articles: abstracts, excerpts, specialties

These back the References page.

| Method | Behaviour |
| --- | --- |
| `save_article(article)` | `article` is a dict with `title` (required) and optional `authors`, `journal`, `year`, `doi`, `pubmed_id`, `url`, `abstract`. Returns the citation id. If the PubMed id or DOI is already a citation, that id is returned and nothing is added; the abstract is stored only if that citation had none. The new `citation_number` is the highest in use plus one. |
| `list_articles()` | citations whose `reference_type` is not `primary_source`, each with `has_abstract` (bool) and `excerpt_count` (int) |
| `get_article(citation_id)` | the citation row plus `abstract` (None if none) and `excerpts`, a list of `{id, excerpt_text, specialties}`. None if there is no such citation. |
| `set_article_abstract(citation_id, abstract)` | stores or replaces the abstract |
| `add_excerpt(citation_id, text)` | returns the new excerpt id. The text, whitespace collapsed, must appear in the stored abstract (also collapsed); the collapsed text is stored. Raises `ValueError` when there is no abstract, the text is empty, or it is not in the abstract. |
| `set_excerpt_specialties(excerpt_id, specialties)` | replaces the excerpt's specialty set |
| `get_excerpt_article_id(excerpt_id)` | the citation id, or None |
| `delete_excerpt(excerpt_id)` | removes it and its specialties; returns the citation id, or None if there was no such excerpt |
| `delete_article(citation_id)` | removes the citation, abstract and excerpts. Raises `ArticleInUse` (defined in `database_manager.py`) when `gene_trait_citations`, `gene_health_citations`, `research_finding_citations`, `primary_sources` or `pharmacogenomic_data` refer to it; nothing is removed then. |
| `get_excerpts_for_specialty(specialty)` | list of dicts with `excerpt_text`, `title`, `authors`, `journal`, `year`, `doi`, `pubmed_id`, `url`, ordered by article then excerpt |

```python
from database_manager import ArticleInUse

citation_id = db.save_article({
    "title": "A test article",
    "authors": "Person, S.",
    "year": 2024,
    "abstract": "Sample abstract text. A second sentence.",
})
excerpt_id = db.add_excerpt(citation_id, "A second sentence.")
db.set_excerpt_specialties(excerpt_id, ["Cardiology"])
db.get_excerpts_for_specialty("Cardiology")
try:
    db.delete_article(citation_id)
except ArticleInUse:
    pass
```

### Associations, interactions, findings, sources

| Method | Returns |
| --- | --- |
| `add_trait_association(gene_id, trait_name, association_direction=None, notes=None, reference_ids=None)` | new id; `reference_ids` are citation ids, linked through `gene_trait_citations` |
| `add_health_condition_association(gene_id, condition_name, association_type=None, notes=None, reference_ids=None)` | new id; links through `gene_health_citations` |
| `add_gene_gene_interaction(gene1_id, gene2_id, interaction_description)` | new id |
| `add_research_finding(gene_id, finding_title, finding_text, reference_ids=None)` | new id; links through `research_finding_citations` |
| `add_database_source(gene_id, source_type, source_url=None, key_information=None)` | new id |
| `get_trait_associations_for_gene(gene_id)` | list with `citation_numbers`, by trait name |
| `get_health_conditions_for_gene(gene_id)` | list with `citation_numbers`, by condition name |
| `get_research_findings_for_gene(gene_id)` | list with `citation_numbers` |
| `get_database_sources_for_gene(gene_id)` | list |
| `search_traits(search_term)`, `search_health_conditions(search_term)` | `LIKE %term%` matches, with `gene_symbol` and `gene_name` |
| `get_genes_by_trait(trait_name)`, `get_genes_by_condition(condition_name)` | genes with a matching trait or condition (`LIKE`) |
| `get_genes_with_trait(trait_keyword)`, `get_genes_with_condition(condition_keyword)` | genes with `matching_traits` / `matching_conditions` |
| `get_interacting_genes(gene_symbol)` | list of `{interacting_gene_symbol, interacting_gene_name, interaction_description}`; empty for an unknown gene |
| `get_gene_summary(gene_symbol)` | a `v_gene_summary` row or None |
| `get_all_gene_summaries()` | all of them, by symbol |

```python
db.add_trait_association(gene_id, "Sample trait", "increased", reference_ids=[ref_id])
for trait in db.get_trait_associations_for_gene(gene_id):
    print(trait["trait_name"], trait["citation_numbers"])
```

### Research references

`check_research_reference_exists(pubmed_id=None, doi=None, reference_number=None)`,
`add_research_reference(reference_number, authors=None, year=None, title=None,
journal=None, volume=None, pages=None, doi=None, pubmed_id=None, url=None,
reference_type="journal", abstract=None, keywords=None, pdf_file_path=None)` (see the
warning under `research_references`), `add_research_reference_if_not_exists(...)` and
`get_all_research_references()` mirror the citation methods.

### Primary sources and findings

| Method | Returns |
| --- | --- |
| `add_primary_source(source_name, source_type, institution=None, patient_name=None, document_date=None, file_path=None, file_name=None, extracted_text=None, metadata=None, citation_id=None)` | new id |
| `update_primary_source(source_id, **fields)` | None. Only `source_name`, `source_type`, `institution`, `patient_name`, `document_date`, `file_path`, `file_name`, `extracted_text` and `metadata` are applied; other keys are ignored. |
| `get_primary_source_by_file_name(file_name)` | the oldest source with that file name, or None |
| `get_all_primary_sources()` | newest document date first |
| `get_primary_sources_by_type(source_type)` | list |
| `get_primary_sources_by_date_range(start_date=None, end_date=None)` | list; with neither, all sources |
| `search_primary_sources(query)` | matches in name, extracted text, institution or finding text |
| `get_primary_source_with_findings(source_id)` | source dict with `findings`, or None |
| `get_primary_source_text(source_id)` | extracted text, or None |
| `add_primary_source_finding(primary_source_id, finding_text, finding_type=None, finding_date=None, related_gene_id=None, related_condition=None, notes=None)` | new id. Note `finding_text` comes before `finding_type`. |
| `add_primary_source_finding_if_not_exists(...)` | same arguments; None when a finding with the same source, text, type and date exists |
| `get_primary_source_findings(primary_source_id)` | list with `gene_symbol` and `gene_name` |
| `get_patient_name()` | the most common `patient_name` across sources, or None |
| `get_genetic_test_info()` | `{date, provider, file_path, source_name, file_name}` from the newest `test_report` source (preferring one whose name or institution mentions genetic testing), or None |
| `get_current_medications()` | from findings of type `medication`: `{medication_name, start_date, details, source_date}` |

```python
source_id = db.add_primary_source("Sample lab report", "lab_result",
                                  institution="Sample Clinic",
                                  document_date="2025-01-15")
db.add_primary_source_finding(source_id, "Sample finding", finding_type="observation")
```

### Patient details

`get_patient_details()` returns a dict of the saved fields. `save_patient_details(details)`
replaces them and returns what is saved. The fields are listed in
`GeneticProfileDB.PATIENT_DETAIL_FIELDS`; unknown keys are ignored, values are trimmed
and cut to `PATIENT_DETAIL_MAX_LENGTH`, and a blank value deletes the field. They live
in `app_settings`.

```python
db.save_patient_details({"full_name": "Sample Person"})
```

### Health metrics

| Method | Returns |
| --- | --- |
| `add_health_metric(primary_source_id, metric_type, collection_date, metric_value=None, metric_value_text=None, metric_name=None, unit=None, collection_time=None, visit_type=None, is_abnormal=False, normal_range_min=None, normal_range_max=None, finding_id=None, notes=None)` | new id. `collection_date` is the third positional. |
| `delete_health_metrics_for_source(primary_source_id)` | number of rows deleted |
| `get_health_metrics(metric_type=None, visit_type=None, routine_only=False, start_date=None, end_date=None)` | newest first. `routine_only=True` reads the routine view and ignores `visit_type`. |
| `get_health_metrics_stats(metric_type=None)` | rows of `v_health_metrics_stats` |
| `get_health_metrics_category_averages()` | per `metric_type` and `unit`, routine readings only, lab values excluded; includes `average_in_normal_range` (True, False or None) |

```python
db.add_health_metric(source_id, "heart_rate", "2025-01-15", metric_value=70.0,
                     unit="bpm", visit_type="routine_visit")
```

### Pharmacogenomics

| Method | Returns |
| --- | --- |
| `add_pharmacogenomic_data(gene_id, metabolism_status, genotype_phenotype=None, citation_id=None)` | new id |
| `add_gene_pharmacogenomic_drug(pharmacogenomic_data_id, drug_name)` | new id |
| `replace_pharmacogenomic_data_for_gene(gene_id, metabolism_status, genotype_phenotype=None, drugs=None)` | id of the new record; deletes the gene's earlier record and drugs first, so repeat imports leave one row |
| `replace_medication_interactions_for_source(primary_source_id, interactions)` | rows written. Each item is a dict with `drug_name`, `category`, and optional `brand_name`, `notes`. |
| `get_medication_interactions(primary_source_id=None)` | rows with `source_name` and `document_date`; categories "significant", then "moderate", then others, then by drug name |
| `get_pharmacogenomic_data_for_gene(gene_id)` | dict with `affected_medications` (a list), or None |
| `get_all_pharmacogenomic()` | one dict per gene that has a record, with `gene_symbol`, `gene_name`, `affected_medications` |
| `get_medications_for_gene(gene_id)` | sorted list of drug names |
| `search_pharmacogenomic(medication_name)` | rows for genes affecting a drug matching `LIKE %name%` |

`close()` closes the connection; `__enter__` and `__exit__` make `with` work.

## Queries and maintenance

- Example queries: `scripts/query_examples.py` (`example_queries()` prints them,
  `export_to_json(filename)` writes genes with their associations). It imports
  `database_manager` without adjusting `sys.path`, so run it with the repository root
  on `PYTHONPATH`.
- Backup and export: `scripts/backup_database.py` takes `--backup` (timestamped copy in
  `config.BACKUPS_DIR`), `--export PATH`, `--json PATH` and `--list`.
- Plain SQLite tools work on the file: `PRAGMA integrity_check;` and
  `PRAGMA foreign_key_check;` (the second reports violations even though they are not
  enforced on write).
