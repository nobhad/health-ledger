# Pharmacogenomic Data

Drug-metabolism findings: for each gene a test report names, a phenotype (for
example "Normal Metabolizer"), the genotype on file, and the medications that
gene is known to affect. A report's own medication lists are kept as well.

## How the data gets in

**From the Import page.** Add a pharmacogenomic report as a document (see
[DATA_IMPORT.md](DATA_IMPORT.md)). If its text contains words such as
"pharmacogenomic", "genotype" or "star allele", `documents.py` treats it as a
test report and calls `documents.pharmacogenomic_plans`, which uses
`plan_import` from `scripts/import_pharmacogenomics.py`. The preview lists
each gene's phenotype and the report's medication lists. Genes the report
names that the ledger does not track are listed too; the "add genes" box on
the preview, ticked by default, starts tracking them. Confirming writes the
data with `apply_import`.

**From the terminal.** `scripts/import_pharmacogenomics.py` does the same for
test reports already in the ledger:

```sh
./venv/bin/python scripts/import_pharmacogenomics.py --dry-run
./venv/bin/python scripts/import_pharmacogenomics.py
```

Other options: `--source ID` (repeatable) to limit it to one source,
`--set GENE=PHENOTYPE` to record a phenotype the text did not yield,
`--add-missing-genes`, and `--db PATH`. Both writes replace what an earlier
import stored, so running it again is safe. Nothing is written with
`--dry-run`.

The script parses the text with patterns written for one style of panel
report: a phenotype per gene, and medication lists under the headings "Use as
Directed", "Moderate Gene-Drug Interaction" and "Significant Gene-Drug
Interaction". A report laid out differently may yield nothing.

## Which medications a gene affects

The medications stored against a gene do not come from the report. They come
from `pharmacogenomic_reference.py`, a general list of gene-drug pairs
(`GENE_DRUGS`), each gene marked as `guideline`, `substrate` or `limited`
evidence. It holds no one's results. A gene missing from it gets no
medications.

## Tables

All in `genetic_profile_db_schema.sql`:

- `pharmacogenomic_data`: one row per gene, with `metabolism_status`,
  `genotype_phenotype` and an optional `citation_id`.
- `gene_pharmacogenomic_drugs`: the medications for each such row.
- `medication_interactions`: each medication a report lists, with its
  `category`, tied to the primary source it came from.

`GeneticProfileDB._ensure_pharmacogenomic_tables` creates the first two for
databases made before they were in the schema.

## Where it shows up

- **Query page.** The **Show Medication Metabolism** button fetches
  `GET /api/pharmacogenomic`: a JSON list, one object per gene, with
  `gene_symbol`, `gene_name`, `metabolism_status`, `genotype_phenotype` and
  `affected_medications` (a comma-separated string, or null). A server error
  returns 500.
- **Gene lookup.** `GET /api/gene-info?gene=SYMBOL` includes a
  `pharmacogenomic` object for that gene, or null.
- **Doctor documents.** `scripts/generate_doctor_document.py` adds a
  "Pharmacogenomic Information" block under each gene, and a "Medication
  Guidance from the Genetic Test Report" section, when the **Doctor Docs**
  pharmacogenomics checkbox is ticked (it is on by default). Both are left
  out when it is unticked.

The app records what a report states. What a finding means for a medicine is
a decision for a doctor or pharmacist.
