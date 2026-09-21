#!/usr/bin/env python3
"""
Configuration and logging setup for the Health Ledger application
"""

import logging
import os
import sys
from pathlib import Path

# Application configuration
APP_NAME = "Health Ledger"

# Printed at the foot of every generated document (doctor documents, summary,
# profile, single-source PDFs and the printable web version). Kept identical to
# the note in templates/footer.html so a printed copy carries what the screen
# already says.
DOCUMENT_DISCLAIMER = (
    "For personal record-keeping. Not a substitute for professional medical advice."
)
APP_VERSION = "1.0.0"

# A copy running from a PyInstaller bundle sees two different roots: the
# read-only bundle it was unpacked into, and a writable folder of its own for
# settings. Run from a checkout the two are the same directory, which is why
# every path below is derived from one of these names rather than __file__.
IS_FROZEN = bool(getattr(sys, 'frozen', False))

# Read-only application resources: templates, static files, the schema.
# PyInstaller unpacks them under sys._MEIPASS; a checkout has them beside
# this file.
BASE_DIR = Path(getattr(sys, '_MEIPASS', None) or Path(__file__).resolve().parent).resolve()

# The folder the setup screen proposes when nothing has been chosen yet: a
# plainly named folder in the person's home, never the app's own folder.
DEFAULT_DATA_DIR_NAME = 'Health Ledger'


def _user_config_dir() -> Path:
    """The per-user folder a packaged copy keeps its settings in."""
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / APP_NAME
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming') / APP_NAME
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'health-ledger'


# Where settings are written. A checkout keeps them in the checkout, in the
# git-ignored .env. A packaged copy cannot: its bundle is read-only and is
# replaced wholesale by the next version, so the choice would not survive.
CONFIG_DIR = _user_config_dir() if IS_FROZEN else BASE_DIR
ENV_PATH = CONFIG_DIR / '.env'


def _load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines from a .env file into os.environ (never overriding
    variables already set). No dependency; the file is git-ignored."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = os.path.expanduser(value)


_load_dotenv(ENV_PATH)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


# Debug stays off unless HEALTH_LEDGER_DEBUG asks for it, and it must never
# default on in a copy someone downloaded: Flask's debug mode serves the
# Werkzeug interactive debugger, which will run arbitrary code for anything
# that can reach the port.
DEBUG = _env_flag('HEALTH_LEDGER_DEBUG')
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# Where the person's records live. Everything private -- the database, the
# source documents, generated output, logs and backups -- sits under this one
# directory, and it should be OUTSIDE the repository so no checkout, sync or
# commit can ever carry a record with it. HEALTH_LEDGER_DATA_DIR sets it (in
# the environment or in the .env above).
DATA_DIR_IS_CONFIGURED = bool(os.environ.get('HEALTH_LEDGER_DATA_DIR'))

# Unset, a checkout falls back to the checkout itself, where those paths are
# git-ignored. A packaged copy must not: its BASE_DIR is a temporary unpack
# directory that is deleted when the app quits, and the records would go with
# it. It falls back to the same folder the setup screen proposes.
_DATA_ROOT_FALLBACK = (Path.home() / DEFAULT_DATA_DIR_NAME) if IS_FROZEN else BASE_DIR
DATA_ROOT = Path(os.environ.get('HEALTH_LEDGER_DATA_DIR')
                 or _DATA_ROOT_FALLBACK).expanduser().resolve()

DB_SCHEMA_PATH = BASE_DIR / 'genetic_profile_db_schema.sql'
DOCS_DIR = BASE_DIR / 'docs'
SCRIPTS_DIR = BASE_DIR / 'scripts'


def default_data_root() -> Path:
    return Path.home() / DEFAULT_DATA_DIR_NAME


def set_data_root(path) -> Path:
    """
    Point every private path at `path` for the running process.

    The setup screen calls this when the person chooses where their records
    live. Everything derived from the data directory is recomputed here, so
    a module must read these names from `config` at call time rather than
    import them by value.
    """
    global DATA_ROOT, DB_PATH, OUTPUT_DIR, DATA_DIR, PRIMARY_SOURCES_DIR
    global LOGS_DIR, BACKUPS_DIR, DOCTOR_DOCS_DIR
    DATA_ROOT = Path(path).expanduser().resolve()
    # HEALTH_LEDGER_DB_PATH overrides the database location (used by the tests).
    DB_PATH = Path(os.environ.get('HEALTH_LEDGER_DB_PATH') or DATA_ROOT / 'genetic_profile.db')
    OUTPUT_DIR = DATA_ROOT / 'output'
    DATA_DIR = DATA_ROOT / 'data'
    PRIMARY_SOURCES_DIR = DATA_ROOT / 'primary_sources'
    LOGS_DIR = DATA_ROOT / 'logs'
    BACKUPS_DIR = DATA_ROOT / 'backups'
    DOCTOR_DOCS_DIR = OUTPUT_DIR / 'doctor_docs'  # Default folder for doctor PDFs
    return DATA_ROOT


def save_data_root(path) -> Path:
    """
    Record the chosen data directory in the git-ignored .env so the next
    launch finds it. Other lines in the file are kept; an existing
    HEALTH_LEDGER_DATA_DIR line is replaced.
    """
    global DATA_DIR_IS_CONFIGURED
    value = str(Path(path).expanduser().resolve())
    line = f'HEALTH_LEDGER_DATA_DIR={value}'
    lines = ENV_PATH.read_text(encoding='utf-8').splitlines() if ENV_PATH.is_file() else []
    replaced = False
    for i, raw in enumerate(lines):
        if raw.split('=', 1)[0].strip() == 'HEALTH_LEDGER_DATA_DIR' and not raw.lstrip().startswith('#'):
            lines[i] = line
            replaced = True
    if not replaced:
        if not lines:
            lines = ['# Local settings for this machine. Git-ignored.',
                     '# All private data (database, primary_sources, output, logs, backups) lives here:']
        lines.append(line)
    # A packaged copy writes this into a per-user folder that may not exist yet.
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    os.environ['HEALTH_LEDGER_DATA_DIR'] = value
    DATA_DIR_IS_CONFIGURED = True
    return ENV_PATH


set_data_root(DATA_ROOT)

# Patient information for PDF naming
# Will be auto-detected from database primary_sources table
# Format: LastFirst (e.g., "SmithJohn")

# Flask configuration
DEFAULT_PORT = 5001
HOST = '127.0.0.1'  # Localhost-only for privacy
ALLOW_EXTERNAL_ACCESS = False

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(log_file=None, level=LOG_LEVEL):
    """
    Set up logging configuration for the application.
    
    Args:
        log_file (str, optional): Path to log file. If None, logs only to console.
        level (int): Logging level (default: LOG_LEVEL from config)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        >>> logger = setup_logging('app.log')
        >>> logger.info("Application started")
    """
    # Create logger
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None):
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str, optional): Logger name. If None, returns root logger.
    
    Returns:
        logging.Logger: Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
    """
    if name is None:
        name = APP_NAME
    return logging.getLogger(f"{APP_NAME}.{name}")

# Initialize root logger
root_logger = setup_logging()

