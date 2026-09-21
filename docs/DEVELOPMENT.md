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
only.

By hand:

```bash
pip3 install -r requirements.txt          # what the app needs
pip3 install -r requirements-extras.txt   # optional: OCR, DICOM, PubMed scripts
pip3 install -r requirements-dev.txt      # optional: the test suite
python3 app.py            # http://localhost:5001
python3 desktop.py        # the same, with the menu-bar icon the packaged app has
```

`python3 app.py [port]` takes a port. `desktop.py` finds a free one by itself,
starting from 5001.

### Environment

| Variable | Does |
| --- | --- |
| `HEALTH_LEDGER_DATA_DIR` | Where all private data lives. Set in `.env`. |
| `HEALTH_LEDGER_DB_PATH` | Overrides just the database file. Used by the tests. |
| `HEALTH_LEDGER_DEBUG` | `1` turns on Flask debug and DEBUG-level logs. Off by default, and it must stay that way in anything released — debug mode serves the Werkzeug interactive debugger, which runs arbitrary code for whatever can reach the port. |

## Privacy — the one hard rule

All private data — `genetic_profile.db`, `primary_sources/`, `output/`,
`logs/`, `backups/` — lives **outside the repository**, under
`HEALTH_LEDGER_DATA_DIR` (set in the git-ignored `.env`; see `config.py`).

Nothing under that directory is ever copied into the repo, a commit, a doc, a
script default or a test fixture. No real names, record file names, home
paths, genotypes or results in tracked files — use placeholders.

```bash
python3 scripts/check_private_data.py       # the whole tree
python3 scripts/check_private_data.py --staged
```

The test suite runs the same scan and the pre-commit hook blocks a commit that
fails it. Import scripts written against one person's records live with that
person's data, not here: a script in `scripts/` must work for anyone's record.

## Project structure

```text
health-ledger/
├── app.py                        # Flask routes
├── desktop.py                    # packaged-app entry: server + menu-bar icon
├── config.py                     # paths, logging, the frozen/checkout split
├── database_manager.py           # database API
├── documents.py, raw_dna.py      # the file readers behind /import
├── pdf_generator.py              # WeasyPrint, with the printable fallback
├── doctor_templates.py           # per-specialty gene lists
├── pharmacogenomic_reference.py  # public gene-drug reference
├── variant_reference.py          # public rsID reference, checked against dbSNP
├── validation.py, ledger_setup.py
├── genetic_profile_db_schema.sql
├── templates/                    # Jinja: base, header, footer, one per page
├── static/                       # css/, js/ (TypeScript), fonts/, images/
├── scripts/                      # importers, extractors, checks
├── packaging/                    # PyInstaller spec, build scripts, icons
├── tests/                        # pytest
└── docs/
```

## Front end

TypeScript in `static/js/*.ts`, compiled in place by `npm run build` (`tsc`).
The `.js` outputs are committed. **Never edit a `.js` file that has a `.ts`
sibling.**

Native `<select>` controls are enhanced by `static/js/dropdown.ts`; give a
select `.form-select` or `.filter-select` and it gets the portal dropdown.

```bash
npm install
npm run build          # tsc + CSS
npm run check          # lint + typecheck — run before calling a change done
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
./venv/bin/python -m pytest          # 185 tests
```

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
- [Release process](../packaging/README.md)
