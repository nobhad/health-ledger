# Development

How Health Ledger runs from source, how it is laid out, and the rules that
apply to changes. For installing it as an app, see
[INSTALL.md](../INSTALL.md); for building the downloadable apps, see
[packaging/README.md](../packaging/README.md).

## Running it

```bash
./start.sh            # macOS and Linux, or double-click "Health Ledger.command"
start.bat             # Windows
npm run dev           # the same as ./start.sh
```

The first run creates `./venv`, installs `requirements.txt`, starts the server
on <http://127.0.0.1:5001> and opens a browser. The server binds to `127.0.0.1`
only. `start.sh` reinstalls when `requirements.txt` changes; `start.bat`
installs once, so after a change run `venv\Scripts\pip install -r requirements.txt`.

By hand, from the project root:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt          # what the app needs
./venv/bin/pip install -r requirements-extras.txt   # optional: OCR, DICOM, PubMed scripts
./venv/bin/pip install -r requirements-dev.txt      # optional: the test suite
./venv/bin/python app.py            # http://127.0.0.1:5001
./venv/bin/python desktop.py        # the same, with the menu-bar icon the packaged app has
```

`python3 app.py [port]` takes a port. `desktop.py` finds a free one by itself,
starting from 5001.

### Environment

| Variable | Does |
| --- | --- |
| `HEALTH_LEDGER_DATA_DIR` | Where all private data lives. Set in `.env`. |
| `HEALTH_LEDGER_DB_PATH` | Overrides just the database file. Used by the tests. |
| `HEALTH_LEDGER_DEBUG` | `1`, `true`, `yes` or `on` turns on Flask debug and DEBUG-level logs. Off by default, and it must stay that way in anything released: debug mode serves the Werkzeug interactive debugger, which runs arbitrary code for whatever can reach the port. |

`config.py` reads `.env` from the checkout (a packaged copy reads a per-user
folder) without overriding variables already in the environment. The setup
screen writes `HEALTH_LEDGER_DATA_DIR` there.

## Privacy — the one hard rule

All private data — `genetic_profile.db`, `primary_sources/`, `output/`,
`logs/`, `backups/` — lives **outside the repository**, under
`HEALTH_LEDGER_DATA_DIR` (set in the git-ignored `.env`; see `config.py`).

Nothing under that directory is ever copied into the repo, a commit, a doc, a
script default or a test fixture. No real names, record file names, home
paths, genotypes or results in tracked files — use placeholders.

```bash
./venv/bin/python scripts/check_private_data.py            # every tracked file
./venv/bin/python scripts/check_private_data.py --staged   # what is staged
./venv/bin/python scripts/check_private_data.py path/to/file.md
```

The test suite runs the same scan, and so does CI. A pre-commit hook that runs
`check_private_data.py --staged` is a local file in `.git/hooks/`; a clone does
not have one, and a `core.hooksPath` setting bypasses it. Import scripts written against one person's records live with that
person's data, not here: a script in `scripts/` must work for anyone's record.

## Project structure

```text
health-ledger/
├── app.py                        # Flask routes
├── desktop.py                    # packaged-app entry: server + menu-bar icon
├── config.py                     # paths, logging, the frozen/checkout split
├── database_manager.py           # database API
├── documents.py, raw_dna.py      # the file readers behind /import
├── literature.py                 # journal lookup: the only code that reaches the internet
├── reference_files.py            # one readable file per saved article
├── ledger_setup.py               # first-run setup, database import and restore
├── pdf_generator.py              # WeasyPrint, with the printable fallback
├── profile_generator.py          # the /profile page
├── doctor_templates.py           # per-specialty gene lists
├── pharmacogenomic_reference.py  # public gene-drug reference (used by an import script)
├── variant_reference.py          # public rsID reference
├── validation.py                 # request validation
├── genetic_profile_db_schema.sql
├── templates/                    # Jinja: base, sidebar, footer, one per page
├── static/                       # css/, js/ (TypeScript), fonts/, images/
├── scripts/                      # importers, extractors, checks
├── packaging/                    # PyInstaller spec, build scripts, icons
├── tests/                        # pytest
└── docs/
```

For how the pieces fit together, see
[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md).

## Front end

TypeScript in `static/js/*.ts`, compiled in place by `npm run build` (`tsc`).
The `.js` outputs are committed. **Never edit a `.js` file that has a `.ts`
sibling.**

Native `<select>` controls are enhanced by `static/js/dropdown.ts`; give a
select `.form-select` or `.filter-select` and it gets the portal dropdown.

```bash
npm install
npm run build          # tsc, then the CSS bundle
npm run build:watch    # tsc --watch
npm run check          # lint + typecheck: run before calling a change done
```

## Styling

The design system is vendored: `static/css/design-system/` is a copy of
no-bhad-codes' tokens, reset, fonts and layer order. **Do not hand-edit it.**
Run `npm run sync:design-system` to pull a newer copy (the script applies two
documented patches). `tests/test_design_system_vendored.py` enforces both that
and the absence of dangling `var()` references.

App CSS lives in `static/css/`: `app-tokens.css` (the few tokens this app
adds), `base.css`, `components.css` (every reusable class), `layout.css`,
`pages.css`, `utilities.css`. Cascade layers are declared once in the vendored
`layer-order.css`; `portal-theme.css` is imported last and unlayered.

No literal colours, sizes or durations in app CSS. If a value is missing, add
a token to `app-tokens.css` that aliases a design-system token, then use it.

`<body data-page="ledger">` is the surface the portal theme keys its palette
to. Dark mode is `html[data-theme="dark"]` (toggle in the header,
`static/js/theme.ts`).

```bash
npm run build:css      # -> static/css/dist/health-ledger.css (committed)
npm run watch:css
```

The built bundle is committed so the Flask app runs without Node. PDFs
(WeasyPrint) do not use it; they load `static/css/pdf.css` + `print.css`.

### Layout contract

- The page is the viewport: sticky header, `<main>` fills the rest, the footer
  is a fixed curtain revealed by the last stretch of scroll. A region that can
  outgrow the page scrolls inside itself (`.is-fill`, `.grid--fill`,
  `.page-body--flush`).
- Panels tile the page with rules between them and no gutters; padding is
  internal.
- Page titles come from the `page_title` / `page_description` blocks in
  `base.html`.
- A card's buttons sit in a `.card-actions` strip as the last child of
  `.card-body` (or of a form that is), so buttons land on the same bottom edge
  on every page.
- Lucide icons, never emoji.

## Python

Use the project venv: `./venv/bin/python`.

```bash
./venv/bin/python -m pytest
```

[tests/README.md](../tests/README.md) says what each test file covers.

Extraction scripts that write to `health_metrics` must stay idempotent and
support `--dry-run`.

### Paths and the packaged build

`config.py` keeps three roots apart, and code must use the right one:

- `BASE_DIR` — read-only application resources (templates, static, the schema
  SQL). In a packaged build this is the PyInstaller unpack directory, so
  **never derive a resource path from `__file__`** in application code.
- `CONFIG_DIR` / `ENV_PATH` — where settings are written. The checkout in a
  checkout; a per-user folder in a packaged build.
- `DATA_ROOT` — the person's records. Never inside either of the above.

## Concurrency

More than one session may work in this repo at once. Before committing run
`git status`, stage only files you edited by path, and commit with
`git commit -F - -- <paths>`. Never `git add -A`, never stash, reset or
rewrite history.

## More

- [API Reference](api/API_REFERENCE.md)
- [Architecture](architecture/ARCHITECTURE.md)
- [Privacy](PRIVACY.md)
- [Troubleshooting](troubleshooting/DEBUGGING_GUIDE.md)
- [Packaging and releases](../packaging/README.md)
