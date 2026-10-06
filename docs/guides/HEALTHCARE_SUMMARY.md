# Healthcare Summary Scripts

Two terminal scripts add and list short notes about a doctor's visit. They are
older than the **Import** page and are optional: the app does not need them,
and the **Import** page is the usual way to add a record. Run them from the
checkout with the project's Python (`./venv/bin/python` below). They write to
the database in your data folder.

## Add a summary after a visit

Interactive:

```bash
./venv/bin/python scripts/add_healthcare_summary.py
```

It asks, in this order: visit date (`YYYY-MM-DD` or `MM/DD/YYYY`), doctor or
provider, institution or clinic, visit type (a number from 1 to 5), chief
complaint, symptoms, diagnosis, treatment or plan, medications,
follow-up instructions, additional notes, and whether lab results or tests
were ordered (and if so a file path for each).

The visit types are `sick_visit`, `routine_visit`, `emergency_visit`,
`specialist_consultation` and `other_visit`.

On one line, without prompts:

```bash
./venv/bin/python scripts/add_healthcare_summary.py --quick "2026-01-15" "Dr. Example" "Headache and fatigue" "Migraine"
```

The arguments are date, doctor, chief complaint and, optionally, diagnosis.
The visit type is `sick_visit`.

Each summary is stored as one source of type `healthcare_summary`, with a
finding for the visit and further findings for symptoms, treatment,
medications and follow-up when you gave them. The lab and test file paths are
written into the summary's details; the script does not read those files or
link them to anything.

## List summaries

```bash
./venv/bin/python scripts/view_healthcare_summaries.py
```

Options, which can be combined:

| Option | Shows |
| --- | --- |
| `--sick` | Only `sick_visit` summaries |
| `--routine` | Only `routine_visit` summaries |
| `--type NAME` | Only that visit type, for example `emergency_visit` |
| `--limit N` | The newest N |
| `--start YYYY-MM-DD` | Visits on or after that date |
| `--end YYYY-MM-DD` | Visits on or before that date |

Dates must be written `YYYY-MM-DD` here, because they are compared as text.
The list is newest first and ends with a count per visit type.
