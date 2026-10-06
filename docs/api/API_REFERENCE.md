# API Reference

Every route in `app.py`. The pages and the JSON routes are served by the same Flask
app. To list the routes as the running code has them:

```sh
./venv/bin/python -c "import app; [print(sorted(r.methods - {'HEAD','OPTIONS'}), r.rule) for r in app.app.url_map.iter_rules()]"
```

## Access

- There is no authentication, no rate limiting, no versioning and no CORS. The server
  binds to `127.0.0.1` only (`HOST` in `config.py`, used by both `app.py` and
  `desktop.py`), so only programs on the same computer can reach it. `python3 app.py`
  listens on port 5001 by default, or the port given as its first argument; the
  packaged launcher (`desktop.py`) picks its own port.
- Every response carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and
  `X-XSS-Protection: 1; mode=block`.
- The app logs to `app.log` in the logs folder (`LOGS_DIR`).

## What changes data or reaches the network

- Routes that write to the database, the data directory or settings: `POST /setup/start`,
  `POST /setup/import`, `POST /setup/restore`, `POST /import/dna`,
  `POST /import/document`, `POST /doctor-docs/details`, `POST /api/references`,
  `DELETE /api/references/<article_id>`, `POST /api/references/<article_id>/abstract`,
  `POST /api/references/<article_id>/excerpts`, `PUT /api/excerpts/<excerpt_id>`,
  `DELETE /api/excerpts/<excerpt_id>`, `POST /api/backup/create`,
  `POST /api/backup/export`.
- Routes that write only files: `POST /import/preview` and `POST /import/cancel` (an
  upload waiting in the `imports` folder of the data directory), `/api/pdf/doctor/<specialty>`
  (a PDF in the doctor documents folder, or the folder named in `save_path`), and
  `GET /api/references/<article_id>` (rewrites the article's file in the references
  folder if it is missing).
- Routes that reach the network: exactly two handlers call `literature`, and both send
  a request to the Europe PMC search service (`https://www.ebi.ac.uk/europepmc/webservices/rest/search`),
  with a `User-Agent` of `HealthLedger/<version>` and a 10 second timeout.
  - `POST /api/references/search` sends the words typed, as a title-or-abstract query
    restricted to PubMed records, sorted by citation count, 25 results per page.
  - `POST /api/references/<article_id>/abstract` sends the saved article's PubMed id.
  - Nothing else in `app.py` makes an outbound request. Records are never sent.

## Error shapes

Three shapes are in use.

- The gene, trait and condition lookups answer with `{"error": "...", "status": 400}`.
  A 500 carries `"details": {"traceback": "..."}` only when `HEALTH_LEDGER_DEBUG` is set.
- The sources, references, PDF and backup routes answer with
  `{"success": false, "message": "..."}`.
- Page routes answer a failure with a short plain-text line such as
  `Error loading page: <reason>` and status 500. The setup and import forms instead
  re-render their own page with the error shown and the status given below.

## Health check

`GET /test` returns 200 `{"status": "ok", "message": "Server is working!", "version": "1.1.0"}`
(the version is `APP_VERSION` from `config.py`).

## Setup

- `GET /setup`: HTML page for choosing a data folder, importing a database or restoring
  a backup. 500 on a render error. `GET /` redirects here while the ledger is empty and
  setup has never been completed.
- `POST /api/browse`: opens the computer's own folder or "save as" dialog and returns
  the choice. JSON body: `kind` (`"folder"` default, or `"save"`), `current` (path to
  start from, default the data directory), `filename` (proposed name for `"save"`,
  default `export.db`). Returns 200 `{"path": "/chosen/path"}`, with `"path": null` if
  the dialog was cancelled. 501 `{"error": "..."}` if no dialog can be shown.
- `POST /setup/start`: form field `data_folder` (absolute path; blank means the
  proposed default). Sets the data folder, marks setup complete and redirects to
  `/import?first=1`. 400 (setup page re-rendered) if the folder is not absolute, is
  inside the app folder, cannot be created or cannot be written to; 500 on other errors.
- `POST /setup/import`: multipart field `database` (a `.db` file), optional
  `data_folder`. The file is checked before it replaces anything. Redirects to
  `/?notice=imported`. 400 if no file is given or the file is not a valid database;
  500 on other errors.
- `POST /setup/restore`: form field `filename` (a file in the backups folder), optional
  `data_folder`. Redirects to `/?notice=restored`. 404 if the backup is not on disk;
  400 if it is not a valid database or the folder is unusable; 500 on other errors.

## Import

- `GET /import`: HTML page for choosing a file. Query `first=1` shows the guided
  first-run framing.
- `POST /import/preview`: multipart field `file`. Reads the file as DNA raw data, then
  (unless it is a `.zip` or `.gz`) as a document, and renders what it holds. Nothing is
  written to the ledger. 400 if no file is given or neither reader recognises it;
  500 on other errors.
- `POST /import/dna`: form fields `token` (from the preview), optional `first=1`.
  Writes the previewed raw-data file and redirects to `/?notice=dna`
  (`/?notice=first-record` when `first=1`). 400 if the token matches no waiting file
  or the file cannot be read; 500 on other errors.
- `POST /import/document`: form fields `token`, optional `add_genes=1`, optional
  `first=1`. Writes the previewed document and redirects to `/?notice=document`
  (or `first-record`). Same refusals as `/import/dna`.
- `POST /import/cancel`: form field `token`. Deletes the waiting upload and redirects
  to `/import`. Never refuses; an unknown token is ignored.

## Pages

HTML pages, each rendered from a template. `GET` only.

- `GET /`: overview (counts, recent sources, abnormal metrics, last backup). Redirects to
  `/setup` on a fresh ledger. Query `notice` selects a confirmation line.
- `GET /query`: gene, trait and condition query page. It calls the query routes below.
- `GET /summary`: key findings. `?full=1` gives the full write-up. 500 if the document
  comes out empty or cannot be generated.
- `GET /profile`: redirects to `/summary?full=1`.
- `GET /metrics`: health metrics list. Query `metric_type`, `start_date`, `end_date`,
  `routine_only=true`. With no query string at all, routine visits only is on.
- `GET /sources`: source browser; it calls the `/api/sources` routes.
- `GET /references`: journal lookup and saved articles; it calls the `/api/references`
  routes.
- `GET /doctor-docs`: doctor document page.
- `GET /doctor-docs/<specialty>/print`: the document as a printable page. Query flags
  `medications`, `stats`, `pharmacogenomics`, `variants`, `details`, `references`;
  `0` leaves that section out, anything else (or absent) keeps it. 404 for an unknown
  specialty; 500 on a render error.
- `GET /backup`: backup page; it calls the backup routes below.
- `GET /static/<path:filename>`: static files.

## Query

JSON. All are `GET`.

- `GET /api/all-genes`: every gene row.

  ```json
  [{"id": 1, "gene_symbol": "GENE1", "gene_name": "Example Gene One", "chromosome": "1"}]
  ```

  The objects are whole `genes` table rows, so they may carry further columns.
- `GET /api/all-traits`: `["trait one", "trait two"]`, distinct, sorted.
- `GET /api/all-conditions`: `["condition one", "condition two"]`, distinct, sorted.
- `GET /api/gene-info?gene=GENE1`: `gene` is required, a gene symbol (upper-cased
  before the lookup).

  ```json
  {
    "gene_symbol": "GENE1",
    "gene_name": "Example Gene One",
    "chromosome": "1",
    "traits": ["trait one"],
    "health_conditions": ["condition one"],
    "interacting_genes": ["GENE2"],
    "pharmacogenomic": {
      "metabolism_status": "Normal",
      "genotype_phenotype": "Example",
      "affected_medications": "Drug A,Drug B"
    },
    "variants": [{"rsid": "rs0000001", "genotype": "AA", "description": "Example"}]
  }
  ```

  `pharmacogenomic` is `null` when the gene has none. `variants` is empty until a DNA
  file has been imported. 400 for a missing or invalid symbol, 404 if the gene is not
  in the ledger, 500 on a database error.
- `GET /api/genes-by-trait?trait=trait+one`: `trait` is required. Returns an array of
  gene objects for matches of that trait (`[{"gene_symbol": "GENE1", "gene_name": "..."}]`,
  with the further fields the query selects). 400 for a missing or invalid trait, 500.
- `GET /api/genes-by-condition?condition=condition+one`: `condition` is required and may
  be repeated as `condition[]=a&condition[]=b` (at most 50). Returns the matching genes
  with duplicates removed. 400 for a missing, invalid or empty condition, 500.
- `GET /api/pharmacogenomic`: all pharmacogenomic rows, ordered by gene symbol.

  ```json
  [{"gene_symbol": "GENE1", "gene_name": "Example Gene One",
    "metabolism_status": "Normal", "genotype_phenotype": "Example",
    "affected_medications": "Drug A,Drug B"}]
  ```

  500 on a database error.

Names are checked by `validation.py` before they reach the database.

## Sources

JSON. All are `GET`; every failure is `{"success": false, "message": "..."}`.

- `GET /api/sources`: optional query `search`, `type`, `start_date`, `end_date`. Only
  one filter is applied, in that order of precedence (`search`, then `type`, then the
  dates). Returns 200:

  ```json
  {"success": true, "count": 1, "sources": [{"id": 1, "source_name": "report.pdf", "source_type": "lab", "document_date": "2026-01-15"}]}
  ```

  Each source is a whole `primary_sources` row. 500 on a database error.
- `GET /api/sources/<source_id>`: `{"success": true, "source": {..., "findings": [...]}}`.
  404 `Source not found`, 500.
- `GET /api/sources/<source_id>/findings`: `{"success": true, "count": 1, "findings": [{"id": 1, "gene_symbol": "GENE1"}]}`.
  Findings carry the `primary_source_findings` columns plus `gene_symbol` and
  `gene_name`. An unknown id gives an empty list, not a 404. 500.
- `GET /api/sources/<source_id>/text`: `{"success": true, "text": "extracted text"}`.
  404 if the source does not exist or has no extracted text, 500.

## References

JSON. Every failure is `{"success": false, "message": "..."}`. A request body that is
not a JSON object gets 400. An unexpected error gets 500. A lookup that could not
complete (offline, timed out, the service answered with an error or something
unreadable) gets 502 with a sentence for the reader.

- `POST /api/references/search`: reaches the network (see above). Body
  `{"term": "example term"}`; at most 200 characters, not blank. Returns 200:

  ```json
  {"success": true, "results": [{
    "title": "Example title", "authors": "Doe J, Roe R", "journal": "Example Journal",
    "year": 2020, "pubmed_id": "00000000", "doi": "10.0000/example", "url": "https://example.org/a",
    "abstract": "Example abstract.", "publication_types": ["Review"],
    "cited_by": 12, "kind": "Review", "saved_id": null
  }]}
  ```

  Results are ordered by kind (Guideline, Meta-analysis, Systematic review, Review,
  Study), then most cited. `saved_id` is the id of the matching saved article, or
  `null`. Nothing is saved. 400 for a missing, blank or over-long term.
- `GET /api/references`: `{"success": true, "articles": [...]}`. Each article is a
  `citations` row plus `has_abstract` (boolean) and `excerpt_count`. Citations that are
  the person's own records are left out.
- `GET /api/references/<article_id>`: `{"success": true, "article": {..., "abstract": null, "excerpts": [{"id": 1, "excerpt_text": "...", "specialties": ["example_specialty"]}]}, "specialties": [{"id": "example_specialty", "label": "Example Specialty"}]}`.
  404 if there is no such article.
- `POST /api/references`: saves an article a search returned. Body keys `title`
  (required, non-blank string), `authors`, `journal`, `year`, `doi`, `pubmed_id`, `url`,
  `abstract`; other keys are ignored. `year` that is not an integer, a `pubmed_id` that
  is not digits, and a `url` that does not start with `http://` or `https://` are
  stored as `null`. Returns 200 `{"success": true, "id": 7, "article": {...}}`. 400 if
  the title is missing.
- `POST /api/references/<article_id>/abstract`: reaches the network (see above). No
  body needed. Fetches and stores the abstract using the article's PubMed id. Returns
  `{"success": true, "article": {...}}`. 404 if the article does not exist or the index
  has no abstract for it; 400 if the article has no PubMed id; 502 if the lookup failed.
- `DELETE /api/references/<article_id>`: `{"success": true}`. 404 if there is no such
  article; 409 if something else in the ledger cites it.
- `POST /api/references/<article_id>/excerpts`: body `{"text": "passage"}`. The passage
  must appear word for word in the stored abstract (whitespace ignored). Returns
  `{"success": true, "id": 3, "article": {...}}`. 404 if there is no such article;
  400 if the article has no abstract, the text is empty or the text is not in the
  abstract.
- `PUT /api/excerpts/<excerpt_id>`: body `{"specialties": ["example_specialty"]}`, a list
  of specialty ids from `GET /api/doctor-specialties`. Replaces the excerpt's list.
  Returns `{"success": true, "article": {...}}`. 404 if there is no such excerpt;
  400 if `specialties` is not a list of strings or names an unknown specialty.
- `DELETE /api/excerpts/<excerpt_id>`: `{"success": true, "article": {...}}`, the
  article the excerpt belonged to. 404 if there is no such excerpt.

## Doctor documents and PDFs

- `GET /api/doctor-specialties`: the templates the page offers.

  ```json
  [{"id": "example_specialty", "label": "Example Specialty", "title": "Example Title",
    "genes": "All genes", "sections": "Summary, Health Metrics", "detail_level": "Brief"}]
  ```

- `POST /doctor-docs/details`: form fields `full_name`, `date_of_birth`, `address`,
  `phone`, `insurance_provider`, `insurance_member_id`, `insurance_group_number`.
  Saves them and redirects to `/doctor-docs?saved=1`. 500 on an error.
- `GET` or `POST /api/pdf/doctor/<specialty>`: makes the PDF, saves a copy as
  `<name>_<specialty>_<YYYY-MM-DD>.pdf`, and returns it as a download
  (`application/pdf`). `GET` uses every option. `POST` takes an optional JSON body:
  `save_path` (a folder, relative to the data directory or absolute inside it;
  default is the doctor documents folder), and the booleans `include_original`,
  `include_medications`, `include_stats`, `include_pharmacogenomics`,
  `include_variants`, `include_details`, `include_references`, all default `true`.
  Refusals: 404 for an unknown specialty; 400 if `save_path` is outside the data
  directory; 503 `{"success": false, "message": "...", "reason": "...", "print_url": "/doctor-docs/<specialty>/print?..."}`
  when the PDF library cannot load on this computer (the `print_url` is the printable
  page with the same options); 500 if generation fails.
- `GET /api/pdf/summary`: the summary as a PDF download. 503 as above (without
  `print_url`), 500 if generation fails.
- `GET /api/pdf/profile`: the full profile as a PDF download. Same refusals.
- `GET /api/pdf/source/<source_id>`: one source as a PDF download. 404
  `Source not found`; 503 and 500 as above.

## Backup

JSON. Failures are `{"success": false, "message": "..."}`.

- `POST /api/backup/create`: no body. Makes a timestamped copy in the backups folder.
  Returns 200 `{"success": true, "message": "Backup created successfully", "path": "/data/backups/example.db"}`.
  500 if it failed.
- `GET /api/backup/list`: newest first.

  ```json
  {"success": true, "backups": [{"filename": "example.db", "path": "/data/backups/example.db", "size": 123456, "created": "2026-01-15T09:30:00"}]}
  ```

  500 on an error.
- `POST /api/backup/export`: body `{"format": "db", "path": "backups/export.db"}`.
  `format` is `"db"` (default; a consistent copy of the database) or `"json"` (every
  table as JSON). `path` is required and must resolve inside the data directory
  (relative paths start from it). Returns 200
  `{"success": true, "message": "Database exported to db", "path": "/data/backups/export.db"}`.
  400 if `path` is missing or outside the data directory; 500 if the export failed.
