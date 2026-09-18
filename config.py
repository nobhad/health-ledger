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
APP_VERSION = "1.0.0"
DEBUG = True
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# Project root. Every path below is anchored here so the app, the scripts and
# the tests all find the same files no matter which directory they run from
# (running `python3 app.py` from elsewhere used to create an empty database
# in the current directory and serve nothing).
BASE_DIR = Path(__file__).resolve().parent


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


_load_dotenv(BASE_DIR / '.env')

# Where the person's records live. Everything private — the database, the
# source documents, generated output, logs and backups — sits under this one
# directory, and it should be OUTSIDE the repository so no checkout, sync or
# commit can ever carry a record with it. HEALTH_LEDGER_DATA_DIR sets it (in
# the environment or in ./.env); unset, it falls back to the project folder,
# where those paths are git-ignored.
DATA_ROOT = Path(os.environ.get('HEALTH_LEDGER_DATA_DIR') or BASE_DIR).expanduser().resolve()

# Database configuration
# HEALTH_LEDGER_DB_PATH overrides the database location (used by the tests).
DB_PATH = Path(os.environ.get('HEALTH_LEDGER_DB_PATH') or DATA_ROOT / 'genetic_profile.db')
DB_SCHEMA_PATH = BASE_DIR / 'genetic_profile_db_schema.sql'

# Paths
OUTPUT_DIR = DATA_ROOT / 'output'
DOCS_DIR = BASE_DIR / 'docs'
SCRIPTS_DIR = BASE_DIR / 'scripts'
DATA_DIR = DATA_ROOT / 'data'
PRIMARY_SOURCES_DIR = DATA_ROOT / 'primary_sources'
LOGS_DIR = DATA_ROOT / 'logs'
BACKUPS_DIR = DATA_ROOT / 'backups'
DOCTOR_DOCS_DIR = OUTPUT_DIR / 'doctor_docs'  # Default folder for doctor PDFs

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

