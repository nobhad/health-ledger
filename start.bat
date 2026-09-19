@echo off
REM Health Ledger launcher for Windows. Double-click this file.
REM First run: creates .\venv and installs requirements. Every run: starts the
REM local server on http://127.0.0.1:5001 and opens it in your browser.
REM PDF files need GTK (see README.md); without it, Doctor Docs offers a printable version.
REM Optional script extras (OCR, DICOM, PubMed): venv\Scripts\pip install -r requirements-extras.txt
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python 3 is required. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist venv\Scripts\python.exe (
    echo First run: setting up a private Python environment in .\venv ...
    python -m venv venv
)

if not exist venv\.installed (
    echo Installing requirements ...
    venv\Scripts\pip install -q --disable-pip-version-check -r requirements.txt
    if errorlevel 1 ( pause & exit /b 1 )
    type nul > venv\.installed
)

start "" http://127.0.0.1:5001
echo Health Ledger is starting at http://127.0.0.1:5001  (close this window or press Ctrl+C to stop)
venv\Scripts\python app.py 5001
pause
