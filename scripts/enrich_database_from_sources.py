#!/usr/bin/env python3
"""
Unified Interface for Enriching Database from Reputable Sources
Pulls information from PubMed, GTR, SNPedia, and GWAS Catalog
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('enrich_database')


def enrich_gene_from_all_sources(gene_symbol: str, db: GeneticProfileDB, 
                                 sources: Dict[str, bool] = None) -> Dict:
    """
    Enrich database for a gene from all reputable sources.
    
    Args:
        gene_symbol: Gene symbol
        db: Database connection
        sources: Dictionary indicating which sources to use
                 {'pubmed': True, 'gtr': True, 'snpedia': True, 'gwas': True}
    
    Returns:
        Dictionary with enrichment statistics
    """
    if sources is None:
        sources = {'pubmed': True, 'gtr': True, 'snpedia': True, 'gwas': True}
    
    stats = {
        'gene': gene_symbol,
        'pubmed': {'processed': 0, 'added': 0, 'skipped': 0},
        'gtr': {'processed': 0, 'added': 0, 'skipped': 0},
        'snpedia': {'processed': 0, 'added': 0, 'skipped': 0},
        'gwas': {'processed': 0, 'added': 0, 'skipped': 0}
    }
    
    # PubMed
    if sources.get('pubmed', False):
        try:
            from scripts.fetch_from_pubmed import process_gene_pubmed_data
            stats['pubmed'] = process_gene_pubmed_data(gene_symbol, db)
            logger.info(f"PubMed enrichment for {gene_symbol}: {stats['pubmed']}")
        except Exception as e:
            logger.error(f"Error enriching from PubMed for {gene_symbol}: {e}", exc_info=True)
    
    # GTR
    if sources.get('gtr', False):
        try:
            from scripts.fetch_from_gtr import process_gene_gtr_data
            stats['gtr'] = process_gene_gtr_data(gene_symbol, db)
            logger.info(f"GTR enrichment for {gene_symbol}: {stats['gtr']}")
        except Exception as e:
            logger.error(f"Error enriching from GTR for {gene_symbol}: {e}", exc_info=True)
    
    # SNPedia (for SNPs associated with the gene)
    if sources.get('snpedia', False):
        try:
            from scripts.fetch_from_snpedia import process_snp_snpedia_data
            cursor = db.conn.cursor()
            cursor.execute("SELECT rs_number FROM snps WHERE gene_id = (SELECT id FROM genes WHERE gene_symbol = ?)", 
                          (gene_symbol,))
            snps = [row[0] for row in cursor.fetchall()]
            
            for rs_number in snps:
                snp_stats = process_snp_snpedia_data(rs_number, db)
                stats['snpedia']['processed'] += snp_stats['processed']
                stats['snpedia']['added'] += snp_stats['added']
                stats['snpedia']['skipped'] += snp_stats['skipped']
            
            logger.info(f"SNPedia enrichment for {gene_symbol}: {stats['snpedia']}")
        except Exception as e:
            logger.error(f"Error enriching from SNPedia for {gene_symbol}: {e}", exc_info=True)
    
    # GWAS Catalog
    if sources.get('gwas', False):
        try:
            from scripts.fetch_from_gwas import process_gene_gwas_data
            stats['gwas'] = process_gene_gwas_data(gene_symbol, db)
            logger.info(f"GWAS enrichment for {gene_symbol}: {stats['gwas']}")
        except Exception as e:
            logger.error(f"Error enriching from GWAS for {gene_symbol}: {e}", exc_info=True)
    
    return stats


def enrich_all_genes(db: GeneticProfileDB, sources: Dict[str, bool] = None,
                     incremental: bool = True) -> Dict:
    """
    Enrich database for all genes from all sources.
    
    Args:
        db: Database connection
        sources: Dictionary indicating which sources to use
        incremental: If True, only fetch new information since last update
        
    Returns:
        Dictionary with total enrichment statistics
    """
    genes = db.get_all_genes()
    
    logger.info(f"Enriching {len(genes)} genes from reputable sources...")
    
    total_stats = {
        'total_genes': len(genes),
        'pubmed': {'processed': 0, 'added': 0, 'skipped': 0},
        'gtr': {'processed': 0, 'added': 0, 'skipped': 0},
        'snpedia': {'processed': 0, 'added': 0, 'skipped': 0},
        'gwas': {'processed': 0, 'added': 0, 'skipped': 0}
    }
    
    for i, gene in enumerate(genes, 1):
        gene_symbol = gene['gene_symbol']
        logger.info(f"Processing gene {i}/{len(genes)}: {gene_symbol}")
        
        stats = enrich_gene_from_all_sources(gene_symbol, db, sources)
        
        # Aggregate statistics
        for source in ['pubmed', 'gtr', 'snpedia', 'gwas']:
            for key in ['processed', 'added', 'skipped']:
                total_stats[source][key] += stats[source].get(key, 0)
    
    return total_stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich database from reputable sources')
    parser.add_argument('--gene', type=str, help='Enrich specific gene')
    parser.add_argument('--all', action='store_true', help='Enrich all genes')
    parser.add_argument('--source', choices=['pubmed', 'gtr', 'snpedia', 'gwas', 'all'],
                       default='all', help='Source to use (default: all)')
    parser.add_argument('--email', type=str, default='user@example.com',
                       help='Email for NCBI Entrez (required for PubMed)')
    
    args = parser.parse_args()
    
    # Setup sources dictionary
    if args.source == 'all':
        sources = {'pubmed': True, 'gtr': True, 'snpedia': True, 'gwas': True}
    else:
        sources = {args.source: True}
    
    # Setup Entrez email if using PubMed
    if sources.get('pubmed'):
        try:
            from Bio import Entrez
            Entrez.email = args.email
            Entrez.tool = "GeneticProfileDatabase"
        except ImportError:
            logger.warning("biopython not available, skipping PubMed")
            sources['pubmed'] = False
    
    db = GeneticProfileDB()
    
    try:
        if args.gene:
            stats = enrich_gene_from_all_sources(args.gene, db, sources)
            print(f"\nEnrichment Summary for {args.gene}:")
            for source, source_stats in stats.items():
                if source != 'gene' and isinstance(source_stats, dict):
                    print(f"\n  {source.upper()}:")
                    print(f"    Processed: {source_stats.get('processed', 0)}")
                    print(f"    Added: {source_stats.get('added', 0)}")
                    print(f"    Skipped: {source_stats.get('skipped', 0)}")
        
        elif args.all:
            total_stats = enrich_all_genes(db, sources)
            print(f"\nTotal Enrichment Summary:")
            print(f"  Genes processed: {total_stats['total_genes']}")
            for source in ['pubmed', 'gtr', 'snpedia', 'gwas']:
                if sources.get(source):
                    print(f"\n  {source.upper()}:")
                    print(f"    Processed: {total_stats[source]['processed']}")
                    print(f"    Added: {total_stats[source]['added']}")
                    print(f"    Skipped: {total_stats[source]['skipped']}")
        
        else:
            parser.print_help()
    
    finally:
        db.close()


if __name__ == '__main__':
    main()

