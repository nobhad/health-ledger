# Architecture

Health Ledger is a local, single-user Flask application over one SQLite
database. The browser talks to a server on `127.0.0.1`; the server reads and
writes files and the database in a data folder the person chose. There is no
account, no remote database and no background job.

## Entry points

| Entry | What it is |
| --- | --- |
| `app.py` | The Flask app: every page and API route. `python3 app.py [port]` serves it on `127.0.0.1`, default port 5001. |
| `desktop.py` | What the packaged `.app` and `.exe` run. Serves the same Flask app (with `waitress`, falling back to Werkzeug), picks a free port, opens a browser and adds a menu-bar or tray icon with Quit. |
| `start.sh`, `start.bat`, `Health Ledger.command` | Launchers for a checkout: create `./venv`, install `requirements.txt`, run `app.py`, open a browser. |

## Modules

Everything at the project root is a flat module; `app.py` imports them.

| Module | Responsibility |
| --- | --- |
| `config.py` | Version, host and port, and every path. Splits read-only resources (`BASE_DIR`) from settings (`CONFIG_DIR`, `.env`) and from the person's records (`DATA_ROOT`). Sets up logging. |
| `database_manager.py` | `GeneticProfileDB`: opens the database (WAL mode, `row_factory=sqlite3.Row`), applies the schema, and holds the queries and writes. |
| `genetic_profile_db_schema.sql` | Tables, indexes and views. Applied on every connect with `CREATE ... IF NOT EXISTS`. |
| `validation.py` | Validates request parameters. |
| `documents.py` | Reads a PDF or text document, says what it holds, and files it with its readings as health metrics. |
| `raw_dna.py` | Reads consumer DNA raw-data files and stores the variants. |
| `variant_reference.py`, `pharmacogenomic_reference.py` | Public reference tables (rs numbers per gene, medications per gene). No personal data. |
| `literature.py` | Journal lookup against Europe PMC. The only module that reaches the internet. |
| `reference_files.py` | Writes one readable HTML file per saved article into the data folder. |
| `ledger_setup.py` | First-run setup: whether the ledger is empty, importing or restoring a database, and the native folder and file choosers. |
| `profile_generator.py` | The long-form `/profile` page. |
| `doctor_templates.py` | Per-specialty gene lists and section choices for Doctor Docs. |
| `pdf_generator.py` | HTML to PDF with WeasyPrint, loaded on first use. If it cannot load, the PDF routes return 503 and the pages offer a printable version. |

`scripts/` holds command-line importers, extractors and checks. `app.py` and
`documents.py` import a few of them (`scripts.backup_database`,
`scripts.extract_health_metrics`); the rest are run by hand. A script must work
for anyone's records.

## Where data lives

All private data sits under one folder, `HEALTH_LEDGER_DATA_DIR`, outside the
repository. Under it, `config.py` defines:

| Path | Holds |
| --- | --- |
| `genetic_profile.db` | The database (`HEALTH_LEDGER_DB_PATH` overrides just this file). |
| `primary_sources/` | Copies of imported documents. |
| `references/` | The saved-article files. |
| `output/` | Generated files, including `output/doctor_docs/`. |
| `logs/` | `app.log`. |
| `backups/` | Database backups. |

A request that names a file location is resolved by `resolve_data_path` in
`app.py`, which refuses anything outside the data folder.

## Database

The schema is in `genetic_profile_db_schema.sql`; read it for the tables and
columns. In outline:

- Gene knowledge: `genes`, `snps`, `genotypes`, trait and health-condition
  associations, gene interactions, pharmacogenomic and medication tables,
  research findings.
- Records: `primary_sources` and `primary_source_findings` (imported
  documents and what was found in them), `health_metrics`, `dna_imports` and
  `snp_genotypes` (raw DNA data).
- References: `citations`, `citation_abstracts`, `citation_excerpts` and
  `citation_excerpt_specialties` (saved articles, their abstracts, and the
  excerpts chosen for each specialist).
- `app_settings`: small settings, including whether setup is done.
- Views named `v_*` for the joined gene, trait, condition and metric queries.

Each server thread keeps its own connection (`get_db()` in `app.py`, stored in
a `threading.local`, closed when the app context tears down). SQLite allows a
single writer; that is fine for one person.

## Request flow

```text
Browser
  -> app.py route
  -> database_manager / documents / raw_dna / literature / pdf_generator
  -> SQLite and the data folder
  -> Jinja page or JSON
```

- Pages are Jinja templates in `templates/`, extending `base.html`. Each page
  has a script in `static/js/` (TypeScript compiled in place) that calls the
  JSON routes (the ones whose paths start with `api`). The routes are listed in
  [the API reference](../api/API_REFERENCE.md).
- `/` sends a ledger that has never been set up to `/setup`.
- An import is two steps: `/import/preview` reads the file and writes
  nothing; `/import/document` or `/import/dna` stores it after the person
  confirms.
- A lookup on the References page is the one outbound request. `literature.py`
  sends the words typed (or one PubMed id) to Europe PMC when the person
  presses the button, and nothing from their records. See
  [PRIVACY.md](../PRIVACY.md).

## Front end

TypeScript in `static/js/*.ts` is compiled in place by `tsc`; the `.js`
outputs are committed. CSS is built by PostCSS from `static/css/health-ledger.css`
into `static/css/dist/health-ledger.css`, which is committed. The design
tokens in `static/css/design-system/` are vendored. PDFs do not use the
bundle; they load `static/css/pdf.css` and `print.css`. Commands and rules are
in [DEVELOPMENT.md](../DEVELOPMENT.md).

## Security posture

- The server binds to `127.0.0.1` (`HOST` in `config.py`) and nothing else.
- No CORS headers are sent, so another website open in the browser cannot read
  the API.
- Every response carries `X-Content-Type-Options`, `X-Frame-Options` and
  `X-XSS-Protection` headers.
- Debug mode is off unless `HEALTH_LEDGER_DEBUG` is set.
- Queries are parameterised; there is no authentication, because the server is
  not reachable from another machine.

Reporting a problem: [SECURITY.md](../../SECURITY.md).

## Packaged build

`packaging/health_ledger.spec` bundles `desktop.py`, the templates, the
shipped static files and the schema with PyInstaller. In a bundle `BASE_DIR` is
the unpack directory and settings live in a per-user folder and the default data folder is
`Health Ledger` in the person's home, which is why application code never derives a resource path
from `__file__`. WeasyPrint is left out of the bundle. See
[packaging/README.md](../../packaging/README.md).

## Related

- [DEVELOPMENT.md](../DEVELOPMENT.md): running, building, rules
- [DATABASE_README.md](../DATABASE_README.md): database documentation
- [Debugging guide](../troubleshooting/DEBUGGING_GUIDE.md)
