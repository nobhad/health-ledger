# Changelog

Notable changes to Health Ledger. Newest first.

## 1.1.0 — 2026-10-05

The first published release. It includes everything listed under 1.0.1 and
1.0.0, neither of which was published.

### Added

- **A References page.** Type a gene, condition or medication, press
  **Look up**, and see journal articles with journal, year, type and citation
  count. Only articles indexed in MEDLINE are shown, so preprints are left
  out, and the words must be in the title or abstract. The most-cited matches
  are shown: practice guidelines first, then meta-analyses, systematic
  reviews and reviews, then the rest, each by citation count. The lookup
  happens only when you press the button.
- Saving an article puts it in your ledger and writes a readable file for it
  in a `references` folder inside your data folder. The file opens without the
  app.
- Fetching the abstract of a saved article, and adding verbatim excerpts from
  it. An excerpt must appear word for word in the abstract. Each excerpt can
  be assigned to one or more specialists.
- A "From the literature" section in a specialist's document, with each
  assigned excerpt as a quote followed by the article's title and a link. It
  is left out when the specialist has no excerpts.
- An **Include journal excerpts** option on Doctor Docs, on by default.

### Changed

- The privacy wording in the README, `SECURITY.md`, `docs/PRIVACY.md` and on
  the Overview and Import pages. Your records still never leave your computer.
  The app previously made no outbound request at all; it now makes one kind,
  the journal lookup you press, which sends the words you typed (or the
  PubMed id of an article you saved) to Europe PMC and nothing from your
  records.

### Fixed

- Saving a citation failed on a newly created ledger, because the code wrote
  to a column the schema does not create.
- A long web address in the middle panel of Sources or References pushed the
  panel sideways instead of wrapping.

## 1.0.1 — 2026-09-30

Built but never published, like 1.0.0.

### Changed

- The downloadable apps carry only the stylesheets the app serves: the built
  bundle and the two print sheets. The CSS source files and the TypeScript
  sources stay out of the download.
- The built stylesheet has no comments, which roughly halves its size
  (190 KB to 86 KB). No rule changed.
- The `/test` health check reports the version from `config.APP_VERSION`
  instead of a copy of it.
- Release notes link to `INSTALL.md` and `CHANGELOG.md` by full URL; the
  relative links went nowhere on a release page.

### Fixed

- The stylesheet declared two fonts (League Spartan, Michroma) whose files
  were not in the app. Nothing on screen uses them yet, so nothing looked
  wrong; the files and their licences now travel with the app, and a test
  fails if a stylesheet ever names a file that is not there.

## 1.0.0 — 2026-09-20

First public release: downloadable apps for macOS and Windows, and the source
published under a [source-available licence](LICENSE).

### Added

- Downloadable desktop apps. `desktop.py` starts the local server, finds a
  free port if 5001 is taken, opens a browser, and puts a menu-bar (macOS) or
  system-tray (Windows) icon on screen with **Open** and **Quit** — the thing
  a double-clicked app needs that a terminal window does not.
- PyInstaller packaging: `packaging/health_ledger.spec`, a build script per
  platform, and a generated icon set. Output is a `.dmg` on macOS and a `.zip`
  on Windows.
- GitHub Actions workflows: tests on every push, and a tagged release that
  builds both platforms and drafts the release.
- `waitress` as the server the packaged app runs on — pure Python, so it
  travels inside the bundle, and it does not print a development-server
  warning at somebody who only wanted to open their records.
- Documentation for people rather than developers: a rewritten `README.md`,
  an `INSTALL.md` covering the unsigned-app warnings on both platforms, and
  `SECURITY.md` stating the privacy model and its known limits.

### Fixed

- **Flask debug mode was on by default.** It served the Werkzeug interactive
  debugger, which runs arbitrary code for anything that can reach the port.
  It is now off unless `HEALTH_LEDGER_DEBUG` asks for it.
- **The database schema was located relative to `__file__`.** In a packaged
  build that points inside the PyInstaller archive rather than at the unpacked
  data file, so a fresh install could not create its database. It now goes
  through `config.DB_SCHEMA_PATH`.
- **Settings and records could have been written into the bundle's temporary
  unpack directory**, which is deleted when the app quits. A packaged copy now
  keeps settings in a per-user folder and falls back to `~/Health Ledger` for
  records, never to the app's own directory.
- Flask's template and static folders are pinned to `config.BASE_DIR`, which
  a packaged build otherwise infers wrongly from the module path.
- A link styled as a button came out dark red on a near-black fill and could
  barely be read: `pages.css` painted every `<a>` inside a `.card-body` brand
  red from a later cascade layer than the button classes.
- Query results were padded twice, sitting further in than anything else,
  because `query.ts` wrapped them in a second `.results-container` inside the
  one the page already provides.

### Changed

- **The app was reworked for people who did not build it.** Every page
  announced itself with a different name from the sidebar item that led
  there, so titles now match what you clicked. Summary and Profile were the
  same document at two lengths and are one page with a "Show everything"
  toggle; `/profile` redirects to it. The overview leads with four things to
  do rather than six counts. The sidebar's nine items are three named groups.
  Setup hands straight over to adding a first record, skippably. Every page
  reached before any records exist now says what is missing and offers the
  one button that fixes it, instead of showing zeros, a blank document, or
  (on the overview) an instruction to run extraction scripts in a terminal.
- The first-run screen no longer opens with a filesystem path field. It names
  the folder in a sentence, shows the path quietly, and offers the system
  folder picker.
- Alignment across the app: panels in a row share their heading and body
  rows, so a title that wraps in one no longer pushes its fields out of line
  with its neighbours; tables are full-bleed so a first column starts on the
  same line as the heading above it; one content inset everywhere.
- Developer material moved out of `README.md` into
  [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).
- Eight stale status files removed from the repository root
  (`ALL_FIXES_COMPLETE.md`, `COMPLETE_REVIEW_SUMMARY.md`,
  `EXTRACTION_STATUS.md`, `FIXES_APPLIED.md`, `FIXES_SUMMARY.md`,
  `MEDIUM_PRIORITY_COMPLETE.md`, `PROJECT_EVALUATION_AND_RECOMMENDATIONS.md`,
  `PROJECT_STATUS.md`). They described work finished in December 2025 and
  contradicted each other.

### Known limitations

- The downloadable apps cannot generate PDFs directly: WeasyPrint needs
  Pango/GTK, which are C libraries that cannot travel inside a bundle. **Open
  printable version** plus the browser's Save as PDF does the same job. Run
  from source to get the direct buttons. See
  [packaging/README.md](packaging/README.md).
- Neither download is code-signed, so macOS and Windows both warn on first
  launch. [INSTALL.md](INSTALL.md) says what to click.
- The macOS build is Apple Silicon (`arm64`) only. Intel Macs run from source.
- The Windows build has not been tested on Windows hardware yet.
