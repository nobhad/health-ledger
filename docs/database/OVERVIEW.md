# Database overview

This file explains what the database holds, where it lives and how its tables relate.
Column lists, views and the method reference are in [README.md](README.md).

## Where it is

One SQLite file, `genetic_profile.db`, in the data folder named by
`HEALTH_LEDGER_DATA_DIR` (`config.DB_PATH`). The data folder is outside the
repository, so no record, genotype or result is ever part of a commit. The file is
named after the program this project grew out of. The schema,
`genetic_profile_db_schema.sql`, is applied every time `GeneticProfileDB` connects, so
a new file gets every table and an existing one is left as it is.

The records themselves are the person's own; this documentation says nothing about
their content.

## What is in it

| Group | Tables |
| --- | --- |
| Genes and variants | `genes`, `snps`, `genotypes` |
| Consumer DNA raw data | `dna_imports`, `snp_genotypes` |
| What genes are associated with | `trait_associations`, `health_condition_associations`, `gene_gene_interactions`, `research_findings`, `database_sources` |
| Drug metabolism | `pharmacogenomic_data`, `gene_pharmacogenomic_drugs`, `medication_interactions` |
| Sources of claims | `citations`, `research_references`, and the link tables `gene_trait_citations`, `gene_health_citations`, `research_finding_citations` |
| Saved journal articles | `citation_abstracts`, `citation_excerpts`, `citation_excerpt_specialties` |
| The person's own records | `primary_sources`, `primary_source_findings`, `health_metrics` |
| Settings | `app_settings` (including the patient details) |

## How they relate

```text
genes -< snps, genotypes, trait_associations, health_condition_associations,
         research_findings, database_sources, pharmacogenomic_data
genes -< gene_gene_interactions (as gene1_id and as gene2_id)

trait_associations >-< citations                (gene_trait_citations)
health_condition_associations >-< citations     (gene_health_citations)
research_findings >-< citations                 (research_finding_citations)

citations -- citation_abstracts                 (one abstract per citation)
citations -< citation_excerpts -< citation_excerpt_specialties

pharmacogenomic_data -< gene_pharmacogenomic_drugs
primary_sources -< primary_source_findings, health_metrics, medication_interactions
primary_source_findings -< health_metrics       (optional link)

dna_imports -< snp_genotypes
```

Two things worth knowing:

- `genotypes` holds one phenotype note per gene. `snp_genotypes` holds the person's
  call at every variant a raw-data file listed, keyed by rs number. They are separate.
- An article saved from the References page is a row in `citations`; the abstract and
  quoted passages hang off it.

## How it behaves

- WAL journal mode; query methods return dicts.
- Foreign keys are declared but SQLite does not enforce them (`PRAGMA foreign_keys` is
  never turned on). Deleting a parent row does not fail because children exist; the
  code that removes things (for example `delete_article`) checks for itself.
- Health-metric statistics come from views that leave out sick visits, so an average
  is not skewed by a fever reading. `visit_type` on `health_metrics` drives that.
- The import and extraction scripts that write derived rows delete and re-write them
  per source, so running them twice does not duplicate rows.

## Quick start

```python
from database_manager import GeneticProfileDB

with GeneticProfileDB("example.db") as db:     # omit the argument for the real ledger
    gene_id = db.add_gene("TEST", "Test Gene", "1")
    ref_id = db.add_reference(1, authors="Person, S.", year=2024,
                              title="A test article", reference_type="journal")
    db.add_trait_association(gene_id, "Sample trait", "increased",
                             reference_ids=[ref_id])
    gene = db.get_gene_by_symbol("TEST")
    traits = db.get_trait_associations_for_gene(gene["id"])
```

## Related

- [README.md](README.md): tables, views, every method.
- [../features/DATABASE_QUERIES.md](../features/DATABASE_QUERIES.md): the read methods and views.
- [../PRIVACY.md](../PRIVACY.md): what stays on the computer.
