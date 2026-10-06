# Quick Start

Downloaded the app? Follow [INSTALL.md](../../INSTALL.md) and the first-five-minutes
list in the [README](../../README.md). This page is for running from source.

## Start it

```bash
./start.sh            # macOS and Linux
```

On Windows double-click `start.bat`. On a Mac you can double-click
`Health Ledger.command`. The first run creates `./venv` and installs
`requirements.txt`; every run then starts the server on
<http://127.0.0.1:5001> and opens your browser. `Ctrl+C` stops it.

To use another port, run the app yourself:

```bash
venv/bin/python app.py 8080
```

## What to do first

1. The first screen asks where to keep your records. Choose a folder, then
   **Start with an empty ledger**, or import a `.db` file you already have.
2. Open **Import** in the sidebar and add a file.
3. Look around: **Overview**, **Sources**, **Metrics**, **Summary**, **Query**,
   **References**, **Doctor Docs**, **Backup**. [WEB_INTERFACE.md](WEB_INTERFACE.md)
   says what each one is for.

If the page does not open, see
[the troubleshooting pages](../troubleshooting/README.md).
