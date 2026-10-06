# Primary Sources

A primary source is a document you added to your ledger: a lab result, a visit
note, a letter, a portal export, a DNA test report. The **Sources** page lists
them.

## Adding one

Use the **Import** page. Under **A document from your care**, choose a `.pdf`,
`.txt`, `.log`, `.md` or `.csv` file. Health Ledger reads it, shows what the
document holds and any readings it found, and saves nothing until you press
**Add to my ledger**.

What happens when you do:

- The file is copied into the `primary_sources` folder inside your data folder.
- One source row is stored with the text read from the file, up to 50,000
  characters.
- Readings found in the text (lab values, blood pressure, temperature) are
  added as health metrics, which the **Metrics** page shows.
- A document that reads as a pharmacogenomic test report also fills in the
  drug-metabolism tables from its gene results.
- Importing the same file again replaces its earlier import rather than adding
  a second copy.

What kind of document it is comes from its text, never its file name. The
kinds the Import page names are lab results, health log, test report and
document.

A scanned page has no text to read. It is kept with your records and marked as
having no searchable text, unless the optional OCR extras are installed (see
[INSTALL.md](../../INSTALL.md)).

DNA raw-data files go in under **DNA raw data** on the same page. Each variant
is stored, and the file itself is recorded as a source too.

## Looking at them

**Sources** has three panels. The left lists sources, with a search box and
filters for type and date range. The middle shows the selected source and its
text. The right shows its findings.

## Tables

Sources live in `primary_sources` and their findings in
`primary_source_findings`; the readings go to `health_metrics`. The columns are
in `genetic_profile_db_schema.sql`.

## The older bulk script

An earlier bulk extractor guessed each document's type and institution from
patterns written for one person's file names. It was removed from this
repository on 2026-10-05, since a script here has to work for anyone's
records. The Import page does the same job for everyone.
