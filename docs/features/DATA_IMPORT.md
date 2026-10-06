# Data Import

How a file gets into the ledger.

## The Import page

Open **Import** (`/import`). There are two file pickers: one for DNA raw data
and one for a document from your care. Either one sends the file to the same
preview route, and the app works out which kind it is. Importing is two steps,
so nothing is stored until you say so.

1. **Preview.** `POST /import/preview` saves the upload to a waiting folder
   (`imports/` inside the data folder) under a random token and reads it
   without writing anything to the database. It tries the DNA reader first and
   falls back to the document reader. A file ending `.zip` or `.gz` is only
   ever treated as DNA, so a failure there reports the DNA reader's message.
2. **Confirm or cancel.** `POST /import/dna` or `POST /import/document` writes
   the previewed file and deletes the waiting copy. `POST /import/cancel`
   deletes the waiting copy and writes nothing. A token that no longer has a
   waiting file gets "That file is no longer waiting to be imported."

### DNA raw data (`raw_dna.py`)

Reads the download from 23andMe, AncestryDNA, MyHeritage, FamilyTreeDNA and
Living DNA. The provider and layout are recognised from the comment lines and
the column header:

- `rsid, chromosome, position, genotype` (23andMe, Living DNA, or a generic
  file when neither name appears in the comments)
- `rsid, chromosome, position, allele1, allele2` (AncestryDNA)
- `RSID, CHROMOSOME, POSITION, RESULT` (MyHeritage, FamilyTreeDNA)

The delimiter is a tab or a comma. A plain file, a `.gz` file, or a `.zip`
holding exactly one file are all read as they came. Anything else is refused
with a message naming the columns it expected, and so is a file with no called
variants.

On confirm, every called variant is stored in `snp_genotypes` (one row per rs
number; a later import replaces an earlier one), the import is recorded in
`dna_imports` and as a primary source, and a copy of the file is kept in
`primary_sources/dna/` under the data folder. The preview lists which variants
fall in genes the ledger already tracks, using the list in
`variant_reference.py`.

VCF files are not read. The Import page says clinical VCF files are planned.

### Documents (`documents.py`)

Reads a PDF or a text file (`.pdf`, `.txt`, `.log`, `.md`, `.csv`).

- A PDF's own text layer is read first. If it has none, OCR is tried, and OCR
  works only when the optional extras are installed
  (`requirements-extras.txt`, plus the programs they need). Without OCR a
  scanned file is still kept with your records, marked as holding no
  searchable text.
- The kind of document comes from the words in the text, never from the file
  name. The kinds are lab results, health log, test report (a pharmacogenomic
  or gene report) and plain document, checked in that order of marker words.
- Readings found in lab results and health logs become rows in
  `health_metrics`.
- On confirm, the file is copied to `primary_sources/documents/` under the
  data folder and a primary source row holds the extracted text. A file
  imported again under the same name replaces its earlier import.
- A test report that names genes and medications also fills the
  drug-metabolism tables; see [PHARMACOGENOMIC.md](PHARMACOGENOMIC.md). The
  preview has an "add genes" box, ticked by default, which also starts
  tracking genes the report names that the ledger does not have yet.

To bring in a whole database or restore a backup, use **Setup**, not Import.

## Terminal scripts

All run from the project root with `./venv/bin/python`.

| Script | What it does |
| --- | --- |
| `scripts/import_raw_dna.py FILE` | The DNA import above. Takes `--dry-run` and `--db PATH`. |
| `scripts/import_document.py FILE` | The document import above. Takes `--dry-run` and `--add-genes`. |
| `scripts/extract_health_metrics.py` | Extracts vitals and lab values from primary sources already in the database. Takes `--dry-run`. |
| `scripts/import_pharmacogenomics.py` | See [PHARMACOGENOMIC.md](PHARMACOGENOMIC.md). |

The earlier program's bulk importers, which read fixed file names from one
person's records, were removed from this repository on 2026-10-05. A script
in `scripts/` has to work for anyone's records.
