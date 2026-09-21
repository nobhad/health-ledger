# Changelog

Notable changes to Health Ledger. Newest first.

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

### Changed

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
