# Database Queries

`GeneticProfileDB` in `database_manager.py` is the one interface to the SQLite
database. The Flask app, the import scripts and the page generators all use it.
This page covers the read methods and the schema's views. The table definitions
are in `genetic_profile_db_schema.sql`; see
[`../DATABASE_README.md`](../DATABASE_README.md) for the database as a whole.

## Connecting

```python
from database_manager import GeneticProfileDB

with GeneticProfileDB() as db:
    genes = db.get_all_genes()
```

With no argument the class opens `config.DB_PATH`: `genetic_profile.db` under
`HEALTH_LEDGER_DATA_DIR`, or the file named by `HEALTH_LEDGER_DB_PATH` if that
is set. Pass a path to open another file. Opening a connection turns on WAL
mode, returns rows as `sqlite3.Row`, and runs the schema file
(`CREATE ... IF NOT EXISTS`, so an existing database is not changed). The
methods below convert rows to plain dictionaries. `close()` or the `with`
block ends the connection.

In the Flask app, `get_db()` in `app.py` keeps one connection per thread and
`close_db` closes it when the app context ends.

## Read methods

Genes:

- `get_all_genes()` returns every row of `genes`, ordered by `gene_symbol`.
- `get_gene_by_symbol(symbol)` returns one `genes` row, or `None`.
- `get_snps_for_gene(gene_id)` returns the gene's `snps` rows.
- `get_gene_summary(symbol)` and `get_all_gene_summaries()` read the
  `v_gene_summary` view (counts of traits, conditions, SNPs and interactions).

Traits and conditions:

- `get_trait_associations_for_gene(gene_id)` returns `id`, `gene_id`,
  `trait_name`, `association_direction`, `notes` and `citation_numbers`
  (a comma-separated string).
- `get_health_conditions_for_gene(gene_id)` returns the same shape with
  `condition_name` and `association_type`.
- `search_traits(term)` and `search_health_conditions(term)` match the name
  with `LIKE '%term%'` and return the association rows with `gene_symbol` and
  `gene_name`.
- `get_genes_by_trait(name)` and `get_genes_by_condition(name)` return gene
  rows with the matching trait or condition and its direction or type.
- `get_genes_with_trait(keyword)` and `get_genes_with_condition(keyword)`
  return one row per gene with `id`, `gene_symbol`, `gene_name` and
  `matching_traits` or `matching_conditions` (comma-separated).

Interactions:

- `get_interacting_genes(symbol)` returns `interacting_gene_symbol`,
  `interacting_gene_name` and `interaction_description`, whichever side of the
  pair the gene is on. It returns `[]` for an unknown symbol.

Pharmacogenomics:

- `get_pharmacogenomic_data_for_gene(gene_id)` returns one row
  (`metabolism_status`, `genotype_phenotype`, `citation_id`) or `None`;
  `affected_medications` is a list of drug names.
- `get_all_pharmacogenomic()` returns one such row per gene, with
  `gene_symbol` and `gene_name`.
- `get_medications_for_gene(gene_id)` returns a sorted list of drug names.
- `search_pharmacogenomic(medication)` returns the genes whose drug list
  matches the medication name.
- `get_medication_interactions(primary_source_id=None)` returns the
  medication guidance rows imported from a genetic test report.

References:

- `get_references_for_gene(gene_id)` returns the `citations` rows linked to
  the gene through its traits, conditions or research findings.
- `get_all_references()` returns every `citations` row by `citation_number`.

Methods that start `add_`, `save_`, `replace_`, `set_` or `delete_` write to
the database. The full list is in `database_manager.py`.

## Views

The schema defines six views:

| View | One row per | Columns |
| --- | --- | --- |
| `v_genes_with_traits` | gene and trait | `gene_id`, `gene_symbol`, `gene_name`, `trait_id`, `trait_name`, `association_direction`, `citation_numbers` |
| `v_genes_with_conditions` | gene and condition | `gene_id`, `gene_symbol`, `gene_name`, `condition_id`, `condition_name`, `association_type`, `citation_numbers` |
| `v_gene_interactions` | interaction | `interaction_id`, `gene1_id`, `gene1_symbol`, `gene1_name`, `gene2_id`, `gene2_symbol`, `gene2_name`, `interaction_description` |
| `v_gene_summary` | gene | `id`, `gene_symbol`, `gene_name`, `chromosome`, `trait_count`, `condition_count`, `snp_count`, `interaction_count` |
| `v_health_metrics_routine_only` | metric from a routine visit | every `health_metrics` column plus `source_name`, `institution` |
| `v_health_metrics_stats` | metric type, name and unit | `metric_type`, `metric_name`, `unit`, `measurement_count`, `average_value`, `min_value`, `max_value`, `abnormal_percentage` |

```python
with GeneticProfileDB() as db:
    rows = db.conn.execute(
        "SELECT * FROM v_genes_with_traits WHERE gene_symbol = ?", ("GENE1",)
    ).fetchall()
```

There is no pharmacogenomic view. Query `pharmacogenomic_data` and
`gene_pharmacogenomic_drugs`, or use the methods above. Views are ordinary
saved SELECT statements, not stored results, so they are not faster than the
same JOINs written out.

## Examples

All genes tied to a condition:

```python
with GeneticProfileDB() as db:
    for gene in db.get_genes_with_condition("sample condition"):
        print(gene["gene_symbol"], gene["matching_conditions"])
```

Everything stored for one gene:

```python
with GeneticProfileDB() as db:
    gene = db.get_gene_by_symbol("GENE1")
    if gene:
        traits = db.get_trait_associations_for_gene(gene["id"])
        conditions = db.get_health_conditions_for_gene(gene["id"])
        interactions = db.get_interacting_genes("GENE1")
        pharmacogenomic = db.get_pharmacogenomic_data_for_gene(gene["id"])
```

`scripts/query_examples.py` runs a longer set of these queries against your
database and prints the results (`./venv/bin/python scripts/query_examples.py`).

## Errors

Methods let `sqlite3.Error` propagate. An `OperationalError` usually means the
file is locked by another process or cannot be opened; an `IntegrityError`
means a write broke a UNIQUE or FOREIGN KEY constraint. `delete_article` raises
`ArticleInUse` when something else in the ledger cites the article.

## Checking the database

```python
with GeneticProfileDB() as db:
    print(db.conn.execute("PRAGMA integrity_check").fetchone()[0])  # "ok"
    for col in db.conn.execute("PRAGMA table_info(genes)"):
        print(col["name"], col["type"])
```
