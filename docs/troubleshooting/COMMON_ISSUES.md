# Common Issues

## The browser did not open, or the page will not load

Go to <http://127.0.0.1:5001> yourself. The server only listens on
`127.0.0.1`, so an address using another machine's name will not work.

If another program is using port 5001:

- The downloaded app, and `desktop.py`, use the next free port. The menu-bar or
  tray icon shows the address.
- `start.sh`, `start.bat` and `app.py` always use 5001 unless you give a port,
  for example `venv/bin/python app.py 5002`. When the port is taken the server
  says "Port 5001 is already in use" in the terminal.

To see what is using a port on a Mac or Linux:

```bash
lsof -i:5001
```

On macOS, AirPlay Receiver is often using port 5000, which is why the app
defaults to 5001.

## Check the server is running

With the app running, this should return JSON containing `"status": "ok"`
and the app version:

```bash
curl http://127.0.0.1:5001/test
```

If it does, the server is fine and the problem is in the browser: try a private
window, another browser, or turn off an extension that blocks local addresses.

## The first screen appears again, or the ledger looks empty

The app looks for `genetic_profile.db` in your data folder. If the data
folder setting is missing or points somewhere else, it starts a new empty
ledger there. Check the `HEALTH_LEDGER_DATA_DIR` line in the settings file
([INSTALL.md](../../INSTALL.md) lists where it is). To bring a database back,
use **Import a database** on that screen, or **Import or restore** from the
Import page.

## "Module not found" or an import error when running from source

Install the requirements into the project's environment:

```bash
venv/bin/pip install -r requirements.txt
```

On Windows use `venv\Scripts\pip`. Running `start.sh` or `start.bat` does this
for you on the first run.

## Import says it cannot read the file

- **`.xyz is not a kind this page reads. Choose a PDF or a text file.`** The
  document form takes `.pdf`, `.txt`, `.log`, `.md` and `.csv`. DNA raw-data
  files go in the **DNA raw data** form.
- **A scanned PDF shows "no text could be read".** It has no text layer. It is
  kept, but cannot be searched, unless you install the OCR extras
  ([INSTALL.md](../../INSTALL.md)).
- **`The zip file should hold one raw-data file`.** Unzip it and choose the
  file inside, or use the zip exactly as the DNA service gave it.

## Generate PDF is missing

The PDF library needs system libraries the downloadable app cannot carry. Use
**Open printable version** and choose **Save as PDF** in the print window. To
get **Generate PDF**, see "Direct PDF generation" in
[INSTALL.md](../../INSTALL.md).

## A journal lookup fails

The References page needs an internet connection for **Look up** and **Fetch
abstract**. A failed lookup says "Could not reach the journal index", "took too
long to answer" or "answered with an error", and always adds "Nothing was
saved." Saved articles keep working offline.

## Database is locked

A "database is locked" error means another process has the file open. Quit
other copies of the app and any other program that has `genetic_profile.db`
open. Do not delete the
`genetic_profile.db-wal` or `genetic_profile.db-shm` files next to it: while
the app is running, recent changes can be in the `-wal` file and not yet in
the main file.
