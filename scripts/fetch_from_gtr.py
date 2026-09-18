#!/usr/bin/env python3
"""
Fetch genetic testing information from GTR (Genetic Testing Registry)
"""

import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('fetch_gtr')

GTR_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def search_gtr_for_gene(gene_symbol: str) -> List[str]:
    """
    Search GTR for genetic tests related to a gene.
    
    Args:
        gene_symbol: Gene symbol
        
    Returns:
        List of GTR test IDs
    """
    try:
        # GTR uses NCBI Entrez API
        url = f"{GTR_API_BASE}esearch.fcgi"
        params = {
            'db': 'gtr',
            'term': f"{gene_symbol}[Gene]",
            'retmax': 50,
            'retmode': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        test_ids = data.get('esearchresult', {}).get('idlist', [])
        
        logger.info(f"Found {len(test_ids)} GTR tests for {gene_symbol}")
        return test_ids
        
    except Exception as e:
        logger.error(f"Error searching GTR for {gene_symbol}: {e}", exc_info=True)
        return []


def fetch_gtr_test_details(test_id: str) -> Optional[Dict]:
    """
    Fetch detailed information about a GTR test.
    
    Args:
        test_id: GTR test ID
        
    Returns:
        Dictionary with test information
    """
    try:
        url = f"{GTR_API_BASE}esummary.fcgi"
        params = {
            'db': 'gtr',
            'id': test_id,
            'retmode': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        test_data = data.get('result', {}).get(test_id, {})
        
        if not test_data:
            return None
        
        return {
            'test_id': test_id,
            'test_name': test_data.get('testname', ''),
            'gene_symbols': test_data.get('genesymbols', []),
            'conditions': test_data.get('conditions', []),
            'clinical_significance': test_data.get('clinicalsignificance', ''),
            'test_provider': test_data.get('provider', ''),
            'test_url': f"https://www.ncbi.nlm.nih.gov/gtr/tests/{test_id}/"
        }
        
    except Exception as e:
        logger.error(f"Error fetching GTR test {test_id}: {e}", exc_info=True)
        return None


def process_gene_gtr_data(gene_symbol: str, db: GeneticProfileDB) -> Dict:
    """
    Process GTR data for a gene and add to database.
    
    Args:
        gene_symbol: Gene symbol
        db: Database connection
        
    Returns:
        Dictionary with processing statistics
    """
    gene = db.get_gene_by_symbol(gene_symbol)
    if not gene:
        logger.warning(f"Gene {gene_symbol} not found in database")
        return {'processed': 0, 'added': 0, 'skipped': 0}
    
    test_ids = search_gtr_for_gene(gene_symbol)
    
    stats = {'processed': 0, 'added': 0, 'skipped': 0}
    
    for test_id in test_ids:
        stats['processed'] += 1
        
        # Fetch test details
        test_data = fetch_gtr_test_details(test_id)
        if not test_data:
            continue
        
        # Add to database_sources table
        try:
            # Check if already exists
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT id FROM database_sources 
                WHERE gene_id = ? AND source_type = 'GTR' AND source_url LIKE ?
            """, (gene['id'], f"%{test_id}%"))
            
            if cursor.fetchone():
                stats['skipped'] += 1
                continue
            
            # Add to database
            key_info = f"Test: {test_data.get('test_name', 'Unknown')}"
            if test_data.get('conditions'):
                key_info += f" | Conditions: {', '.join(test_data['conditions'])}"
            if test_data.get('clinical_significance'):
                key_info += f" | Clinical Significance: {test_data['clinical_significance']}"
            
            cursor.execute("""
                INSERT INTO database_sources (gene_id, source_type, source_url, key_information)
                VALUES (?, ?, ?, ?)
            """, (gene['id'], 'GTR', test_data.get('test_url', ''), key_info))
            
            db.conn.commit()
            stats['added'] += 1
            logger.info(f"Added GTR test {test_id} for {gene_symbol}")
            
            # Rate limiting
            time.sleep(0.4)
            
        except Exception as e:
            logger.error(f"Error adding GTR test {test_id}: {e}", exc_info=True)
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch genetic testing data from GTR')
    parser.add_argument('--gene', type=str, help='Process specific gene')
    parser.add_argument('--all', action='store_true', help='Process all genes in database')
    
    args = parser.parse_args()
    
    db = GeneticProfileDB()
    
    try:
        if args.gene:
            stats = process_gene_gtr_data(args.gene, db)
            print(f"\nProcessing Summary for {args.gene}:")
            print(f"  Processed: {stats['processed']}")
            print(f"  Added: {stats['added']}")
            print(f"  Skipped: {stats['skipped']}")
        
        elif args.all:
            genes = db.get_all_genes()
            print(f"Processing {len(genes)} genes...")
            
            total_stats = {'processed': 0, 'added': 0, 'skipped': 0}
            
            for gene in genes:
                gene_symbol = gene['gene_symbol']
                print(f"\nProcessing {gene_symbol}...")
                stats = process_gene_gtr_data(gene_symbol, db)
                
                total_stats['processed'] += stats['processed']
                total_stats['added'] += stats['added']
                total_stats['skipped'] += stats['skipped']
            
            print(f"\nTotal Summary:")
            print(f"  Processed: {total_stats['processed']}")
            print(f"  Added: {total_stats['added']}")
            print(f"  Skipped: {total_stats['skipped']}")
        
        else:
            parser.print_help()
    
    finally:
        db.close()


if __name__ == '__main__':
    main()

