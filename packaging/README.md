# Packaging and releases

How the downloadable Health Ledger apps are built.

## What is here

| File | Does |
| --- | --- |
| `health_ledger.spec` | The PyInstaller build. Shared by both platforms. |
| `build_macos.sh` | Builds `Health Ledger.app`, wraps it in a `.dmg`. |
| `build_windows.ps1` | Builds `HealthLedger.exe`, wraps it in a `.zip`. |
| `make_icons.py` | Draws `icon.png`, `icon.icns` and `icon.ico`. |
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

Output lands in `dist/`:

```text
dist/HealthLedger-1.0.0-macOS-arm64.dmg      ~37 MB
dist/HealthLedger-1.0.0-windows-x64.zip
```

Both `build/` and `dist/` are git-ignored. **A Mac cannot build the Windows
executable and vice versa** — PyInstaller bundles a platform's own Python
runtime. Use the GitHub Actions workflow for the pair.

## Two decisions worth knowing

### WeasyPrint is excluded on purpose

WeasyPrint is a binding onto Pango/GTK, which are C libraries. Shipping them
inside a bundle means relocating a good part of Homebrew and fixing every
dylib path, and it breaks on the next OS update.

The app already degrades without it — `pdf_generator.pdf_unavailable_reason()`
reports why, the `/api/pdf/*` routes answer 503 with a plain message and a
`print_url`, and Doctor Docs offers **Open printable version** instead. The
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
   git tag -a v1.0.0 -m "Health Ledger 1.0.0"
   git push origin main --tags
   ```

6. The `release` workflow builds both platforms and attaches them to a draft
   GitHub Release. Check the draft, then publish it.

To build without tagging, run the workflow by hand from the Actions tab
(`workflow_dispatch`).

## Cost

GitHub Actions is free for public repositories, with no minute cap, and
Releases hosting is free. A release build costs nothing. On a private
repository the same workflow would bill against the account's Actions
minutes — macOS runners at 10x the Linux rate — so keep releases on the
public repo.
