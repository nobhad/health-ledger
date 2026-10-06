# Packaging and releases

How the downloadable Health Ledger apps are built.

## What is here

| File | Does |
| --- | --- |
| `health_ledger.spec` | The PyInstaller build. Shared by both platforms. |
| `build_macos.sh` | Builds `Health Ledger.app`, wraps it in a `.dmg`. |
| `build_windows.ps1` | Builds `HealthLedger.exe`, wraps it in a `.zip`. |
| `make_icons.py` | Draws `icon.svg`, `icon.png`, `icon.icns` and `icon.ico`; `icon.sha256` records what they were drawn from. |
| `verify_icon.py` | Checks that a built `.icns` carries the committed `icon.png`, by pixels. The release workflow runs it. |
| `requirements-build.txt` | PyInstaller and pystray, on top of `requirements.txt`. |

The entry point is `desktop.py` in the project root, not `app.py`: it adds the
free-port search, the browser open and the menu-bar icon that gives a
double-clicked app a **Quit**.

## Building

Each build makes its own virtual environment in `build/venv`, so the project's
`./venv` — which has pytest and WeasyPrint in it — cannot leak into the
bundle.

```bash
packaging/build_macos.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

Output lands in `dist/`, named from `APP_VERSION` in `config.py`:

```text
dist/HealthLedger-<version>-macOS-<arch>.dmg
dist/HealthLedger-<version>-windows-x64.zip
```

Both `build/` and `dist/` are git-ignored. **A Mac cannot build the Windows
executable and vice versa** — PyInstaller bundles a platform's own Python
runtime. Use the `release` GitHub Actions workflow for the pair.

## Two decisions worth knowing

### WeasyPrint is excluded on purpose

WeasyPrint is a binding onto Pango/GTK, which are C libraries. Shipping them
inside a bundle means relocating a good part of Homebrew and fixing every
dylib path, and it breaks on the next OS update.

The app already degrades without it — `pdf_generator.pdf_unavailable_reason()`
reports why, the PDF routes (`/api/pdf/summary`, `/api/pdf/profile`,
`/api/pdf/source/<id>`, `/api/pdf/doctor/<specialty>`) answer 503 with a plain message and a
`reason`, the doctor route adds a `print_url`, and Doctor Docs offers
**Open printable version** instead. The
browser's own Save as PDF makes the file. The build scripts strip WeasyPrint
out of the runtime requirements so it cannot be pulled in by accident.

If that changes, the fallback tests are in `tests/test_pdf_fallback.py`.

### One folder, not one file

A one-file PyInstaller build unpacks the entire bundle into a temporary
directory on every launch: slow to start, and the pattern Windows antivirus
objects to most. The one-folder build is wrapped in a `.dmg` or a `.zip`, so
the person still downloads a single file.

## Signing

Neither artifact is signed, so both systems warn on first launch. Getting rid
of that costs:

| | Cost | Removes |
| --- | --- | --- |
| Apple Developer Program | 99 USD / year | Gatekeeper's "unidentified developer", once the app is also notarized. |
| Windows code-signing certificate | ~200–400 USD / year | SmartScreen, after the certificate builds reputation. |

Until then, `INSTALL.md` tells people exactly what they will see and what to
click. `build_macos.sh` does an ad-hoc `codesign`, which does **not** avoid
Gatekeeper — it only keeps macOS from refusing to run the app locally.

## Cutting a release

1. Update `APP_VERSION` in `config.py`. Everything else reads it from there:
   the spec, the build scripts, the file names and the Info.plist.
2. Add the version to `CHANGELOG.md`.
3. `./venv/bin/python -m pytest` and `npm run check` — both clean.
4. `python3 scripts/check_private_data.py` — clean.
5. Commit, then tag:

   ```bash
   git tag -a v<version> -m "Health Ledger <version>"
   git push origin main --tags
   ```

6. The `release` workflow builds both platforms, starts each built app and
   waits for it to answer on `127.0.0.1:5099`, checks the macOS icon with
   `verify_icon.py`, and attaches the files to a draft GitHub Release. Check
   the draft, then publish it.

To build without tagging, run the workflow by hand from the Actions tab
(`workflow_dispatch`); that builds and uploads the files as workflow artifacts but drafts no release.

The separate `tests` workflow (`.github/workflows/ci.yml`) runs pytest, the
private-data scan, lint, typecheck, and checks that the committed CSS bundle
and compiled JS are current, on every push to `main` and every pull request.

## Cost

GitHub Actions is free for public repositories, with no minute cap, and
Releases hosting is free. A release build costs nothing. On a private
repository the same workflow would bill against the account's Actions
minutes — macOS runners at 10x the Linux rate — so keep releases on the
public repo.
