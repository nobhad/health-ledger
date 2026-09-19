#!/usr/bin/env python3
"""
Health Ledger Database Manager

Handles all database operations for genetic profile data including:
- Gene, SNP, and genotype management
- Trait and health condition associations
- Gene-gene interactions
- Pharmacogenomic data
- Citation and reference management
- Research findings

The database uses SQLite with WAL (Write-Ahead Logging) mode for better
concurrency and thread safety. All methods return dictionaries for easy
JSON serialization.

Example:
    >>> db = GeneticProfileDB()
    >>> gene = db.get_gene_by_symbol("COMT")
    >>> traits = db.get_trait_associations_for_gene(gene['id'])
    >>> db.close()
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import variant_reference

try:
    import config
    from config import get_logger
    logger = get_logger('database_manager')
except ImportError:
    import logging
    config = None
    logger = logging.getLogger(__name__)


class GeneticProfileDB:
    """
    Database manager for genetic profile data.
    
    Provides a high-level interface for all genetic profile database operations.
    Thread-safe when used with thread-local storage in Flask applications.
    
    Attributes:
        db_path (str): Path to the SQLite database file
        conn (sqlite3.Connection): Database connection object
    
    Example:
        >>> db = GeneticProfileDB()
        >>> genes = db.get_all_genes()
        >>> db.close()
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path (str, optional): Path to SQLite database file. Defaults to
                config.DB_PATH (the project's genetic_profile.db), so the same
                database is opened regardless of the current working directory.
        
        Raises:
            sqlite3.Error: If database connection fails
        
        Example:
            >>> db = GeneticProfileDB("my_database.db")
        """
        if db_path is None:
            db_path = str(config.DB_PATH) if config is not None else "genetic_profile.db"
        self.db_path = str(db_path)
        self.conn = None
        logger.debug(f"Initializing database connection to {db_path}")
        self._connect()
    
    def _connect(self):
        """
        Connect to SQLite database with thread-safe configuration.
        
        Configures:
        - check_same_thread=False: Allows connections from different threads
        - row_factory=sqlite3.Row: Returns rows as dictionaries
        - WAL mode: Better concurrency for read/write operations
        
        Note:
            This is safe when using thread-local storage in Flask applications.
            Each request thread gets its own connection.
        """
        try:
            # Use check_same_thread=False to allow connections from different threads
            # This is safe when using thread-local storage in Flask
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self.conn.execute('PRAGMA journal_mode=WAL')
            logger.debug("Database connection established with WAL mode")
            self._initialize_schema()
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _initialize_schema(self):
        """
        Initialize database schema from SQL file.
        
        Reads and executes the schema file if it exists. Creates all tables,
        indexes, and views defined in genetic_profile_db_schema.sql.
        
        Note:
            Schema initialization is idempotent - safe to call multiple times.
            Existing tables are not recreated.
        """
        schema_file = Path(__file__).parent / "genetic_profile_db_schema.sql"
        if schema_file.exists():
            try:
                with open(schema_file, 'r') as f:
                    schema = f.read()
                
                # Execute schema as script (handles multiple statements)
                # SQLite's executescript handles CREATE IF NOT EXISTS properly
                try:
                    self.conn.executescript(schema)
                except Exception as e:
                    # If there's an error, try executing statements individually
                    # This handles cases where views reference tables that don't exist yet
                    statements = schema.split(';')
                    for statement in statements:
                        statement = statement.strip()
                        if not statement or statement.startswith('--'):
                            continue
                        try:
                            self.conn.execute(statement)
                        except Exception as e2:
                            # If it's a view that references a missing table, that's OK
                            # (table might be added later via migration)
                            if 'no such table' in str(e2).lower() and 'view' in statement.lower():
                                logger.warning(f"Skipping view creation (table not found): {e2}")
                            elif 'already exists' in str(e2).lower():
                                # Table/view already exists, that's fine
                                pass
                            else:
                                # Re-raise if it's a real error
                                raise
                
                self.conn.commit()
                logger.debug("Database schema initialized")
            except Exception as e:
                logger.error(f"Failed to initialize schema: {e}")
                raise
        else:
            logger.warning(f"Schema file not found: {schema_file}")
        
        # Ensure pharmacogenomic tables exist (for backwards compatibility)
        self._ensure_pharmacogenomic_tables()
    
    def _ensure_pharmacogenomic_tables(self):
        """
        Ensure pharmacogenomic tables exist (for backwards compatibility with older databases).
        """
        try:
            # Check if pharmacogenomic_data table exists
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='pharmacogenomic_data'
            """)
            if not cursor.fetchone():
                logger.debug("Creating pharmacogenomic_data table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pharmacogenomic_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gene_id INTEGER NOT NULL,
                        metabolism_status TEXT NOT NULL,
                        genotype_phenotype TEXT,
                        citation_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (gene_id) REFERENCES genes(id),
                        FOREIGN KEY (citation_id) REFERENCES citations(id)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gene_pharmacogenomic_drugs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pharmacogenomic_data_id INTEGER NOT NULL,
                        drug_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pharmacogenomic_data_id) REFERENCES pharmacogenomic_data(id)
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharmacogenomic_data_gene_id ON pharmacogenomic_data(gene_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_gene_pharmacogenomic_drugs_pg_id ON gene_pharmacogenomic_drugs(pharmacogenomic_data_id)")
                self.conn.commit()
                logger.debug("Pharmacogenomic tables created")
        except Exception as e:
            logger.warning(f"Error ensuring pharmacogenomic tables: {e}")
            # Don't raise - this is for backwards compatibility
    
    def add_gene(self, gene_symbol: str, gene_name: str, chromosome: Optional[str] = None) -> int:
        """
        Add a gene to the database.
        
        Args:
            gene_symbol (str): Gene symbol (e.g., "COMT", "ADRA2A")
            gene_name (str): Full gene name (e.g., "Catechol-O-Methyltransferase")
            chromosome (str, optional): Chromosome location (e.g., "22")
        
        Returns:
            int: ID of the newly created gene record
        
        Raises:
            sqlite3.IntegrityError: If gene_symbol already exists (unique constraint)
        
        Example:
            >>> db = GeneticProfileDB()
            >>> gene_id = db.add_gene("COMT", "Catechol-O-Methyltransferase", "22")
            >>> print(f"Added gene with ID: {gene_id}")
            >>> db.close()
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO genes (gene_symbol, gene_name, chromosome)
                VALUES (?, ?, ?)
            """, (gene_symbol, gene_name, chromosome))
            self.conn.commit()
            gene_id = cursor.lastrowid
            logger.info(f"Added gene: {gene_symbol} (ID: {gene_id})")
            return gene_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to add gene {gene_symbol}: {e}")
            raise
    
    def add_snp(self, rs_number: str, gene_id: int, position: Optional[str] = None,
                 reference_allele: Optional[str] = None, alternate_allele: Optional[str] = None) -> int:
        """Add an SNP to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO snps (rs_number, gene_id, position, reference_allele, alternate_allele)
            VALUES (?, ?, ?, ?, ?)
        """, (rs_number, gene_id, position, reference_allele, alternate_allele))
        self.conn.commit()
        return cursor.lastrowid
    
    def ensure_snp(self, rs_number: str, gene_id: int) -> int:
        """The snps row for this rs number, created if missing; returns its id."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM snps WHERE rs_number = ?", (rs_number,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return self.add_snp(rs_number, gene_id)

    # --- consumer DNA raw data (see raw_dna.py) ---

    def add_dna_import(self, file_name: str, provider: Optional[str], build: Optional[str],
                       variant_count: int, no_call_count: int, matched_count: int,
                       primary_source_id: Optional[int] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dna_imports (file_name, provider, reference_build, variant_count,
                                     no_call_count, matched_count, primary_source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_name, provider, build, variant_count, no_call_count, matched_count,
              primary_source_id))
        self.conn.commit()
        return cursor.lastrowid

    def replace_snp_genotypes(self, import_id: int, rows) -> int:
        """
        Store (rsid, chromosome, position, genotype) rows for an import.
        An rs number already on file is replaced. Returns the number written.
        """
        cursor = self.conn.cursor()
        written = 0
        batch = []
        for rsid, chromosome, position, genotype in rows:
            batch.append((rsid, chromosome, position, genotype, import_id))
            if len(batch) >= 5000:
                cursor.executemany("INSERT OR REPLACE INTO snp_genotypes VALUES (?, ?, ?, ?, ?)", batch)
                written += len(batch)
                batch = []
        if batch:
            cursor.executemany("INSERT OR REPLACE INTO snp_genotypes VALUES (?, ?, ?, ?, ?)", batch)
            written += len(batch)
        self.conn.commit()
        return written

    def get_dna_imports(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dna_imports ORDER BY imported_at DESC, id DESC")
        return [dict(row) for row in cursor.fetchall()]

    def count_snp_genotypes(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM snp_genotypes")
        return cursor.fetchone()[0]

    def get_snp_genotypes(self, rsids: List[str]) -> Dict[str, str]:
        """{rsid: genotype} for the rs numbers on file among those asked for."""
        if not rsids:
            return {}
        cursor = self.conn.cursor()
        found = {}
        rsids = list(rsids)
        for start in range(0, len(rsids), 500):
            chunk = rsids[start:start + 500]
            cursor.execute(
                f"SELECT rsid, genotype FROM snp_genotypes WHERE rsid IN ({','.join('?' * len(chunk))})",
                chunk)
            found.update({row[0]: row[1] for row in cursor.fetchall()})
        return found

    def add_genotype(self, gene_id: int, genotype: str, phenotype: Optional[str] = None) -> int:
        """Add a genotype"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO genotypes (gene_id, genotype, phenotype)
            VALUES (?, ?, ?)
        """, (gene_id, genotype, phenotype))
        self.conn.commit()
        return cursor.lastrowid
    
    def check_citation_exists(self, pubmed_id: Optional[str] = None, 
                              doi: Optional[str] = None, 
                              citation_number: Optional[int] = None) -> Optional[Dict]:
        """
        Check if a citation already exists in the database.
        
        Args:
            pubmed_id: PubMed ID to check
            doi: DOI to check
            citation_number: Citation number to check
            
        Returns:
            Dictionary with citation data if found, None otherwise
        """
        cursor = self.conn.cursor()
        
        if pubmed_id:
            cursor.execute("SELECT * FROM citations WHERE pubmed_id = ?", (pubmed_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        if doi:
            cursor.execute("SELECT * FROM citations WHERE doi = ?", (doi,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        if citation_number:
            cursor.execute("SELECT * FROM citations WHERE citation_number = ?", (citation_number,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        return None
    
    def add_reference(self, citation_number: int, authors: Optional[str] = None,
                     year: Optional[int] = None, title: Optional[str] = None,
                     journal: Optional[str] = None, volume: Optional[str] = None,
                     pages: Optional[str] = None, doi: Optional[str] = None,
                     pubmed_id: Optional[str] = None, url: Optional[str] = None,
                     reference_type: str = "journal", pdf_file_path: Optional[str] = None) -> int:
        """Add a reference to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO citations (citation_number, authors, year, title, journal, 
                                  volume, pages, doi, pubmed_id, url, reference_type, pdf_file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (citation_number, authors, year, title, journal, volume, pages, 
              doi, pubmed_id, url, reference_type, pdf_file_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_reference_if_not_exists(self, citation_number: int, authors: Optional[str] = None,
                                   year: Optional[int] = None, title: Optional[str] = None,
                                   journal: Optional[str] = None, volume: Optional[str] = None,
                                   pages: Optional[str] = None, doi: Optional[str] = None,
                                   pubmed_id: Optional[str] = None, url: Optional[str] = None,
                                   reference_type: str = "journal", 
                                   pdf_file_path: Optional[str] = None) -> Optional[int]:
        """
        Add a reference only if it doesn't already exist (prevents duplicates).
        
        Returns:
            Citation ID if added, None if duplicate found
        """
        existing = self.check_citation_exists(pubmed_id=pubmed_id, doi=doi, 
                                             citation_number=citation_number)
        if existing:
            logger.debug(f"Citation already exists: {existing.get('id')}")
            return existing.get('id')
        
        try:
            return self.add_reference(citation_number, authors, year, title, journal,
                                     volume, pages, doi, pubmed_id, url, reference_type,
                                     pdf_file_path)
        except sqlite3.IntegrityError as e:
            # Handle unique constraint violations
            if 'UNIQUE constraint' in str(e):
                logger.warning(f"Duplicate citation detected: {e}")
                existing = self.check_citation_exists(pubmed_id=pubmed_id, doi=doi,
                                                     citation_number=citation_number)
                return existing.get('id') if existing else None
            raise
    
    def add_trait_association(self, gene_id: int, trait_name: str,
                            association_direction: Optional[str] = None,
                            notes: Optional[str] = None,
                            reference_ids: Optional[List[int]] = None) -> int:
        """Add a trait association"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trait_associations (gene_id, trait_name, association_direction, notes)
            VALUES (?, ?, ?, ?)
        """, (gene_id, trait_name, association_direction, notes))
        trait_id = cursor.lastrowid
        
        # Link references
        if reference_ids:
            for ref_id in reference_ids:
                cursor.execute("""
                    INSERT INTO gene_trait_citations (trait_association_id, citation_id)
                    VALUES (?, ?)
                """, (trait_id, ref_id))
        
        self.conn.commit()
        return trait_id
    
    def add_health_condition_association(self, gene_id: int, condition_name: str,
                                        association_type: Optional[str] = None,
                                        notes: Optional[str] = None,
                                        reference_ids: Optional[List[int]] = None) -> int:
        """Add a health condition association"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO health_condition_associations (gene_id, condition_name, association_type, notes)
            VALUES (?, ?, ?, ?)
        """, (gene_id, condition_name, association_type, notes))
        health_id = cursor.lastrowid
        
        # Link references
        if reference_ids:
            for ref_id in reference_ids:
                cursor.execute("""
                    INSERT INTO gene_health_citations (health_condition_association_id, citation_id)
                    VALUES (?, ?)
                """, (health_id, ref_id))
        
        self.conn.commit()
        return health_id
    
    def add_gene_gene_interaction(self, gene1_id: int, gene2_id: int,
                                 interaction_description: str) -> int:
        """Add a gene-gene interaction"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO gene_gene_interactions (gene1_id, gene2_id, interaction_description)
            VALUES (?, ?, ?)
        """, (gene1_id, gene2_id, interaction_description))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_research_finding(self, gene_id: int, finding_title: Optional[str],
                           finding_text: str,
                           reference_ids: Optional[List[int]] = None) -> int:
        """Add a research finding"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO research_findings (gene_id, finding_title, finding_text)
            VALUES (?, ?, ?)
        """, (gene_id, finding_title, finding_text))
        finding_id = cursor.lastrowid
        
        # Link references
        if reference_ids:
            for ref_id in reference_ids:
                cursor.execute("""
                    INSERT INTO research_finding_citations (research_finding_id, citation_id)
                    VALUES (?, ?)
                """, (finding_id, ref_id))
        
        self.conn.commit()
        return finding_id
    
    def add_database_source(self, gene_id: int, source_type: str, source_url: Optional[str] = None,
                          key_information: Optional[str] = None) -> int:
        """Add a database source"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO database_sources (gene_id, source_type, source_url, key_information)
            VALUES (?, ?, ?, ?)
        """, (gene_id, source_type, source_url, key_information))
        self.conn.commit()
        return cursor.lastrowid
    
    # Query methods
    def get_gene_by_symbol(self, gene_symbol: str) -> Optional[Dict]:
        """Get gene by symbol"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM genes WHERE gene_symbol = ?", (gene_symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_genes(self) -> List[Dict]:
        """
        Get all genes from the database.
        
        Returns:
            List[Dict]: List of all genes, each as a dictionary.
                Sorted alphabetically by gene_symbol.
        
        Example:
            >>> db = GeneticProfileDB()
            >>> genes = db.get_all_genes()
            >>> print(f"Total genes: {len(genes)}")
            >>> for gene in genes:
            ...     print(f"{gene['gene_symbol']}: {gene['gene_name']}")
            >>> db.close()
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM genes ORDER BY gene_symbol")
            genes = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Retrieved {len(genes)} genes")
            return genes
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all genes: {e}")
            raise
    
    def get_trait_associations_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all trait associations for a gene (deduplicated)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ta.id, ta.gene_id, ta.trait_name, ta.association_direction, ta.notes,
                   GROUP_CONCAT(DISTINCT c.citation_number) as citation_numbers
            FROM trait_associations ta
            LEFT JOIN gene_trait_citations gtc ON ta.id = gtc.trait_association_id
            LEFT JOIN citations c ON gtc.citation_id = c.id
            WHERE ta.gene_id = ?
            GROUP BY ta.id, ta.trait_name
            ORDER BY ta.trait_name
        """, (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_health_conditions_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all health conditions for a gene (deduplicated)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT hca.id, hca.gene_id, hca.condition_name, hca.association_type, hca.notes,
                   GROUP_CONCAT(DISTINCT c.citation_number) as citation_numbers
            FROM health_condition_associations hca
            LEFT JOIN gene_health_citations ghc ON hca.id = ghc.health_condition_association_id
            LEFT JOIN citations c ON ghc.citation_id = c.id
            WHERE hca.gene_id = ?
            GROUP BY hca.id, hca.condition_name
            ORDER BY hca.condition_name
        """, (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_references_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all references for a gene"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.*
            FROM citations c
            JOIN gene_trait_citations gtc ON c.id = gtc.citation_id
            JOIN trait_associations ta ON gtc.trait_association_id = ta.id
            WHERE ta.gene_id = ?
            UNION
            SELECT DISTINCT c.*
            FROM citations c
            JOIN gene_health_citations ghc ON c.id = ghc.citation_id
            JOIN health_condition_associations hca ON ghc.health_condition_association_id = hca.id
            WHERE hca.gene_id = ?
            UNION
            SELECT DISTINCT c.*
            FROM citations c
            JOIN research_finding_citations rfc ON c.id = rfc.citation_id
            JOIN research_findings rf ON rfc.research_finding_id = rf.id
            WHERE rf.gene_id = ?
            ORDER BY c.citation_number
        """, (gene_id, gene_id, gene_id))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_references(self) -> List[Dict]:
        """Get all references sorted by citation number"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM citations ORDER BY citation_number")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_snps_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all SNPs for a gene"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM snps WHERE gene_id = ? ORDER BY rs_number", (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_variant_genotypes_for_gene(self, gene_symbol: str) -> List[Dict]:
        """
        The well-known variants in a gene that a DNA import actually called,
        with the person's genotype at each.

        Pairs `variant_reference` (public knowledge: which rs numbers sit in
        this gene and what each is called) with `snp_genotypes` (this
        person's file). Variants the file did not call are left out rather
        than listed as blanks, so an empty list means "nothing on file for
        this gene", which is also what a ledger with no DNA import returns.

        Each row: {'rsid', 'genotype', 'description'}.
        """
        known = variant_reference.variants_for_gene(gene_symbol)
        if not known:
            return []
        called = self.get_snp_genotypes([rsid for rsid, _ in known])
        return [{'rsid': rsid, 'genotype': called[rsid], 'description': description}
                for rsid, description in known if rsid in called]

    def get_genotypes_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all genotypes for a gene"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM genotypes WHERE gene_id = ?", (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_database_sources_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all database sources for a gene"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM database_sources WHERE gene_id = ? ORDER BY source_type", (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_research_findings_for_gene(self, gene_id: int) -> List[Dict]:
        """Get all research findings for a gene with citations"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rf.*, GROUP_CONCAT(c.citation_number) as citation_numbers
            FROM research_findings rf
            LEFT JOIN research_finding_citations rfc ON rf.id = rfc.research_finding_id
            LEFT JOIN citations c ON rfc.citation_id = c.id
            WHERE rf.gene_id = ?
            GROUP BY rf.id
            ORDER BY rf.finding_title, rf.id
        """, (gene_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_traits(self, search_term: str) -> List[Dict]:
        """Search trait associations"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ta.*, g.gene_symbol, g.gene_name
            FROM trait_associations ta
            JOIN genes g ON ta.gene_id = g.id
            WHERE ta.trait_name LIKE ?
            ORDER BY g.gene_symbol, ta.trait_name
        """, (f"%{search_term}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_health_conditions(self, search_term: str) -> List[Dict]:
        """Search health condition associations"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hca.*, g.gene_symbol, g.gene_name
            FROM health_condition_associations hca
            JOIN genes g ON hca.gene_id = g.id
            WHERE hca.condition_name LIKE ?
            ORDER BY g.gene_symbol, hca.condition_name
        """, (f"%{search_term}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_genes_by_trait(self, trait_name: str) -> List[Dict]:
        """Get all genes associated with a specific trait"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.*, ta.trait_name, ta.association_direction
            FROM genes g
            JOIN trait_associations ta ON g.id = ta.gene_id
            WHERE ta.trait_name LIKE ?
            ORDER BY g.gene_symbol
        """, (f"%{trait_name}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_genes_by_condition(self, condition_name: str) -> List[Dict]:
        """Get all genes associated with a specific health condition"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.*, hca.condition_name, hca.association_type
            FROM genes g
            JOIN health_condition_associations hca ON g.id = hca.gene_id
            WHERE hca.condition_name LIKE ?
            ORDER BY g.gene_symbol
        """, (f"%{condition_name}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_interacting_genes(self, gene_symbol: str) -> List[Dict]:
        """Get all genes that interact with a given gene"""
        cursor = self.conn.cursor()
        gene = self.get_gene_by_symbol(gene_symbol)
        if not gene:
            return []
        
        gene_id = gene['id']
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN ggi.gene1_id = ? THEN g2.gene_symbol
                    ELSE g1.gene_symbol
                END as interacting_gene_symbol,
                CASE 
                    WHEN ggi.gene1_id = ? THEN g2.gene_name
                    ELSE g1.gene_name
                END as interacting_gene_name,
                ggi.interaction_description
            FROM gene_gene_interactions ggi
            JOIN genes g1 ON ggi.gene1_id = g1.id
            JOIN genes g2 ON ggi.gene2_id = g2.id
            WHERE ggi.gene1_id = ? OR ggi.gene2_id = ?
            ORDER BY interacting_gene_symbol
        """, (gene_id, gene_id, gene_id, gene_id))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_gene_summary(self, gene_symbol: str) -> Optional[Dict]:
        """Get comprehensive summary for a gene"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM v_gene_summary WHERE gene_symbol = ?
        """, (gene_symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_gene_summaries(self) -> List[Dict]:
        """Get summaries for all genes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM v_gene_summary ORDER BY gene_symbol")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_genes_with_trait(self, trait_keyword: str) -> List[Dict]:
        """Get all genes that have a trait matching the keyword"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT 
                g.id,
                g.gene_symbol,
                g.gene_name,
                GROUP_CONCAT(DISTINCT ta.trait_name) as matching_traits
            FROM genes g
            JOIN trait_associations ta ON g.id = ta.gene_id
            WHERE ta.trait_name LIKE ?
            GROUP BY g.id
            ORDER BY g.gene_symbol
        """, (f"%{trait_keyword}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_genes_with_condition(self, condition_keyword: str) -> List[Dict]:
        """Get all genes that have a health condition matching the keyword"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT 
                g.id,
                g.gene_symbol,
                g.gene_name,
                GROUP_CONCAT(DISTINCT hca.condition_name) as matching_conditions
            FROM genes g
            JOIN health_condition_associations hca ON g.id = hca.gene_id
            WHERE hca.condition_name LIKE ?
            GROUP BY g.id
            ORDER BY g.gene_symbol
        """, (f"%{condition_keyword}%",))
        return [dict(row) for row in cursor.fetchall()]
    
    def check_research_reference_exists(self, pubmed_id: Optional[str] = None,
                                        doi: Optional[str] = None,
                                        reference_number: Optional[int] = None) -> Optional[Dict]:
        """
        Check if a research reference already exists in the database.
        
        Args:
            pubmed_id: PubMed ID to check
            doi: DOI to check
            reference_number: Reference number to check
            
        Returns:
            Dictionary with reference data if found, None otherwise
        """
        cursor = self.conn.cursor()
        
        if pubmed_id:
            cursor.execute("SELECT * FROM research_references WHERE pubmed_id = ?", (pubmed_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        if doi:
            cursor.execute("SELECT * FROM research_references WHERE doi = ?", (doi,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        if reference_number:
            cursor.execute("SELECT * FROM research_references WHERE reference_number = ?", (reference_number,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        
        return None
    
    def add_research_reference(self, reference_number: int, authors: Optional[str] = None,
                              year: Optional[int] = None, title: Optional[str] = None,
                              journal: Optional[str] = None, volume: Optional[str] = None,
                              pages: Optional[str] = None, doi: Optional[str] = None,
                              pubmed_id: Optional[str] = None, url: Optional[str] = None,
                              reference_type: str = "journal", abstract: Optional[str] = None,
                              keywords: Optional[str] = None, pdf_file_path: Optional[str] = None) -> int:
        """Add a research reference to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO research_references (reference_number, authors, year, title, journal, 
                                  volume, pages, doi, pubmed_id, url, reference_type, abstract, keywords, pdf_file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reference_number, authors, year, title, journal, volume, pages, 
              doi, pubmed_id, url, reference_type, abstract, keywords, pdf_file_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_research_reference_if_not_exists(self, reference_number: int, authors: Optional[str] = None,
                                            year: Optional[int] = None, title: Optional[str] = None,
                                            journal: Optional[str] = None, volume: Optional[str] = None,
                                            pages: Optional[str] = None, doi: Optional[str] = None,
                                            pubmed_id: Optional[str] = None, url: Optional[str] = None,
                                            reference_type: str = "journal", abstract: Optional[str] = None,
                                            keywords: Optional[str] = None,
                                            pdf_file_path: Optional[str] = None) -> Optional[int]:
        """
        Add a research reference only if it doesn't already exist (prevents duplicates).
        
        Returns:
            Reference ID if added, None if duplicate found
        """
        existing = self.check_research_reference_exists(pubmed_id=pubmed_id, doi=doi,
                                                       reference_number=reference_number)
        if existing:
            logger.debug(f"Research reference already exists: {existing.get('id')}")
            return existing.get('id')
        
        try:
            return self.add_research_reference(reference_number, authors, year, title, journal,
                                              volume, pages, doi, pubmed_id, url, reference_type,
                                              abstract, keywords, pdf_file_path)
        except sqlite3.IntegrityError as e:
            # Handle unique constraint violations
            if 'UNIQUE constraint' in str(e):
                logger.warning(f"Duplicate research reference detected: {e}")
                existing = self.check_research_reference_exists(pubmed_id=pubmed_id, doi=doi,
                                                               reference_number=reference_number)
                return existing.get('id') if existing else None
            raise
    
    def add_primary_source(self, source_name: str, source_type: str,
                          institution: Optional[str] = None, patient_name: Optional[str] = None,
                          document_date: Optional[str] = None, file_path: Optional[str] = None,
                          file_name: Optional[str] = None, extracted_text: Optional[str] = None,
                          metadata: Optional[str] = None, citation_id: Optional[int] = None) -> int:
        """Add a primary source to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO primary_sources (source_name, source_type, institution, patient_name,
                                       document_date, file_path, file_name, extracted_text,
                                       metadata, citation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_name, source_type, institution, patient_name, document_date,
              file_path, file_name, extracted_text, metadata, citation_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_primary_source_finding(self, primary_source_id: int, finding_text: str,
                                  finding_type: Optional[str] = None,
                                  finding_date: Optional[str] = None,
                                  related_gene_id: Optional[int] = None,
                                  related_condition: Optional[str] = None,
                                  notes: Optional[str] = None) -> int:
        """Add a finding from a primary source"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO primary_source_findings (primary_source_id, finding_type, finding_text,
                                                finding_date, related_gene_id, related_condition, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (primary_source_id, finding_type, finding_text, finding_date,
              related_gene_id, related_condition, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_primary_source_finding_if_not_exists(self, primary_source_id: int, finding_text: str,
                                                finding_type: Optional[str] = None,
                                                finding_date: Optional[str] = None,
                                                related_gene_id: Optional[int] = None,
                                                related_condition: Optional[str] = None,
                                                notes: Optional[str] = None) -> Optional[int]:
        """
        Add a finding unless an identical one (same source, type, text and date)
        already exists. Lets extraction scripts be re-run without duplicating rows.

        Returns:
            int: ID of the new finding, or None if it already existed
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM primary_source_findings
            WHERE primary_source_id = ?
              AND finding_text = ?
              AND finding_type IS ?
              AND finding_date IS ?
            LIMIT 1
        """, (primary_source_id, finding_text, finding_type, finding_date))
        if cursor.fetchone():
            return None
        return self.add_primary_source_finding(primary_source_id, finding_text, finding_type,
                                               finding_date, related_gene_id, related_condition, notes)
    
    def get_all_primary_sources(self) -> List[Dict]:
        """Get all primary sources"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM primary_sources ORDER BY document_date DESC, source_name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_primary_sources_by_type(self, source_type: str) -> List[Dict]:
        """Get all primary sources of a specific type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM primary_sources 
            WHERE source_type = ?
            ORDER BY document_date DESC, source_name
        """, (source_type,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_primary_sources_by_date_range(self, start_date: Optional[str] = None,
                                          end_date: Optional[str] = None) -> List[Dict]:
        """Get primary sources within a date range"""
        cursor = self.conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM primary_sources 
                WHERE document_date >= ? AND document_date <= ?
                ORDER BY document_date DESC, source_name
            """, (start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM primary_sources 
                WHERE document_date >= ?
                ORDER BY document_date DESC, source_name
            """, (start_date,))
        elif end_date:
            cursor.execute("""
                SELECT * FROM primary_sources 
                WHERE document_date <= ?
                ORDER BY document_date DESC, source_name
            """, (end_date,))
        else:
            return self.get_all_primary_sources()
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_primary_sources(self, query: str) -> List[Dict]:
        """Search primary sources by text in source name, extracted text, or findings"""
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        
        cursor.execute("""
            SELECT DISTINCT ps.*
            FROM primary_sources ps
            LEFT JOIN primary_source_findings psf ON ps.id = psf.primary_source_id
            WHERE ps.source_name LIKE ?
               OR ps.extracted_text LIKE ?
               OR ps.institution LIKE ?
               OR psf.finding_text LIKE ?
            ORDER BY ps.document_date DESC, ps.source_name
        """, (search_pattern, search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_primary_source_with_findings(self, source_id: int) -> Optional[Dict]:
        """Get a primary source with all its findings"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM primary_sources WHERE id = ?", (source_id,))
        source = cursor.fetchone()
        
        if not source:
            return None
        
        source_dict = dict(source)
        source_dict['findings'] = self.get_primary_source_findings(source_id)
        return source_dict
    
    def get_primary_source_text(self, source_id: int) -> Optional[str]:
        """Get the extracted text for a primary source"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT extracted_text FROM primary_sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        return row['extracted_text'] if row else None
    
    # The person's details, printed at the top of every document they share
    # with a doctor. Stored in app_settings under patient.<field>.
    PATIENT_DETAIL_FIELDS = (
        'full_name', 'date_of_birth', 'address', 'phone',
        'insurance_provider', 'insurance_member_id', 'insurance_group_number',
    )
    PATIENT_DETAIL_MAX_LENGTH = 500

    def get_patient_details(self) -> Dict[str, str]:
        """The saved patient details, one entry per filled field."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'patient.%'")
        except sqlite3.OperationalError:
            return {}
        details = {}
        for key, value in cursor.fetchall():
            field = key[len('patient.'):]
            if field in self.PATIENT_DETAIL_FIELDS and value:
                details[field] = value
        return details

    def save_patient_details(self, details: Dict[str, str]) -> Dict[str, str]:
        """
        Replace the saved patient details with these.

        Unknown fields are ignored, values are trimmed and capped, and a
        blank value clears the field. Returns what is now saved.
        """
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)')
        for field in self.PATIENT_DETAIL_FIELDS:
            value = (details.get(field) or '').strip()[:self.PATIENT_DETAIL_MAX_LENGTH]
            key = f'patient.{field}'
            if value:
                cursor.execute('INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
                               (key, value))
            else:
                cursor.execute('DELETE FROM app_settings WHERE key = ?', (key,))
        self.conn.commit()
        return self.get_patient_details()

    def get_patient_name(self) -> Optional[str]:
        """
        Get the patient name from primary sources.
        Returns the most common patient name, or the most recent one if multiple exist.
        
        Returns:
            Optional[str]: Patient name in LastFirst format, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT patient_name, COUNT(*) as count
            FROM primary_sources
            WHERE patient_name IS NOT NULL AND patient_name != ''
            GROUP BY patient_name
            ORDER BY count DESC, MAX(document_date) DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return None
    
    def get_genetic_test_info(self) -> Optional[Dict]:
        """
        Get genetic test information (date, provider, file path) from primary sources.
        Looks for test_report type sources, prioritizing GeneSight or genetic testing reports.
        
        Returns:
            Optional[Dict]: Dictionary with 'date', 'provider', 'file_path', 'source_name', or None if not found
        """
        cursor = self.conn.cursor()
        # Look for test_report sources, prioritizing those with "genetic" or "genesight" in name/institution
        cursor.execute("""
            SELECT document_date, institution, file_path, source_name, file_name
            FROM primary_sources
            WHERE source_type = 'test_report'
            AND (institution LIKE '%GeneSight%' 
                 OR institution LIKE '%genetic%' 
                 OR source_name LIKE '%genetic%'
                 OR source_name LIKE '%GeneSight%'
                 OR file_name LIKE '%genetic%'
                 OR file_name LIKE '%GeneSight%')
            ORDER BY document_date DESC, id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                'date': row[0],
                'provider': row[1] or 'Unknown',
                'file_path': row[2],
                'source_name': row[3],
                'file_name': row[4]
            }
        
        # Fallback: any test_report
        cursor.execute("""
            SELECT document_date, institution, file_path, source_name, file_name
            FROM primary_sources
            WHERE source_type = 'test_report'
            ORDER BY document_date DESC, id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                'date': row[0],
                'provider': row[1] or 'Unknown',
                'file_path': row[2],
                'source_name': row[3],
                'file_name': row[4]
            }
        return None
    
    def get_current_medications(self) -> List[Dict]:
        """
        Get current medications from primary source findings.
        Returns the most recent medication entries.
        
        Returns:
            List[Dict]: List of medication dictionaries with 'medication_name', 'start_date', 'details'
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT finding_text, finding_date, notes, MAX(ps.document_date) as source_date
            FROM primary_source_findings psf
            JOIN primary_sources ps ON psf.primary_source_id = ps.id
            WHERE psf.finding_type = 'medication'
            GROUP BY psf.finding_text
            ORDER BY source_date DESC, psf.finding_date DESC
        """)
        medications = []
        for row in cursor.fetchall():
            medications.append({
                'medication_name': row[0],
                'start_date': row[1],
                'details': row[2],
                'source_date': row[3]
            })
        return medications
    
    def get_primary_source_findings(self, primary_source_id: int) -> List[Dict]:
        """Get all findings for a primary source"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT psf.*, g.gene_symbol, g.gene_name
            FROM primary_source_findings psf
            LEFT JOIN genes g ON psf.related_gene_id = g.id
            WHERE psf.primary_source_id = ?
            ORDER BY psf.finding_date DESC, psf.id
        """, (primary_source_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_research_references(self) -> List[Dict]:
        """Get all research references sorted by reference number"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM research_references ORDER BY reference_number")
        return [dict(row) for row in cursor.fetchall()]
    
    def add_health_metric(self, primary_source_id: int, metric_type: str,
                         collection_date: str, metric_value: Optional[float] = None,
                         metric_value_text: Optional[str] = None,
                         metric_name: Optional[str] = None,
                         unit: Optional[str] = None,
                         collection_time: Optional[str] = None,
                         visit_type: Optional[str] = None,
                         is_abnormal: bool = False,
                         normal_range_min: Optional[float] = None,
                         normal_range_max: Optional[float] = None,
                         finding_id: Optional[int] = None,
                         notes: Optional[str] = None) -> int:
        """Add a health metric (vital sign, lab value, etc.) to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO health_metrics (primary_source_id, finding_id, metric_type, metric_name,
                                      metric_value, metric_value_text, unit, collection_date,
                                      collection_time, visit_type, is_abnormal, normal_range_min,
                                      normal_range_max, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (primary_source_id, finding_id, metric_type, metric_name, metric_value,
              metric_value_text, unit, collection_date, collection_time, visit_type,
              is_abnormal, normal_range_min, normal_range_max, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def delete_health_metrics_for_source(self, primary_source_id: int) -> int:
        """
        Delete every health metric extracted from a primary source.

        The extraction scripts call this before re-extracting so a re-run
        replaces the derived rows instead of appending duplicates.

        Returns:
            int: Number of rows deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM health_metrics WHERE primary_source_id = ?", (primary_source_id,))
        self.conn.commit()
        logger.info(f"Deleted {cursor.rowcount} health metrics for source {primary_source_id}")
        return cursor.rowcount
    
    def get_health_metrics(self, metric_type: Optional[str] = None,
                          visit_type: Optional[str] = None,
                          routine_only: bool = False,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        """Get health metrics with optional filtering"""
        cursor = self.conn.cursor()
        
        if routine_only:
            # Use view that filters out sick visits
            query = "SELECT * FROM v_health_metrics_routine_only WHERE 1=1"
            params = []
        else:
            query = "SELECT * FROM health_metrics WHERE 1=1"
            params = []
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)
        
        if visit_type and not routine_only:
            query += " AND visit_type = ?"
            params.append(visit_type)
        
        if start_date:
            query += " AND collection_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND collection_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY collection_date DESC, collection_time DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_health_metrics_stats(self, metric_type: Optional[str] = None) -> List[Dict]:
        """Get statistics for health metrics (routine visits only)"""
        cursor = self.conn.cursor()
        
        if metric_type:
            cursor.execute("""
                SELECT * FROM v_health_metrics_stats
                WHERE metric_type = ?
            """, (metric_type,))
        else:
            cursor.execute("SELECT * FROM v_health_metrics_stats")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_health_metrics_category_averages(self) -> List[Dict]:
        """
        Get averages per vital sign (routine visits only).

        Grouped by metric_type AND unit: averaging 36.8 °C with 98.6 °F gave
        a meaningless "temperature 58". Lab values are excluded because each
        analyte is its own measurement; use get_health_metrics_stats for those.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                metric_type,
                unit,
                COUNT(*) as total_measurements,
                COUNT(DISTINCT metric_name) as unique_metrics,
                AVG(metric_value) as category_average,
                MIN(metric_value) as category_min,
                MAX(metric_value) as category_max,
                AVG(CASE WHEN is_abnormal = 1 THEN 1.0 ELSE 0.0 END) * 100 as abnormal_percentage,
                MIN(normal_range_min) as normal_range_min,
                MAX(normal_range_max) as normal_range_max,
                COUNT(DISTINCT CASE WHEN normal_range_min IS NOT NULL AND normal_range_max IS NOT NULL THEN metric_name END) as metrics_with_ranges
            FROM v_health_metrics_routine_only
            WHERE metric_value IS NOT NULL
              AND metric_type != 'lab_value'
            GROUP BY metric_type, unit
            ORDER BY metric_type, unit
        """)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Determine if category average is within normal range
        for result in results:
            avg = result.get('category_average')
            normal_min = result.get('normal_range_min')
            normal_max = result.get('normal_range_max')
            
            # Check if average is within normal range
            if avg is not None and normal_min is not None and normal_max is not None:
                result['average_in_normal_range'] = normal_min <= avg <= normal_max
            else:
                result['average_in_normal_range'] = None
        
        return results
    
    def add_pharmacogenomic_data(self, gene_id: int, metabolism_status: str,
                                 genotype_phenotype: Optional[str] = None,
                                 citation_id: Optional[int] = None) -> int:
        """
        Add pharmacogenomic data for a gene.
        
        Args:
            gene_id (int): The ID of the gene
            metabolism_status (str): Metabolism status (e.g., "Normal", "Rapid", "Intermediate", "Poor")
            genotype_phenotype (Optional[str]): Genotype/phenotype information
            citation_id (Optional[int]): Reference to citation
        
        Returns:
            int: The ID of the newly added pharmacogenomic data record
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO pharmacogenomic_data (gene_id, metabolism_status, genotype_phenotype, citation_id)
            VALUES (?, ?, ?, ?)
        """, (gene_id, metabolism_status, genotype_phenotype, citation_id))
        self.conn.commit()
        logger.info(f"Added pharmacogenomic data for gene_id {gene_id}: {metabolism_status}")
        return cursor.lastrowid
    
    def add_gene_pharmacogenomic_drug(self, pharmacogenomic_data_id: int, drug_name: str) -> int:
        """
        Add a drug associated with pharmacogenomic data.
        
        Args:
            pharmacogenomic_data_id (int): The ID of the pharmacogenomic data record
            drug_name (str): Name of the affected medication
        
        Returns:
            int: The ID of the newly added drug record
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO gene_pharmacogenomic_drugs (pharmacogenomic_data_id, drug_name)
            VALUES (?, ?)
        """, (pharmacogenomic_data_id, drug_name))
        self.conn.commit()
        logger.info(f"Added drug {drug_name} to pharmacogenomic_data_id {pharmacogenomic_data_id}")
        return cursor.lastrowid
    
    def replace_pharmacogenomic_data_for_gene(self, gene_id: int, metabolism_status: str,
                                              genotype_phenotype: Optional[str] = None,
                                              drugs: Optional[List[str]] = None) -> int:
        """
        Set a gene's pharmacogenomic record, replacing whatever it had.

        Idempotent: running an import twice leaves one record per gene.
        Returns the new record's id.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM gene_pharmacogenomic_drugs
            WHERE pharmacogenomic_data_id IN (SELECT id FROM pharmacogenomic_data WHERE gene_id = ?)
        """, (gene_id,))
        cursor.execute("DELETE FROM pharmacogenomic_data WHERE gene_id = ?", (gene_id,))
        cursor.execute("""
            INSERT INTO pharmacogenomic_data (gene_id, metabolism_status, genotype_phenotype)
            VALUES (?, ?, ?)
        """, (gene_id, metabolism_status, genotype_phenotype))
        record_id = cursor.lastrowid
        for drug in drugs or []:
            cursor.execute("""
                INSERT INTO gene_pharmacogenomic_drugs (pharmacogenomic_data_id, drug_name)
                VALUES (?, ?)
            """, (record_id, drug))
        self.conn.commit()
        return record_id

    def replace_medication_interactions_for_source(self, primary_source_id: int,
                                                   interactions: List[Dict]) -> int:
        """
        Store a report's medication categories, replacing the source's earlier rows.

        Each interaction: {'drug_name', 'category', 'brand_name'?, 'notes'?}.
        Returns the number of rows written.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM medication_interactions WHERE primary_source_id = ?",
                       (primary_source_id,))
        for item in interactions:
            cursor.execute("""
                INSERT INTO medication_interactions
                    (primary_source_id, drug_name, brand_name, category, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (primary_source_id, item['drug_name'], item.get('brand_name'),
                  item['category'], item.get('notes')))
        self.conn.commit()
        return len(interactions)

    def get_medication_interactions(self, primary_source_id: Optional[int] = None) -> List[Dict]:
        """
        The report's medication guidance, most significant category first,
        then by drug name. Empty when nothing has been imported.
        """
        cursor = self.conn.cursor()
        sql = """
            SELECT mi.id, mi.primary_source_id, mi.drug_name, mi.brand_name, mi.category, mi.notes,
                   ps.source_name, ps.document_date
            FROM medication_interactions mi
            LEFT JOIN primary_sources ps ON ps.id = mi.primary_source_id
        """
        params: tuple = ()
        if primary_source_id is not None:
            sql += " WHERE mi.primary_source_id = ?"
            params = (primary_source_id,)
        sql += """
            ORDER BY CASE mi.category
                         WHEN 'significant' THEN 0
                         WHEN 'moderate' THEN 1
                         ELSE 2
                     END, mi.drug_name
        """
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_pharmacogenomic_data_for_gene(self, gene_id: int) -> Optional[Dict]:
        """
        Get pharmacogenomic data for a specific gene.
        
        Args:
            gene_id (int): The ID of the gene
        
        Returns:
            Optional[Dict]: Pharmacogenomic data with associated drugs, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                pd.id,
                pd.gene_id,
                pd.metabolism_status,
                pd.genotype_phenotype,
                pd.citation_id,
                GROUP_CONCAT(gpd.drug_name) as affected_medications
            FROM pharmacogenomic_data pd
            LEFT JOIN gene_pharmacogenomic_drugs gpd ON pd.id = gpd.pharmacogenomic_data_id
            WHERE pd.gene_id = ?
            GROUP BY pd.id
        """, (gene_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('affected_medications'):
                result['affected_medications'] = result['affected_medications'].split(',')
            else:
                result['affected_medications'] = []
            return result
        return None
    
    def get_all_pharmacogenomic(self) -> List[Dict]:
        """
        Get all pharmacogenomic data with associated genes and drugs.
        
        Returns:
            List[Dict]: List of all pharmacogenomic records with gene and drug information
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                g.id as gene_id,
                g.gene_symbol,
                g.gene_name,
                pd.id as pharmacogenomic_id,
                pd.metabolism_status,
                pd.genotype_phenotype,
                pd.citation_id,
                GROUP_CONCAT(gpd.drug_name) as affected_medications
            FROM genes g
            JOIN pharmacogenomic_data pd ON g.id = pd.gene_id
            LEFT JOIN gene_pharmacogenomic_drugs gpd ON pd.id = gpd.pharmacogenomic_data_id
            GROUP BY g.id, pd.id
            ORDER BY g.gene_symbol
        """)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('affected_medications'):
                result['affected_medications'] = result['affected_medications'].split(',')
            else:
                result['affected_medications'] = []
            results.append(result)
        return results
    
    def get_medications_for_gene(self, gene_id: int) -> List[str]:
        """
        Get all medications affected by a gene's pharmacogenomic profile.
        
        Args:
            gene_id (int): The ID of the gene
        
        Returns:
            List[str]: List of medication names
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT gpd.drug_name
            FROM gene_pharmacogenomic_drugs gpd
            JOIN pharmacogenomic_data pd ON gpd.pharmacogenomic_data_id = pd.id
            WHERE pd.gene_id = ?
            ORDER BY gpd.drug_name
        """, (gene_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def search_pharmacogenomic(self, medication_name: str) -> List[Dict]:
        """
        Search for pharmacogenomic data by medication name.
        
        Args:
            medication_name (str): Name of medication to search for
        
        Returns:
            List[Dict]: List of pharmacogenomic records for genes affecting this medication
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                g.id as gene_id,
                g.gene_symbol,
                g.gene_name,
                pd.metabolism_status,
                pd.genotype_phenotype,
                gpd.drug_name
            FROM genes g
            JOIN pharmacogenomic_data pd ON g.id = pd.gene_id
            JOIN gene_pharmacogenomic_drugs gpd ON pd.id = gpd.pharmacogenomic_data_id
            WHERE gpd.drug_name LIKE ?
            ORDER BY g.gene_symbol
        """, (f'%{medication_name}%',))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Example usage
    db = GeneticProfileDB()
    
    # Add a gene
    gene_id = db.add_gene("ADRA2A", "Adrenergic Alpha-2A Receptor", "10")
    print(f"Added gene ADRA2A with ID: {gene_id}")
    
    # Add an SNP
    snp_id = db.add_snp("rs1800544", gene_id)
    print(f"Added SNP rs1800544 with ID: {snp_id}")
    
    # Add a genotype
    genotype_id = db.add_genotype(gene_id, "C/G", "Heterozygous")
    print(f"Added genotype C/G with ID: {genotype_id}")
    
    # Add a reference
    ref_id = db.add_reference(
        citation_number=1,
        authors="GeneSight",
        year=2024,
        title="Get to know a gene: ADRA2A",
        url="https://genesight.com/white-papers/get-to-know-a-gene-adra2a/",
        reference_type="website"
    )
    print(f"Added reference with ID: {ref_id}")
    
    # Add a trait association
    trait_id = db.add_trait_association(
        gene_id=gene_id,
        trait_name="ADHD susceptibility",
        association_direction="increased",
        reference_ids=[ref_id]
    )
    print(f"Added trait association with ID: {trait_id}")
    
    # Query examples
    genes = db.get_all_genes()
    print(f"\nTotal genes in database: {len(genes)}")
    
    traits = db.get_trait_associations_for_gene(gene_id)
    print(f"\nTrait associations for ADRA2A: {len(traits)}")
    
    db.close()

