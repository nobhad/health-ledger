# Summary

The Summary page (`/summary`) is the short version of what the ledger holds:
the health conditions, traits and gene interactions recorded in the database,
grouped for reading. The same page with `?full=1` is the long version, covered
in [`PROFILE_VIEWER.md`](PROFILE_VIEWER.md). `/profile` redirects to
`/summary?full=1`.

Nothing is stored. The page is built from the database on each request, so it
changes when the ledger does.

## How the short version is built

`app.summary()` in `app.py`:

1. If the `genes` table is empty, it renders `templates/summary.html` with an
   empty-state message and a link to Import.
2. Otherwise it calls `generate_summary_html(db)` from
   `scripts/generate_personalized_summary.py`.
3. It answers 500 if the generated HTML is shorter than 100 characters or if
   anything raises.

`generate_summary_html` calls `collect_findings`, which walks every gene and
groups its health-condition associations, trait associations and interacting
genes. The HTML has:

- an overview with the number of genes, conditions and traits;
- one heading per health condition, listing the genes tied to it with their
  notes (conditions with the most genes first);
- a list of traits, each with the genes that carry it;
- a closing line pointing to Show everything.

It does not read the DNA file, the pharmacogenomic tables or the primary
sources; the long version and the Query page cover those.

## The page

`templates/summary.html` shows the document with a Sections list on the left
(built in the browser by `static/js/doc-nav.ts` from the document's `h2`
headings; hidden when there are fewer than two) and two links above the
document: Show everything or Show the short version, and Save as PDF.

## PDF

Save as PDF links to `/api/pdf/summary` (short) or `/api/pdf/profile` (long).
Both build the same HTML, wrap it with `pdf_generator.wrap_pdf_document`, and
render it with WeasyPrint using `static/css/pdf.css` and `static/css/print.css`.
The PDF does not use the app's CSS bundle.

WeasyPrint's Python package installs anywhere, but it needs the Pango and
GObject libraries on the computer. When it cannot load them,
`pdf_generator.pdf_unavailable_reason()` returns the import error. The
summary page then leaves out the Save as PDF link (the browser's print dialog
still saves the page), and the two PDF endpoints answer 503 with JSON holding
`success: false`, a `message` and the `reason`. Other failures answer 500 with
`success: false` and a message.

## From the terminal

```sh
./venv/bin/python scripts/generate_personalized_summary.py
```

Takes no arguments. Writes a Markdown version of the same findings into
`config.OUTPUT_DIR` (under `HEALTH_LEDGER_DATA_DIR`, outside the repository),
creating the folder if needed, and prints the path it wrote.

## Files

- `scripts/generate_personalized_summary.py`: `collect_findings`,
  `generate_summary_markdown`, `generate_summary_html`.
- `app.py`: the `/summary`, `/profile`, `/api/pdf/summary` and
  `/api/pdf/profile` routes.
- `pdf_generator.py`: `generate_summary_pdf`, `generate_profile_pdf`,
  `pdf_unavailable_reason`.
- `templates/summary.html`, `static/js/doc-nav.ts`.
