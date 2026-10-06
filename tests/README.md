# Tests

Run them from the project root with the project's virtual environment:

```bash
./venv/bin/python -m pytest                       # everything
./venv/bin/python -m pytest tests/test_setup.py   # one file
./venv/bin/python -m pytest -k pdf -v             # by name
```

pytest comes from `requirements-dev.txt`
(`./venv/bin/pip install -r requirements-dev.txt`). The tests are written with
`unittest`, so `./venv/bin/python -m unittest discover tests` also works.

## What they cover

No test touches the network, and none opens a real person's records: each one
works on temporary files and made-up data. Where the code reaches the internet
(`literature.py`) the request is patched.

One line per file:

- `test_api_endpoints.py` - the JSON routes.
- `test_database_manager.py` - `database_manager.py` against a temporary database.
- `test_validation.py` - `validation.py`.
- `test_setup.py` - first-run setup, importing and restoring a database.
- `test_documents.py` - reading, previewing and filing a document.
- `test_raw_dna.py` - consumer DNA files: parsing, matching, importing.
- `test_variant_genotypes.py` - a person's genotypes on gene pages and in doctor documents.
- `test_pharmacogenomics.py` - `scripts/import_pharmacogenomics.py` and the optional drug section.
- `test_extraction_patterns.py` - the vitals and lab extractors in `scripts/extraction_patterns.py`.
- `test_patient_details.py` - patient details saved with the database and printed on doctor documents.
- `test_literature.py` - `literature.py` with a made-up response.
- `test_reference_files.py` - `reference_files.py`, the folder of saved articles.
- `test_references_store.py` - saved articles, abstracts and excerpts in the database.
- `test_references_routes.py` - the References routes, lookup patched.
- `test_references_page.py` - what the References page sends.
- `test_document_references.py` - excerpts assigned to a specialist appear in that specialist's document.
- `test_document_disclaimer.py` - every generated document carries the disclaimer.
- `test_pdf_fallback.py` - PDF routes degrade to the printable version without WeasyPrint.
- `test_packaging.py` - properties a downloaded copy depends on: debug off by default, resource paths, port search, the PyInstaller spec and icons.
- `test_design_system_vendored.py` - the vendored design system matches the commit `VENDORED.md` pins and has no dangling `var()`.
- `test_docs_accuracy.py` - paths, routes and `npm run` names written in the docs exist, and every route is in the API reference.
- `test_no_private_data.py` - runs `scripts/check_private_data.py` over every tracked file.

`static/js/*.ts` behaviour is checked in a browser, not here.

## Adding a test

Create `tests/test_<thing>.py`, use made-up data, and clean up what you create
(temporary directory, or `setUp` / `tearDown`). Include a case that should
fail as well as one that should pass.
