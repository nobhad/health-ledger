# Citation Management

How references are stored, and which tools put them there.

## In the app

The only way to add a journal reference in the running app is the
**References** page: you press **Look up**, the app asks Europe PMC, and you
save what you want. That is described in
[REFERENCES.md](REFERENCES.md), including exactly what is sent. No other page
and no route in `app.py` looks anything up on the internet.

## Where references are stored

Each reference is a row in `citations` (see `genetic_profile_db_schema.sql`).
`citation_number` is unique. The other columns are `authors`, `year`,
`title`, `journal`, `volume`, `pages`, `doi`, `pubmed_id`, `url` and
`reference_type`.

- `citation_abstracts`, `citation_excerpts` and `citation_excerpt_specialties`
  hang an abstract, selected passages and the specialists each passage is for
  off a `citations` row. The References page writes them.
- `gene_trait_citations`, `gene_health_citations` and
  `research_finding_citations` link a citation to a trait association, a
  health-condition association or a research finding.
- `research_references` is a second table with the same bibliographic columns
  plus `abstract` and `keywords`.

## From Python

`database_manager.GeneticProfileDB` has the write and read methods:
`add_reference`, `add_reference_if_not_exists`, `check_citation_exists`,
`add_research_reference`, `add_research_reference_if_not_exists`,
`get_all_references`, `get_references_for_gene` and
`get_all_research_references`. `add_trait_association`,
`add_health_condition_association` and `add_research_finding` take a
`reference_ids` list to link citations as they are created. Read the
signatures in `database_manager.py`; they are not repeated here.

`add_reference` accepts a `pdf_file_path`, but writes it only when the
`citations` table has a `pdf_file_path` column. The schema does not create
that column, so on a fresh database the argument is ignored.

## Terminal tools

These live in `scripts/` and are run by hand. No route in `app.py` calls them
and the test suite does not cover them.

| Script | What it is |
| --- | --- |
| `fetch_from_pubmed.py` | PubMed through NCBI Entrez; takes `--gene NAME` or `--all`, and `--email` |
| `fetch_from_gwas.py` | GWAS Catalog; takes `--gene NAME` or `--all` |
| `fetch_from_gtr.py` | Genetic Testing Registry; takes `--gene NAME` or `--all` |
| `fetch_from_snpedia.py` | SNPedia; takes `--rs RSID` or `--all` |
| `enrich_database_from_sources.py` | Runs the fetchers above; takes `--gene`, `--all`, `--source` and `--email` |
| `download_research_papers.py` | Downloads papers as PDFs; takes `--json`, `--pubmed-id` and `--doi` |

They need `biopython`, which is in `requirements-extras.txt`. The packaged
app leaves it out (`Bio` is in the excludes of `packaging/health_ledger.spec`),
so these scripts work only from a source checkout with the extras installed.
They open the configured database (`config.DB_PATH`, under
`HEALTH_LEDGER_DATA_DIR`). Unlike the References page, they query those sites
for every gene or SNP in the database when given `--all`, not on a button
press, so read a script before running it. None of them has a `--dry-run`.

`citation_overhaul.py` is left over from the earlier program. It reads a
fixed markdown file name from the current directory, which the app does not
produce, and takes no arguments.

An older write-up of the overhaul is in
[../archive/CITATION_OVERHAUL_SUMMARY.md](../archive/CITATION_OVERHAUL_SUMMARY.md).
