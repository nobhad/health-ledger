#!/usr/bin/env python3
"""
Web application for querying the genetic profile database
Clean Flask app with proper structure

Features:
- Query interface for genes, traits, and health conditions
- Full profile document viewer
- Personalized summary viewer
- RESTful API endpoints for database queries
- Thread-safe database connections
- Comprehensive error handling and logging

Usage:
    python3 app.py [port]
    
    Default port: 5001
    Access at: http://localhost:5001
"""

from flask import Flask, render_template, jsonify, request, send_file, after_this_request, redirect, url_for
from werkzeug.utils import secure_filename
from database_manager import GeneticProfileDB
from pathlib import Path
import os
import sqlite3
import tempfile
import threading
import traceback
import config
from config import setup_logging, get_logger, DEFAULT_PORT, HOST, DEBUG, LOGS_DIR
from validation import (
    validate_gene_symbol, validate_condition_name, validate_trait_name,
    validate_list_param, create_error_response
)
from profile_generator import generate_profile_html
import ledger_setup
from doctor_templates import get_available_specialties, DOCTOR_TEMPLATES

# Set up logging
logger = setup_logging(str(LOGS_DIR / 'app.log'))
app_logger = get_logger('app')

app = Flask(__name__)
# No CORS. The pages and the API are served from the same origin, and a
# permissive CORS policy would let any website open in the browser read this
# medical data from http://127.0.0.1 while the server is running.

# Security headers to prevent accidental external exposure
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Log application startup
app_logger.info("=" * 60)
app_logger.info("HEALTH LEDGER WEB INTERFACE")
app_logger.info("=" * 60)

# Thread-local storage for database connections
_local = threading.local()


class PathOutsideDataDir(ValueError):
    """A request named a file location outside HEALTH_LEDGER_DATA_DIR."""


def resolve_data_path(user_path: str) -> Path:
    """
    Resolve a path supplied by a request to a location inside the data directory.

    Relative paths are taken from the data directory, so "backups/export.db"
    lands next to the other backups. Absolute paths are allowed only when they
    already point inside it. Anything else (a home path, "..", another disk)
    is refused: the server must never write records outside the folder the
    person chose for them.
    """
    data_root = Path(config.DATA_ROOT).resolve()
    candidate = Path(user_path).expanduser()
    if not candidate.is_absolute():
        candidate = data_root / candidate
    candidate = candidate.resolve()
    if candidate != data_root and data_root not in candidate.parents:
        raise PathOutsideDataDir(
            f"Path must be inside the data directory ({data_root}); got {user_path}"
        )
    return candidate

def get_db():
    """
    Get database connection for current thread.
    
    Creates a thread-local database connection to ensure thread safety.
    Each Flask request thread gets its own database connection.
    
    Returns:
        GeneticProfileDB: Database connection instance
    
    Raises:
        Exception: If database connection fails
    
    Example:
        >>> db = get_db()
        >>> genes = db.get_all_genes()
    """
    thread_id = threading.current_thread().ident
    app_logger.debug(f"Getting database connection for thread {thread_id}")
    
    if not hasattr(_local, 'db') or _local.db is None:
        app_logger.debug("Creating new database connection")
        _local.db = GeneticProfileDB()
        _local.thread_id = thread_id
    elif hasattr(_local, 'thread_id') and _local.thread_id != thread_id:
        # Thread changed, create new connection
        app_logger.debug(f"Thread changed from {_local.thread_id} to {thread_id}, creating new connection")
        if _local.db is not None:
            try:
                _local.db.close()
            except Exception as e:
                app_logger.warning(f"Error closing old database connection: {e}")
        _local.db = GeneticProfileDB()
        _local.thread_id = thread_id
    
    return _local.db

@app.teardown_appcontext
def close_db(error):
    """
    Close database connection at end of request.
    
    Called automatically by Flask after each request completes.
    Ensures database connections are properly closed to prevent leaks.
    
    Args:
        error: Any exception that occurred during request processing
    """
    if hasattr(_local, 'db') and _local.db is not None:
        try:
            app_logger.debug("Closing database connection")
            _local.db.close()
        except Exception as e:
            app_logger.warning(f"Error closing database connection: {e}")
        finally:
            _local.db = None
    
    if error:
        app_logger.error(f"Request error: {error}", exc_info=True)


# Template filters
@app.template_filter('temp_display')
def temp_display(value, unit):
    """
    Convert temperature to display format: Fahrenheit first, then Celsius.
    
    Args:
        value: Temperature value
        unit: Original unit ('F' or 'C')
    
    Returns:
        str: Formatted temperature string like "98.6°F (37.0°C)"
    """
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        if unit == 'F':
            # Already in Fahrenheit, convert to Celsius
            celsius = (value - 32) * 5 / 9
            return f"{value:.1f}°F ({celsius:.1f}°C)"
        elif unit == 'C':
            # Convert to Fahrenheit first, then show both
            fahrenheit = (value * 9 / 5) + 32
            return f"{fahrenheit:.1f}°F ({value:.1f}°C)"
        else:
            # Unknown unit, just return the value
            return f"{value:.1f}{unit}" if unit else f"{value:.1f}"
    except (ValueError, TypeError):
        return str(value) if value else "N/A"


# Routes
@app.route('/')
def index():
    """
    Overview page.

    What the ledger holds (counts by kind), the most recent sources, any
    metrics flagged abnormal, and when the last backup was made.

    Returns:
        str: Rendered HTML template
    """
    app_logger.info("Rendering overview")
    try:
        db = get_db()
        if ledger_setup.needs_setup(db.conn):
            # Nothing in the ledger and nobody has chosen to begin: the first
            # thing to see is the choice, not a page of zeros.
            return redirect(url_for('setup'))
        cursor = db.conn.cursor()

        def count(sql: str) -> int:
            cursor.execute(sql)
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

        stats = {
            'genes': count("SELECT COUNT(*) FROM genes"),
            'pharmacogenomic': count("SELECT COUNT(DISTINCT gene_id) FROM pharmacogenomic_data"),
            'traits': count("SELECT COUNT(*) FROM trait_associations"),
            'conditions': count("SELECT COUNT(*) FROM health_condition_associations"),
            'sources': count("SELECT COUNT(*) FROM primary_sources"),
            'findings': count("SELECT COUNT(*) FROM primary_source_findings"),
            'metrics': count("SELECT COUNT(*) FROM health_metrics"),
            'abnormal': count("SELECT COUNT(*) FROM health_metrics WHERE is_abnormal = 1"),
        }

        cursor.execute("""
            SELECT id, source_name, source_type, institution, document_date
            FROM primary_sources
            ORDER BY document_date DESC, id DESC
            LIMIT 5
        """)
        recent_sources = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT metric_name, metric_type, metric_value, metric_value_text, unit, collection_date
            FROM health_metrics
            WHERE is_abnormal = 1
            ORDER BY collection_date DESC
            LIMIT 5
        """)
        abnormal_metrics = [dict(row) for row in cursor.fetchall()]

        from scripts.backup_database import list_backups
        backups = list_backups()

        # The setup page has already shown where the records live; the
        # notice only confirms the step that was taken.
        notice = {
            'fresh': 'Your ledger is ready.',
            'imported': 'Your database was imported.',
            'restored': 'The backup was restored.',
        }.get(request.args.get('notice', ''))

        return render_template('overview.html',
                               stats=stats,
                               recent_sources=recent_sources,
                               abnormal_metrics=abnormal_metrics,
                               last_backup=backups[0] if backups else None,
                               backup_count=len(backups),
                               ledger_empty=not ledger_setup.ledger_has_content(db.conn),
                               notice=notice)
    except Exception as e:
        app_logger.error(f"Error rendering overview: {e}", exc_info=True)
        return f"Error loading page: {str(e)}", 500


# First run: import a database or start fresh
def _render_setup(error: str = None, status: int = 200):
    """The setup screen, with what the ledger holds now and the backups on disk."""
    from scripts.backup_database import list_backups
    db = get_db()
    # The folder field proposes what is configured, or a plainly named
    # folder in the home directory when nothing has been chosen yet.
    proposed = config.DATA_ROOT if config.DATA_DIR_IS_CONFIGURED else config.default_data_root()
    return render_template('setup.html',
                           current=ledger_setup.summarize(db.conn),
                           backups=list_backups(),
                           data_root=str(config.DATA_ROOT),
                           db_path=str(config.DB_PATH),
                           proposed_folder=request.form.get('data_folder') or str(proposed),
                           error=error), status


def _choose_data_folder(form) -> Path:
    """
    Apply the data folder named on the setup screen (blank means the
    proposed default), for this process and for the next launch.

    Raises ValueError with a sentence for the screen when the folder is
    unusable.
    """
    raw = (form.get('data_folder') or '').strip()
    folder = Path(raw).expanduser() if raw else config.default_data_root()
    if not folder.is_absolute():
        raise ValueError('Give the full path of the folder, starting from the top of the disk.')
    folder = folder.resolve()
    app_dir = Path(config.BASE_DIR).resolve()
    if folder == app_dir or app_dir in folder.parents:
        raise ValueError("Choose a folder outside the Health Ledger app folder, so your "
                         "records never travel with the app's code.")
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ValueError(f'That folder cannot be created: {e.strerror or e}.') from e
    if not os.access(folder, os.W_OK):
        raise ValueError('That folder cannot be written to. Choose another.')
    if folder != Path(config.DATA_ROOT).resolve() or not config.DATA_DIR_IS_CONFIGURED:
        previous_db = Path(config.DB_PATH)
        config.set_data_root(folder)
        config.save_data_root(folder)
        app_logger.info(f'Data folder set to {folder}')
        _discard_placeholder_db(previous_db, Path(config.DB_PATH))
    return folder


def _discard_placeholder_db(previous_db: Path, current_db: Path) -> None:
    """
    Before a folder is chosen the app falls back to its own directory, so a
    launch has already created an empty database there. Once the records
    have a home, that placeholder is removed; a database holding anything
    is never touched.
    """
    try:
        if previous_db.resolve() == current_db.resolve() or not previous_db.is_file():
            return
        if Path(config.BASE_DIR).resolve() not in previous_db.resolve().parents:
            return
        conn = sqlite3.connect(f'file:{previous_db}?mode=ro', uri=True)
        try:
            empty = not ledger_setup.ledger_has_content(conn)
        finally:
            conn.close()
        if not empty:
            return
        for suffix in ('', '-wal', '-shm'):
            leftover = previous_db.with_name(previous_db.name + suffix)
            if leftover.exists():
                leftover.unlink()
        app_logger.info(f'Removed the empty placeholder database at {previous_db}')
    except Exception as e:
        app_logger.warning(f'Could not remove the placeholder database {previous_db}: {e}')


@app.route('/setup')
def setup():
    """
    Getting started: import an existing Health Ledger database, restore a
    backup, or start with an empty ledger. The overview sends an empty,
    never-started ledger here; it stays reachable afterwards for restores.
    """
    try:
        return _render_setup()
    except Exception as e:
        app_logger.error(f"Error rendering setup: {e}", exc_info=True)
        return f"Error loading page: {str(e)}", 500


@app.route('/setup/browse', methods=['POST'])
def setup_browse():
    """
    Open this computer's folder picker for the setup screen and return the
    folder chosen. The server runs on the user's own machine, so the dialog
    appears in front of them; nothing is chosen on their behalf.
    """
    try:
        payload = request.get_json(silent=True) or {}
        initial = payload.get('current') or str(config.DATA_ROOT)
        chosen = ledger_setup.choose_folder(Path(initial))
        return jsonify({'folder': str(chosen) if chosen else None})
    except Exception as e:
        app_logger.warning(f"Folder picker unavailable: {e}")
        return jsonify({'error': str(e)}), 501


@app.route('/setup/start', methods=['POST'])
def setup_start():
    """Start fresh: keep the empty database and stop showing the setup screen."""
    try:
        _choose_data_folder(request.form)
        ledger_setup.ensure_data_directories()
        db = get_db()
        ledger_setup.mark_setup_completed(db.conn)
        app_logger.info("Setup: started with an empty ledger")
        return redirect(url_for('index', notice='fresh'))
    except ValueError as e:
        return _render_setup(error=str(e), status=400)
    except Exception as e:
        app_logger.error(f"Error starting fresh: {e}", exc_info=True)
        return _render_setup(error=f'Could not start the ledger: {e}', status=500)


@app.route('/setup/import', methods=['POST'])
def setup_import():
    """Import an uploaded .db file. It is checked before it replaces anything."""
    upload = request.files.get('database')
    if upload is None or not upload.filename:
        return _render_setup(error='Choose a database file first.', status=400)

    tmp_path = None
    try:
        # A first-run import also settles where the records live. Once the
        # ledger has content the folder is already chosen and the field is
        # not shown.
        if 'data_folder' in request.form:
            _choose_data_folder(request.form)
        ledger_setup.ensure_data_directories()
        # The upload lands inside the data directory, never in the system
        # temp folder, and is removed whether or not the import succeeds.
        fd, tmp_path = tempfile.mkstemp(prefix='import_', suffix='.db', dir=str(config.DATA_ROOT))
        os.close(fd)
        upload.save(tmp_path)
        summary = ledger_setup.import_database(Path(tmp_path))
        app_logger.info(f"Setup: imported {secure_filename(upload.filename)}: {summary}")
        return redirect(url_for('index', notice='imported'))
    except (ledger_setup.InvalidDatabase, ValueError) as e:
        return _render_setup(error=str(e), status=400)
    except Exception as e:
        app_logger.error(f"Error importing database: {e}", exc_info=True)
        return _render_setup(error=f'The import failed: {e}', status=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/setup/restore', methods=['POST'])
def setup_restore():
    """Restore one of the backups in the backups folder, by file name."""
    filename = secure_filename(request.form.get('filename', ''))
    # Look the backup up where backups are now, before a first-run folder
    # choice moves the data directory.
    backup_path = ledger_setup.find_backup(filename) if filename else None
    if backup_path is None:
        return _render_setup(error='That backup is no longer on disk.', status=404)
    try:
        if 'data_folder' in request.form:
            _choose_data_folder(request.form)
        summary = ledger_setup.import_database(backup_path)
        app_logger.info(f"Setup: restored {filename}: {summary}")
        return redirect(url_for('index', notice='restored'))
    except (ledger_setup.InvalidDatabase, ValueError) as e:
        return _render_setup(error=str(e), status=400)
    except Exception as e:
        app_logger.error(f"Error restoring backup: {e}", exc_info=True)
        return _render_setup(error=f'The restore failed: {e}', status=500)


@app.route('/query')
def query():
    """
    Query interface page.

    Renders the query interface template with searchable multiselect dropdowns
    for genes, traits, and health conditions.

    Returns:
        str: Rendered HTML template
    """
    app_logger.info("Rendering query interface")
    try:
        return render_template('query.html')
    except Exception as e:
        app_logger.error(f"Error rendering query interface: {e}", exc_info=True)
        return f"Error loading page: {str(e)}", 500


@app.route('/test')
def test():
    """
    Health check endpoint.
    
    Simple endpoint to verify the server is running and responsive.
    Useful for monitoring and debugging.
    
    Returns:
        JSON: Status object with 'ok' status and message
    
    Example:
        GET /test -> {"status": "ok", "message": "Server is working!"}
    """
    app_logger.debug("Health check requested")
    return jsonify({
        'status': 'ok',
        'message': 'Server is working!',
        'version': '1.0.0'
    })


@app.route('/api/genes-by-condition')
def genes_by_condition():
    """
    API endpoint: Get genes associated with a health condition.
    
    Query Parameters:
        condition (str, required): Name of the health condition to search for
    
    Returns:
        JSON: Array of gene objects associated with the condition
    
    Example:
        GET /api/genes-by-condition?condition=ADHD
        -> [{"gene_symbol": "ADRA2A", "gene_name": "...", ...}, ...]
    
    Error Responses:
        400: Missing or invalid condition parameter
        500: Database or server error
    """
    # Get condition parameter (can be string or list)
    condition_param = request.args.get('condition') or request.args.getlist('condition[]')
    
    if not condition_param:
        return create_error_response('Missing required parameter: condition', 400)
    
    # Validate and normalize to list
    is_valid, error_msg, conditions = validate_list_param(condition_param, 'condition', max_items=50)
    if not is_valid:
        return create_error_response(error_msg, 400)
    
    if not conditions:
        return create_error_response('At least one condition is required', 400)
    
    # Validate each condition
    validated_conditions = []
    for cond in conditions:
        is_valid, error_msg = validate_condition_name(cond)
        if not is_valid:
            return create_error_response(f"Invalid condition: {error_msg}", 400)
        validated_conditions.append(cond)
    
    app_logger.info(f"Querying genes for conditions: {validated_conditions}")
    
    try:
        db = get_db()
        all_results = []
        for cond in validated_conditions:
            genes = db.get_genes_with_condition(cond)
            all_results.extend(genes)
        
        # Deduplicate by gene_id
        seen = set()
        unique_results = []
        for gene in all_results:
            gene_id = gene.get('id')
            if gene_id and gene_id not in seen:
                seen.add(gene_id)
                unique_results.append(gene)
        
        app_logger.info(f"Found {len(unique_results)} unique genes for conditions: {validated_conditions}")
        return jsonify(unique_results)
    except Exception as e:
        app_logger.error(f"Error querying genes by condition: {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/genes-by-trait')
def genes_by_trait():
    """
    API endpoint: Get genes associated with a trait.
    
    Query Parameters:
        trait (str, required): Name of the trait to search for
    
    Returns:
        JSON: Array of gene objects associated with the trait
    
    Example:
        GET /api/genes-by-trait?trait=pain+sensitivity
        -> [{"gene_symbol": "COMT", "gene_name": "...", ...}, ...]
    
    Error Responses:
        400: Missing or invalid trait parameter
        500: Database or server error
    """
    trait = request.args.get('trait', '').strip()
    app_logger.info(f"Querying genes for trait: {trait}")
    
    if not trait:
        app_logger.warning("genes-by-trait called without trait parameter")
        return create_error_response('Missing required parameter: trait', 400)
    
    is_valid, error_msg = validate_trait_name(trait)
    if not is_valid:
        return create_error_response(f"Invalid trait: {error_msg}", 400)
    
    try:
        db = get_db()
        genes = db.get_genes_with_trait(trait)
        app_logger.info(f"Found {len(genes)} genes for trait '{trait}'")
        return jsonify(genes)
    except Exception as e:
        app_logger.error(f"Error querying genes by trait '{trait}': {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/gene-info')
def gene_info():
    """
    API endpoint: Get comprehensive information about a gene.
    
    Returns detailed information including traits, health conditions, interactions,
    and pharmacogenomic data for a specific gene.
    
    Query Parameters:
        gene (str, required): Gene symbol (e.g., "COMT", "ADRA2A")
    
    Returns:
        JSON: Gene information object with:
            - gene_symbol: Gene symbol
            - gene_name: Full gene name
            - chromosome: Chromosome location
            - traits: List of associated traits
            - health_conditions: List of associated health conditions
            - interacting_genes: List of interacting gene symbols
            - pharmacogenomic: Drug metabolism information (if available)
    
    Example:
        GET /api/gene-info?gene=COMT
        -> {
            "gene_symbol": "COMT",
            "gene_name": "Catechol-O-Methyltransferase",
            "traits": ["pain sensitivity", ...],
            ...
        }
    
    Error Responses:
        400: Missing or invalid gene parameter
        404: Gene not found
        500: Database or server error
    """
    gene_symbol = request.args.get('gene', '').strip()
    
    if not gene_symbol:
        return create_error_response('Missing required parameter: gene', 400)
    
    # Validate gene symbol
    is_valid, error_msg = validate_gene_symbol(gene_symbol)
    if not is_valid:
        return create_error_response(f"Invalid gene symbol: {error_msg}", 400)
    
    gene_symbol = gene_symbol.upper()
    app_logger.info(f"Querying comprehensive info for gene: {gene_symbol}")
    
    try:
        db = get_db()
        gene = db.get_gene_by_symbol(gene_symbol)
        
        if not gene:
            app_logger.warning(f"Gene '{gene_symbol}' not found")
            return create_error_response(f'Gene {gene_symbol} not found', 404)
        
        app_logger.debug(f"Found gene: {gene['gene_symbol']} - {gene['gene_name']}")
        
        # Get all related information
        app_logger.debug("Fetching trait associations")
        traits = db.get_trait_associations_for_gene(gene['id'])
        
        app_logger.debug("Fetching health condition associations")
        conditions = db.get_health_conditions_for_gene(gene['id'])
        
        app_logger.debug("Fetching gene-gene interactions")
        interactions = db.get_interacting_genes(gene_symbol)
        
        # Get pharmacogenomic data if available
        app_logger.debug("Fetching pharmacogenomic data")
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT 
                pd.metabolism_status,
                pd.genotype_phenotype,
                GROUP_CONCAT(gpd.drug_name) as affected_medications
            FROM pharmacogenomic_data pd
            LEFT JOIN gene_pharmacogenomic_drugs gpd ON pd.id = gpd.pharmacogenomic_data_id
            WHERE pd.gene_id = ?
            GROUP BY pd.id
        """, (gene['id'],))
        pharmacogenomic_row = cursor.fetchone()
        pharmacogenomic = dict(pharmacogenomic_row) if pharmacogenomic_row else None
        
        result = {
            'gene_symbol': gene['gene_symbol'],
            'gene_name': gene['gene_name'],
            'chromosome': gene.get('chromosome', ''),
            'traits': [t['trait_name'] for t in traits],
            'health_conditions': [c['condition_name'] for c in conditions],
            'interacting_genes': [i.get('interacting_gene_symbol', i.get('interacting_gene', '')) for i in interactions],
            'pharmacogenomic': pharmacogenomic
        }
        
        app_logger.info(f"Returning info for {gene_symbol}: {len(traits)} traits, {len(conditions)} conditions")
        return jsonify(result)
    except Exception as e:
        app_logger.error(f"Error querying gene info for '{gene_symbol}': {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/all-genes')
def all_genes():
    """
    API endpoint: Get all genes in the database.
    
    Returns a list of all genes with their basic information.
    Used to populate the gene multiselect dropdown.
    
    Returns:
        JSON: Array of gene objects with gene_symbol and gene_name
    
    Example:
        GET /api/all-genes
        -> [{"gene_symbol": "ADRA2A", "gene_name": "...", ...}, ...]
    
    Error Responses:
        500: Database or server error
    """
    app_logger.info("Fetching all genes")
    try:
        db = get_db()
        genes = db.get_all_genes()
        app_logger.info(f"Returning {len(genes)} genes")
        return jsonify(genes)
    except Exception as e:
        app_logger.error(f"Error fetching all genes: {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/pharmacogenomic')
def pharmacogenomic():
    """Get all pharmacogenomic data"""
    try:
        db = get_db()
        # Query pharmacogenomic data using SQL directly
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT 
                g.gene_symbol,
                g.gene_name,
                pd.metabolism_status,
                pd.genotype_phenotype,
                GROUP_CONCAT(gpd.drug_name) as affected_medications
            FROM genes g
            JOIN pharmacogenomic_data pd ON g.id = pd.gene_id
            LEFT JOIN gene_pharmacogenomic_drugs gpd ON pd.id = gpd.pharmacogenomic_data_id
            GROUP BY g.gene_symbol, g.gene_name, pd.metabolism_status, pd.genotype_phenotype
            ORDER BY g.gene_symbol
        """)
        results = [dict(row) for row in cursor.fetchall()]
        return jsonify(results)
    except Exception as e:
        app_logger.error(f"Error fetching pharmacogenomic data: {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/all-conditions')
def all_conditions():
    """
    API endpoint: Get all unique health conditions.
    
    Returns a list of all distinct health condition names in the database.
    Used to populate the condition multiselect dropdown.
    
    Returns:
        JSON: Array of condition name strings
    
    Example:
        GET /api/all-conditions
        -> ["ADHD", "Anxiety", "Depression", ...]
    
    Error Responses:
        500: Database or server error
    """
    app_logger.info("Fetching all health conditions")
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute("SELECT DISTINCT condition_name FROM health_condition_associations ORDER BY condition_name")
        conditions = [row[0] for row in cursor.fetchall()]
        app_logger.info(f"Returning {len(conditions)} unique health conditions")
        return jsonify(conditions)
    except Exception as e:
        app_logger.error(f"Error fetching all conditions: {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/api/all-traits')
def all_traits():
    """
    API endpoint: Get all unique traits.
    
    Returns a list of all distinct trait names in the database.
    Used to populate the trait multiselect dropdown.
    
    Returns:
        JSON: Array of trait name strings
    
    Example:
        GET /api/all-traits
        -> ["pain sensitivity", "stress response", ...]
    
    Error Responses:
        500: Database or server error
    """
    app_logger.info("Fetching all traits")
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute("SELECT DISTINCT trait_name FROM trait_associations ORDER BY trait_name")
        traits = [row[0] for row in cursor.fetchall()]
        app_logger.info(f"Returning {len(traits)} unique traits")
        return jsonify(traits)
    except Exception as e:
        app_logger.error(f"Error fetching all traits: {e}", exc_info=True)
        return create_error_response(
            'Internal server error',
            500,
            {'traceback': traceback.format_exc()} if DEBUG else None
        )


@app.route('/profile')
def profile():
    """
    Full genetic profile document page.
    
    Generates the complete genetic profile HTML from the database with all gene information,
    trait associations, health conditions, and references.
    
    Returns:
        str: Rendered HTML template with profile content
    
    Error Responses:
        500: Error generating profile from database
    
    Example:
        GET /profile -> Returns full profile page generated from database
    """
    app_logger.info("Generating full profile page from database")
    
    try:
        db = get_db()
        app_logger.debug("Generating profile HTML from database")
        profile_html = generate_profile_html(db)
        
        # Check if content is empty or missing
        if not profile_html or len(profile_html.strip()) < 100:
            app_logger.warning("Generated profile content appears to be empty or very short")
            return "Profile content is missing. Please check database.", 500
        
        app_logger.info("Profile generated successfully from database")
        return render_template('profile.html', profile_html=profile_html)
    except Exception as e:
        app_logger.error(f"Error generating profile from database: {e}", exc_info=True)
        return f"Error generating profile: {str(e)}", 500


@app.route('/summary')
def summary():
    """
    Personalized summary page.
    
    Generates a personalized summary from the database with key genetic findings, strengths,
    sensitivities, medication metabolism, and clinical recommendations.
    
    Returns:
        str: Rendered HTML template with summary content
    
    Error Responses:
        500: Error generating summary from database
    
    Example:
        GET /summary -> Returns personalized summary page generated from database
    """
    app_logger.info("Generating personalized summary from database")
    
    try:
        db = get_db()
        app_logger.debug("Generating summary HTML from database")
        
        from scripts.generate_personalized_summary import generate_summary_html
        
        summary_html = generate_summary_html(db)
        
        # Check if content is empty or missing
        if not summary_html or len(summary_html.strip()) < 100:
            app_logger.warning("Generated summary content appears to be empty or very short")
            return "Summary content is missing. Please check database.", 500
        
        app_logger.info("Summary generated successfully from database")
        return render_template('summary.html', summary_html=summary_html)
    except Exception as e:
        app_logger.error(f"Error generating summary from database: {e}", exc_info=True)
        return f"Error generating summary: {str(e)}", 500


@app.route('/metrics')
def metrics():
    """
    Health metrics page.
    
    Lists health metrics (vitals, lab values) with filters. Per-metric
    statistics live in the doctor documents; the page itself is the list.
    
    Returns:
        str: Rendered HTML template with metrics content
    
    Example:
        GET /metrics -> Returns health metrics page
        GET /metrics?metric_type=blood_pressure -> Filter by metric type
        GET /metrics?routine_only=true -> Show only routine visits
    """
    app_logger.info("Rendering metrics page")
    
    try:
        db = get_db()
        
        # Get filter parameters. Empty strings from the filter form mean "not set".
        metric_type = request.args.get('metric_type') or None
        start_date = request.args.get('start_date') or None
        end_date = request.args.get('end_date') or None
        # "Routine visits only" is a checkbox: an unchecked box sends nothing.
        # Default it on only when no filter form was submitted at all;
        # otherwise its absence means the user unchecked it.
        if request.args:
            routine_only = request.args.get('routine_only', '').lower() == 'true'
        else:
            routine_only = True
        
        # Get metrics
        metrics_data = db.get_health_metrics(
            metric_type=metric_type,
            routine_only=routine_only,
            start_date=start_date,
            end_date=end_date
        )
        
        # Metric type breakdown for the filter dropdown
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT metric_type, COUNT(*) as count,
                   COUNT(DISTINCT collection_date) as date_count
            FROM health_metrics
            GROUP BY metric_type
        """)
        metric_types = [dict(row) for row in cursor.fetchall()]
        
        app_logger.info(f"Retrieved {len(metrics_data)} metrics")
        return render_template('metrics.html',
                             metrics=metrics_data,
                             metric_types=metric_types,
                             current_metric_type=metric_type,
                             routine_only=routine_only,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        app_logger.error(f"Error rendering metrics: {e}", exc_info=True)
        return f"Error loading metrics: {str(e)}", 500


@app.route('/sources')
def sources():
    """Primary source browser page"""
    try:
        return render_template('sources.html')
    except Exception as e:
        app_logger.error(f"Error rendering sources page: {e}", exc_info=True)
        return f"Error loading sources page: {str(e)}", 500


@app.route('/api/sources')
def api_sources():
    """Get all primary sources with optional filtering"""
    try:
        db = get_db()
        source_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        if search:
            sources = db.search_primary_sources(search)
        elif source_type:
            sources = db.get_primary_sources_by_type(source_type)
        elif start_date or end_date:
            sources = db.get_primary_sources_by_date_range(start_date, end_date)
        else:
            sources = db.get_all_primary_sources()
        
        return jsonify({
            'success': True,
            'sources': sources,
            'count': len(sources)
        })
    except Exception as e:
        app_logger.error(f"Error fetching sources: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error fetching sources: {str(e)}'
        }), 500


@app.route('/api/sources/<int:source_id>')
def api_source_detail(source_id):
    """Get details for a specific primary source"""
    try:
        db = get_db()
        source = db.get_primary_source_with_findings(source_id)
        
        if not source:
            return jsonify({
                'success': False,
                'message': 'Source not found'
            }), 404
        
        return jsonify({
            'success': True,
            'source': source
        })
    except Exception as e:
        app_logger.error(f"Error fetching source {source_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error fetching source: {str(e)}'
        }), 500


@app.route('/api/sources/<int:source_id>/findings')
def api_source_findings(source_id):
    """Get findings for a specific primary source"""
    try:
        db = get_db()
        findings = db.get_primary_source_findings(source_id)
        
        return jsonify({
            'success': True,
            'findings': findings,
            'count': len(findings)
        })
    except Exception as e:
        app_logger.error(f"Error fetching findings for source {source_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error fetching findings: {str(e)}'
        }), 500


@app.route('/api/sources/<int:source_id>/text')
def api_source_text(source_id):
    """Get extracted text for a specific primary source"""
    try:
        db = get_db()
        text = db.get_primary_source_text(source_id)
        
        if text is None:
            return jsonify({
                'success': False,
                'message': 'Source not found or has no extracted text'
            }), 404
        
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        app_logger.error(f"Error fetching text for source {source_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error fetching text: {str(e)}'
        }), 500


def _new_temp_pdf_path() -> str:
    """Reserve a temporary .pdf path for a generated download."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        return tmp.name


def _send_temp_pdf(tmp_path: str, download_name: str):
    """
    Send a generated PDF as a download and delete the temp file afterwards.

    Flask streams the file after the view returns, so the cleanup is
    registered with after_this_request instead of running inline.
    """
    @after_this_request
    def _cleanup(response):
        try:
            os.unlink(tmp_path)
        except OSError as e:
            app_logger.warning(f"Could not delete temporary PDF {tmp_path}: {e}")
        return response
    
    return send_file(tmp_path, as_attachment=True,
                     download_name=download_name,
                     mimetype='application/pdf')


@app.route('/api/pdf/summary')
def api_pdf_summary():
    """Generate PDF from personalized summary"""
    try:
        from pdf_generator import generate_summary_pdf
        
        db = get_db()
        tmp_path = _new_temp_pdf_path()
        
        if generate_summary_pdf(db, tmp_path):
            return _send_temp_pdf(tmp_path, 'genetic_profile_summary.pdf')
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate PDF'
            }), 500
    except Exception as e:
        app_logger.error(f"Error generating summary PDF: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error generating PDF: {str(e)}'
        }), 500


@app.route('/api/pdf/profile')
def api_pdf_profile():
    """Generate PDF from full genetic profile"""
    try:
        from pdf_generator import generate_profile_pdf
        
        db = get_db()
        tmp_path = _new_temp_pdf_path()
        
        if generate_profile_pdf(db, tmp_path):
            return _send_temp_pdf(tmp_path, 'genetic_profile_full.pdf')
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate PDF'
            }), 500
    except Exception as e:
        app_logger.error(f"Error generating profile PDF: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error generating PDF: {str(e)}'
        }), 500


@app.route('/api/pdf/source/<int:source_id>')
def api_pdf_source(source_id):
    """Generate PDF from a primary source"""
    try:
        from pdf_generator import generate_source_pdf
        
        db = get_db()
        source = db.get_primary_source_with_findings(source_id)
        if not source:
            return jsonify({
                'success': False,
                'message': 'Source not found'
            }), 404
        
        tmp_path = _new_temp_pdf_path()
        
        if generate_source_pdf(db, source_id, tmp_path):
            # source_name is a file name from the records; keep the download
            # name to a single safe path segment.
            stem = secure_filename(Path(source.get('source_name') or 'source').stem) or 'source'
            return _send_temp_pdf(tmp_path, f"source_{source_id}_{stem}.pdf")
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate PDF'
            }), 500
    except Exception as e:
        app_logger.error(f"Error generating source PDF: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error generating PDF: {str(e)}'
        }), 500


@app.route('/api/pdf/doctor/<specialty>', methods=['GET', 'POST'])
def api_pdf_doctor(specialty):
    """Generate PDF for a specific doctor specialty"""
    try:
        from pdf_generator import generate_doctor_pdf
        from datetime import datetime
        
        specialty = specialty.lower()
        if specialty not in get_available_specialties():
            return jsonify({
                'success': False,
                'message': f"Unknown specialty '{specialty}'. Available: {', '.join(get_available_specialties())}"
            }), 404
        
        db = get_db()
        
        # Get patient name from database
        patient_name = db.get_patient_name()
        if not patient_name:
            # Fallback if no patient name found in database
            patient_name = "Patient"
            app_logger.warning("No patient name found in database, using default 'Patient'")
        
        # Get options from request (POST) or use defaults (GET)
        if request.method == 'POST':
            data = request.get_json() or {}
            save_path = data.get('save_path')
            include_original = data.get('include_original', True)
            include_medications = data.get('include_medications', True)
            include_stats = data.get('include_stats', True)
        else:
            save_path = None
            include_original = True
            include_medications = True
            include_stats = True
        
        # Generate filename: LastFirst_Specialty_YYYY-MM-DD.pdf
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{patient_name}_{specialty}_{today}.pdf"
        
        # Determine where to save the file
        if save_path:
            # User-specified folder, kept inside the data directory
            try:
                save_dir = resolve_data_path(save_path)
            except PathOutsideDataDir as e:
                return jsonify({'success': False, 'message': str(e)}), 400
            save_dir.mkdir(parents=True, exist_ok=True)
            final_path = save_dir / filename
        else:
            # Default folder
            config.DOCTOR_DOCS_DIR.mkdir(parents=True, exist_ok=True)
            final_path = config.DOCTOR_DOCS_DIR / filename
        
        # Generate PDF with options
        if generate_doctor_pdf(db, specialty, str(final_path), 
                               include_original=include_original,
                               include_medications=include_medications,
                               include_stats=include_stats):
            app_logger.info(f"PDF saved to: {final_path}")
            
            # Return file for download
            return send_file(str(final_path), as_attachment=True,
                           download_name=filename,
                           mimetype='application/pdf')
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate PDF'
            }), 500
    except Exception as e:
        app_logger.error(f"Error generating doctor PDF: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error generating PDF: {str(e)}'
        }), 500


def describe_specialties() -> list:
    """The doctor templates as the UI shows them, one entry per specialty."""
    described = []
    for specialty_id, template in DOCTOR_TEMPLATES.items():
        genes = template['genes']
        sections = template['sections']
        described.append({
            'id': specialty_id,
            'label': specialty_id.replace('_', ' ').title(),
            'title': template['title'],
            'genes': 'All genes' if genes == 'all' else ', '.join(genes),
            'sections': 'All sections' if sections == 'all'
                        else ', '.join(s.replace('_', ' ').title() for s in sections),
            'detail_level': template['detail_level'].title(),
        })
    return described


@app.route('/api/doctor-specialties')
def api_doctor_specialties():
    """The available doctor document templates"""
    return jsonify(describe_specialties())


@app.route('/doctor-docs')
def doctor_docs():
    """Doctor document generation interface"""
    try:
        return render_template('doctor_docs.html', specialties=describe_specialties())
    except Exception as e:
        app_logger.error(f"Error rendering doctor docs page: {e}", exc_info=True)
        return f"Error loading doctor docs page: {str(e)}", 500


@app.route('/backup')
def backup():
    """Backup interface page"""
    try:
        return render_template('backup.html')
    except Exception as e:
        app_logger.error(f"Error rendering backup page: {e}", exc_info=True)
        return f"Error loading backup page: {str(e)}", 500


@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create a timestamped backup of the database"""
    try:
        from scripts.backup_database import create_backup
        
        backup_path = create_backup()
        if backup_path:
            return jsonify({
                'success': True,
                'message': 'Backup created successfully',
                'path': backup_path
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create backup'
            }), 500
    except Exception as e:
        app_logger.error(f"Error creating backup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error creating backup: {str(e)}'
        }), 500


@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List all available backups"""
    try:
        from scripts.backup_database import list_backups
        
        backups = list_backups()
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        app_logger.error(f"Error listing backups: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error listing backups: {str(e)}'
        }), 500


@app.route('/api/backup/export', methods=['POST'])
def export_backup():
    """Export database to specified format"""
    try:
        from scripts.backup_database import export_database, export_to_json
        
        data = request.get_json() or {}
        format_type = data.get('format', 'db')
        output_path = data.get('path')
        
        if not output_path:
            return jsonify({
                'success': False,
                'message': 'Output path required'
            }), 400
        
        try:
            output_path = str(resolve_data_path(output_path))
        except PathOutsideDataDir as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        
        if format_type == 'json':
            success = export_to_json(output_path)
        else:
            success = export_database(output_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Database exported to {format_type}',
                'path': output_path
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to export database'
            }), 500
    except Exception as e:
        app_logger.error(f"Error exporting backup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error exporting backup: {str(e)}'
        }), 500


if __name__ == '__main__':
    import sys
    
    # Try port 5001 first (5000 is often used by AirPlay on macOS)
    port = DEFAULT_PORT
    
    # Check if port is specified as command line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            app_logger.info(f"Port specified via command line: {port}")
        except ValueError:
            app_logger.warning(f"Invalid port number: {sys.argv[1]}, using default {DEFAULT_PORT}")
            port = DEFAULT_PORT
    
    app_logger.info(f"Starting web server on {HOST}:{port}")
    app_logger.info(f"Access at: http://localhost:{port}")
    app_logger.info("Press Ctrl+C to stop the server")
    app_logger.warning("PRIVACY: Server is configured for localhost-only access (127.0.0.1)")
    app_logger.warning("PRIVACY: No external network access allowed")
    
    # Security: Only bind to localhost for privacy
    # This ensures the server is only accessible from the local machine
    try:
        app.run(debug=DEBUG, host=HOST, port=port, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e):
            app_logger.error(f"Port {port} is already in use!")
            app_logger.info(f"Try running with a different port: python3 app.py {port + 1}")
            app_logger.info(f"Or kill the process: lsof -ti:{port} | xargs kill -9")
            app_logger.info("On macOS, port 5000 is often used by AirPlay Receiver.")
            app_logger.info("Disable it in: System Settings → General → AirDrop & Handoff")
        else:
            app_logger.error(f"Error starting server: {e}", exc_info=True)
            raise

