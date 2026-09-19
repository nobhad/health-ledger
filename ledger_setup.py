#!/usr/bin/env python3
"""
First-run setup: is the ledger empty, and how does a database get into it.

A person who has just launched Health Ledger has one of two situations. They
have a database already (a backup, an export, a copy from another computer)
and want it here; or they have nothing yet and want to begin. The overview
sends an empty, never-started ledger to the setup screen, and the functions
here do the work behind that screen's two buttons.

Importing goes through SQLite's online backup API rather than copying the
file: the current database is in WAL mode, so a plain copy could pair a new
main file with a stale write-ahead log. The API replaces the contents in one
consistent step and leaves the journal in order.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import config
from config import get_logger

logger = get_logger('setup')

SQLITE_HEADER = b'SQLite format 3\x00'

# Tables a Health Ledger database always has. A file without them is some
# other SQLite database and is refused before it can replace anything.
REQUIRED_TABLES = ('genes', 'primary_sources')

# Tables whose row counts say whether the ledger holds anything.
CONTENT_TABLES = ('genes', 'primary_sources', 'health_metrics', 'trait_associations',
                  'health_condition_associations')

SETUP_COMPLETED_KEY = 'setup_completed_at'


class InvalidDatabase(ValueError):
    """The file offered for import is not a Health Ledger database."""


@dataclass
class DatabaseSummary:
    genes: int
    sources: int
    metrics: int

    @property
    def is_empty(self) -> bool:
        return self.genes == 0 and self.sources == 0 and self.metrics == 0


def _count(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0]) if row and row[0] is not None else 0


def summarize(conn: sqlite3.Connection) -> DatabaseSummary:
    """Row counts that describe a database in one line."""
    return DatabaseSummary(
        genes=_count(conn, 'genes'),
        sources=_count(conn, 'primary_sources'),
        metrics=_count(conn, 'health_metrics'),
    )


def ledger_has_content(conn: sqlite3.Connection) -> bool:
    return any(_count(conn, table) for table in CONTENT_TABLES)


def setup_completed(conn: sqlite3.Connection) -> bool:
    """True once the person chose to start fresh (or a database was imported)."""
    try:
        row = conn.execute(
            'SELECT value FROM app_settings WHERE key = ?', (SETUP_COMPLETED_KEY,)
        ).fetchone()
    except sqlite3.OperationalError:
        return False
    return bool(row and row[0])


def needs_setup(conn: sqlite3.Connection) -> bool:
    """An empty ledger nobody has started yet belongs on the setup screen."""
    return not ledger_has_content(conn) and not setup_completed(conn)


def mark_setup_completed(conn: sqlite3.Connection) -> None:
    conn.execute(
        'INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
        (SETUP_COMPLETED_KEY, datetime.now().isoformat(timespec='seconds')),
    )
    conn.commit()


def ensure_data_directories() -> None:
    """The folders the app writes into, created so the first run finds them."""
    for directory in (config.DATA_ROOT, config.PRIMARY_SOURCES_DIR, config.OUTPUT_DIR,
                      config.LOGS_DIR, config.BACKUPS_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)


def inspect_database(path: Path) -> DatabaseSummary:
    """
    Check that a file is a healthy Health Ledger database and describe it.

    Raises InvalidDatabase with a sentence the person can act on.
    """
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise InvalidDatabase('The file is empty.')
    with path.open('rb') as fh:
        if fh.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            raise InvalidDatabase(
                'That is not a SQLite database. Health Ledger imports the .db file '
                'it creates: a backup or an export.'
            )
    try:
        conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    except sqlite3.Error as e:
        raise InvalidDatabase(f'The database could not be opened: {e}') from e
    try:
        check = conn.execute('PRAGMA quick_check').fetchone()
        if not check or check[0] != 'ok':
            raise InvalidDatabase('The database file is damaged and cannot be imported.')
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
        missing = [t for t in REQUIRED_TABLES if t not in tables]
        if missing:
            raise InvalidDatabase(
                'That SQLite file is not a Health Ledger database '
                f'(no {", ".join(missing)} table).'
            )
        return summarize(conn)
    except sqlite3.DatabaseError as e:
        raise InvalidDatabase(f'The database could not be read: {e}') from e
    finally:
        conn.close()


def import_database(source: Path, backup_current: bool = True) -> DatabaseSummary:
    """
    Replace the ledger's database with the one at `source`.

    The file is validated first. If the current database holds anything and
    `backup_current` is set, a timestamped backup is made before it is
    replaced, so an import is never the only copy of what was there.
    Returns the summary of what was imported.
    """
    source = Path(source)
    summary = inspect_database(source)

    ensure_data_directories()
    target = Path(config.DB_PATH)

    if backup_current and target.exists():
        current = sqlite3.connect(target)
        try:
            had_content = ledger_has_content(current)
        finally:
            current.close()
        if had_content:
            from scripts.backup_database import create_backup
            backup_path = create_backup()
            if not backup_path:
                raise RuntimeError('The current database could not be backed up, so it was not replaced.')
            logger.info(f'Backed up the current database before import: {backup_path}')

    src = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
    dest = sqlite3.connect(target)
    try:
        src.backup(dest)
        # The imported file marks the ledger as set up; it has content or the
        # person chose it on purpose, and either way the setup screen is done.
        dest.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)')
        mark_setup_completed(dest)
    finally:
        src.close()
        dest.close()

    logger.info(f'Imported database: {summary.genes} genes, {summary.sources} sources, '
                f'{summary.metrics} metrics')
    return summary


def find_backup(filename: str) -> Optional[Path]:
    """A backup by its file name, or None if no such backup is on disk."""
    from scripts.backup_database import list_backups
    for backup in list_backups():
        if backup['filename'] == filename:
            return Path(backup['path'])
    return None


def choose_folder(initial: Optional[Path] = None) -> Optional[Path]:
    """
    Open this computer's own folder picker and return the folder chosen,
    or None if the picker was cancelled.

    The server only ever runs on the user's machine (it binds to
    127.0.0.1), so the dialog opens in front of the person clicking. macOS
    uses the system chooser through osascript, Windows the
    FolderBrowserDialog through PowerShell, Linux zenity or kdialog when one
    is installed. Raises RuntimeError when no picker is available, so the
    screen can say to type the path instead.
    """
    import shutil
    import subprocess
    import sys

    prompt = 'Choose where Health Ledger keeps your records'
    start = Path(initial).expanduser() if initial else Path.home()
    if not start.is_dir():
        start = Path.home()

    if sys.platform == 'darwin':
        location = str(start).replace('\\', '\\\\').replace('"', '\\"')
        script = (f'POSIX path of (choose folder with prompt "{prompt}" '
                  f'default location POSIX file "{location}")')
        result = subprocess.run(['osascript', '-e', script],
                                capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            if 'User canceled' in result.stderr or '-128' in result.stderr:
                return None
            raise RuntimeError(result.stderr.strip() or 'The folder picker could not open.')
        chosen = result.stdout.strip()
        return Path(chosen) if chosen else None

    if sys.platform.startswith('win'):
        location = str(start).replace("'", "''")
        script = ('Add-Type -AssemblyName System.Windows.Forms; '
                  '$d = New-Object System.Windows.Forms.FolderBrowserDialog; '
                  f"$d.Description = '{prompt}'; "
                  f"$d.SelectedPath = '{location}'; "
                  'if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) '
                  '{ Write-Output $d.SelectedPath }')
        result = subprocess.run(['powershell', '-NoProfile', '-STA', '-Command', script],
                                capture_output=True, text=True, timeout=600)
        chosen = result.stdout.strip()
        return Path(chosen) if chosen else None

    for command in (
        ['zenity', '--file-selection', '--directory', f'--title={prompt}', f'--filename={start}/'],
        ['kdialog', '--getexistingdirectory', str(start), '--title', prompt],
    ):
        if shutil.which(command[0]):
            result = subprocess.run(command, capture_output=True, text=True, timeout=600)
            chosen = result.stdout.strip()
            return Path(chosen) if result.returncode == 0 and chosen else None

    raise RuntimeError('No folder picker is available on this system. Type the folder path instead.')
