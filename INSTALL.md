# Installing Health Ledger

Two ways in: download the app, or run it from source. The app is the one to
pick unless you want to read and change the code.

## Download the app

Get the file for your computer from the
[Releases page](https://github.com/YOUR-USERNAME/health-ledger/releases/latest).

### macOS

1. Open the `.dmg` and drag **Health Ledger** into Applications.
2. **The first launch is different.** Do not double-click it. Right-click (or
   Control-click) the app and choose **Open**, then **Open** again in the
   dialog. After that once, it opens normally forever.

If you double-click first and macOS says the app *"cannot be opened because
the developer cannot be verified"*, close the dialog and do the right-click
step. If it says the app is **damaged and should be moved to the Bin**, macOS
has quarantined the download; clear the flag in Terminal:

```bash
xattr -dr com.apple.quarantine "/Applications/Health Ledger.app"
```

Requires macOS 11 (Big Sur) or newer. The `.dmg` is built for Apple Silicon
(`arm64`); on an Intel Mac, run from source instead.

### Windows

1. Unzip the `.zip` anywhere — your Desktop or Documents is fine.
2. Open the unzipped `HealthLedger` folder and run **HealthLedger.exe**.
3. Windows SmartScreen will say *"Windows protected your PC"*. Click
   **More info**, then **Run anyway**.

Keep the whole folder together. The `.exe` needs the files beside it.

### Why the warnings

Apple charges 99 USD a year and Microsoft several hundred for the
certificates that make those dialogs go away. Health Ledger is not signed with
either, so both systems warn that they cannot confirm who built it. The
warnings are about the missing signature, not about anything found in the app.

If that is not good enough for you — and it is a perfectly reasonable position
for something that will hold your medical records — run it from source, where
you can read every line first.

## Run it from source

You need [Python 3.9 or newer](https://www.python.org/downloads/). Git is
handy but you can download the source as a zip instead.

```bash
git clone https://github.com/YOUR-USERNAME/health-ledger.git
cd health-ledger
./start.sh            # macOS and Linux
```

On Windows, double-click `start.bat`.

The first run creates a private Python environment in `./venv`, installs what
it needs, starts the server on <http://127.0.0.1:5001> and opens your browser.
Every later run just starts it. `Ctrl+C` stops it.

To get the menu-bar icon and a **Quit** item, as the downloadable app has:

```bash
venv/bin/pip install -r packaging/requirements-build.txt
venv/bin/python desktop.py
```

### Choosing where records go

The first screen asks. To set it ahead of time, copy `.env.example` to `.env`
and edit it:

```text
HEALTH_LEDGER_DATA_DIR=~/Health Ledger
```

Keep that folder outside the source checkout, so no copy or commit can pick up
a record.

## Direct PDF generation (optional)

Health Ledger always offers **Open printable version**, which uses your
browser's own print window and its **Save as PDF**. That needs nothing extra
and is what the downloadable app uses.

Running from source, you can also install WeasyPrint's graphics libraries and
get **Generate PDF** buttons that write the file directly:

```bash
brew install pango                      # macOS
sudo apt install libpango-1.0-0 libpangoft2-1.0-0   # Debian, Ubuntu
```

On Windows, install GTK from the
[WeasyPrint instructions](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

These are C libraries, which is why they cannot be bundled into a
downloadable app. Without them nothing breaks: the buttons are simply replaced
by the printable version.

## Other optional extras

Reading scanned pages (OCR), DICOM images and PubMed lookups are handled by
scripts that need more packages. The file says which programs each one also
needs:

```bash
venv/bin/pip install -r requirements-extras.txt
```

## Uninstalling

Delete the app (Applications on a Mac, the unzipped folder on Windows), or the
source checkout.

Your records are **not** in either of those. They are in the folder you chose
on the first screen, and deleting the app leaves them alone. Delete that
folder too if you want them gone — and be sure you have a backup you are happy
with first, because nobody can recover it.

The app also keeps one small settings file recording where that folder is:

- macOS: `~/Library/Application Support/Health Ledger/.env`
- Windows: `%APPDATA%\Health Ledger\.env`
- Linux: `~/.config/health-ledger/.env`
- From source: `.env` in the checkout
