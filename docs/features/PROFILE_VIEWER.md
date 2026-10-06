# Full Profile

The full profile is the long version of the Summary page: every gene in the
ledger and what is recorded about each. It lives at `/summary?full=1`
(the Summary page's Show everything link). `/profile` redirects there, so old links still work.
In the sidebar the page is called Summary.

The short version is described in [`SUMMARY_GENERATOR.md`](SUMMARY_GENERATOR.md).

## How it is built

`app.summary()` in `app.py` calls `generate_profile_html(db)` from
`profile_generator.py` when `full=1`, and renders it in `templates/summary.html`.
Nothing is stored; the HTML is generated from the database on each request. An
empty ledger (no rows in `genes`) shows a message and a link to Import instead.
A generation error, or output shorter than 100 characters, answers 500.

## What the document contains

In this order:

1. A title and a header with the test provider and test date (from
   `db.get_genetic_test_info()`, left out when there is none) and the date it
   was generated.
2. A numbered table of contents linking to each gene.
3. One section per gene, in the order of `get_all_genes()`. Each shows, when
   the ledger has them: the genotype and phenotype, the SNP rs numbers, trait
   associations, health-condition associations, database sources, gene-gene
   interactions and research findings.
4. A References list built from `get_all_references()`.

Trait and condition lines carry citation numbers. Each is a link to the
matching reference (`#ref-<number>`), and each reference list item has
`id="ref-<number>"`. When a line cites more than one source, only the first
number shows, followed by `+`; clicking it expands the full list (the small
script at the bottom of `summary.html`).

## Navigation and PDF

`static/js/doc-nav.ts` builds the Sections list from the document's `h2`
headings (one per gene, plus References) and marks the section in view. The
page's Save as PDF link goes to `/api/pdf/profile`; see
[`SUMMARY_GENERATOR.md`](SUMMARY_GENERATOR.md) for what happens when the PDF
libraries are missing.

## Styling

The document sits in `.summary-content` inside `.doc-layout`. Those rules are
in `static/css/pages.css`; they use design-system tokens, the dark theme is
`html[data-theme="dark"]`, and the built bundle is
`static/css/dist/health-ledger.css` (`npm run build:css`).

## Files

- `profile_generator.py`: `generate_profile_html`, `format_citation_numbers`.
- `app.py`: `/summary`, `/profile`, `/api/pdf/profile`.
- `templates/summary.html`, `static/js/doc-nav.ts`.
