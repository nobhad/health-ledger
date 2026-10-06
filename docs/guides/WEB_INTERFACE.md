# Web Interface Guide

Health Ledger is a local web app: a Flask server on `127.0.0.1` and the pages
below in your browser. The pages are listed in the sidebar, in this order.

To start it, see [QUICK_START.md](QUICK_START.md) or [INSTALL.md](../../INSTALL.md).

## Pages

| Sidebar name | Address | What it is for |
| --- | --- | --- |
| Overview | `/` | What the ledger holds, recent sources, flagged results, and where to go next. |
| Import | `/import` | Add a document from your care, or a DNA raw-data file. The file is read and shown first; nothing is saved until you press **Add to my ledger**. |
| Sources | `/sources` | Every document you have added, with the text pulled out of it. Filter by search, type and date range. Three panels: Sources, Source Details, Findings. |
| Metrics | `/metrics` | Readings over time (blood pressure, weight, lab results) taken from the documents you added. **Apply Filters** and **Clear Filters** narrow the table. |
| Summary | `/summary` | The short version of your key findings. **Show everything** (`/summary?full=1`) is the long version; `/profile` redirects there. |
| Query | `/query` | Which of your genes relate to a condition, a trait or a medication. See below. |
| References | `/references` | Look up journal articles and choose excerpts for a specialist's document. See [REFERENCES.md](../features/REFERENCES.md). |
| Doctor Docs | `/doctor-docs` | A document for one kind of specialist. Fill in **Your details**, choose a **Specialty**, tick what to include, then **Open printable version** (or **Generate PDF** where the PDF library is installed). |
| Backup | `/backup` | **Create Backup**, **Available Backups**, **Export Database**, and notes on cloud storage. |

The first-run screen at `/setup` appears until you have started a ledger or
imported one. Afterwards **Import or restore** (linked from
the Import page) brings in a whole database or goes back to a backup.

The specialties in Doctor Docs come from `doctor_templates.py`.

## Query

The Query page has three cards, each with a search box to pick names from:

1. **Find Genes by Health Condition**: pick one or more conditions, press
   **Search**.
2. **Find Genes by Trait**: pick one or more traits, press **Search**.
3. **Get Gene Information**: pick one or more genes, press **Get Gene Info**.

Two buttons below the cards show everything at once: **Show All Genes** and
**Show Medication Metabolism**. Results appear underneath.

The API behind these pages is described in
[API_REFERENCE.md](../api/API_REFERENCE.md).

## Stopping

Press `Ctrl+C` in the terminal running `app.py`, `start.sh` or `start.bat`. The
downloaded app has a **Quit** item in its menu-bar or tray icon.

## Troubleshooting

See [the troubleshooting pages](../troubleshooting/README.md).
