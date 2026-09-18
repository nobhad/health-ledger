#!/usr/bin/env bash
# Health Ledger launcher for macOS and Linux.
#
#   ./start.sh          (or double-click "Health Ledger.command" on a Mac)
#
# First run: creates ./venv and installs requirements. Every run: starts the
# local server on http://127.0.0.1:5001 and opens it in your browser.
# The server only listens on this machine. Ctrl+C stops it.
set -euo pipefail
cd "$(dirname "$0")"

URL="http://127.0.0.1:5001"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install it from https://www.python.org/downloads/ and run this again."
    exit 1
fi

if [ ! -x venv/bin/python ]; then
    echo "First run: setting up a private Python environment in ./venv ..."
    python3 -m venv venv
fi

if [ ! -f venv/.installed ] || [ requirements.txt -nt venv/.installed ]; then
    echo "Installing requirements ..."
    venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
    touch venv/.installed
fi

# Homebrew libraries for WeasyPrint (PDF generation) on macOS
if [[ "$OSTYPE" == darwin* ]]; then
    export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"
fi

# Open the browser once the server is up
(
    sleep 2
    if [[ "$OSTYPE" == darwin* ]]; then
        open "$URL"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1
    fi
) &

echo "Health Ledger is starting at $URL  (Ctrl+C to stop)"
exec venv/bin/python app.py 5001
