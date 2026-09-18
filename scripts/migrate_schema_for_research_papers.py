#!/usr/bin/env python3
"""
Migration script to add research paper support to database schema
- Adds UNIQUE constraints on pubmed_id and doi
- Adds pdf_file_path columns to citations and research_references
- Adds indexes for faster lookups
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH, get_logger

logger = get_logger('migration')


def migrate_schema():
    """Apply schema migrations for research paper support"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        logger.info("Starting schema migration for research paper support...")
        
        # Check if pdf_file_path column exists in citations
        cursor.execute("PRAGMA table_info(citations)")
        citations_columns = [col[1] for col in cursor.fetchall()]
        
        if 'pdf_file_path' not in citations_columns:
            logger.info("Adding pdf_file_path column to citations table...")
            cursor.execute("ALTER TABLE citations ADD COLUMN pdf_file_path TEXT")
        
        # Check if pdf_file_path column exists in research_references
        cursor.execute("PRAGMA table_info(research_references)")
        ref_columns = [col[1] for col in cursor.fetchall()]
        
        if 'pdf_file_path' not in ref_columns:
            logger.info("Adding pdf_file_path column to research_references table...")
            cursor.execute("ALTER TABLE research_references ADD COLUMN pdf_file_path TEXT")
        
        # Create unique indexes (SQLite doesn't support ALTER TABLE ADD UNIQUE)
        # Instead, we'll create unique indexes which enforce uniqueness
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_citations_pubmed_id_unique ON citations(pubmed_id) WHERE pubmed_id IS NOT NULL")
            logger.info("Created unique index on citations.pubmed_id")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Could not create unique index on citations.pubmed_id: {e}")
        
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_citations_doi_unique ON citations(doi) WHERE doi IS NOT NULL")
            logger.info("Created unique index on citations.doi")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Could not create unique index on citations.doi: {e}")
        
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_research_references_pubmed_id_unique ON research_references(pubmed_id) WHERE pubmed_id IS NOT NULL")
            logger.info("Created unique index on research_references.pubmed_id")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Could not create unique index on research_references.pubmed_id: {e}")
        
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_research_references_doi_unique ON research_references(doi) WHERE doi IS NOT NULL")
            logger.info("Created unique index on research_references.doi")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Could not create unique index on research_references.doi: {e}")
        
        # Add indexes for faster lookups (if they don't exist)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_doi_lookup ON citations(doi)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_references_doi_lookup ON research_references(doi)")
            logger.info("Created lookup indexes on doi columns")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"Could not create lookup indexes: {e}")
        
        conn.commit()
        logger.info("Schema migration completed successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error during schema migration: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = migrate_schema()
    sys.exit(0 if success else 1)

