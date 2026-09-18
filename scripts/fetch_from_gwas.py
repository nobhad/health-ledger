#!/usr/bin/env python3
"""
Fetch association data from GWAS Catalog
Extracts trait associations, p-values, effect sizes, and population information
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

logger = get_logger('fetch_gwas')

GWAS_API_BASE = "https://www.ebi.ac.uk/gwas/api/v1/"


def search_gwas_for_gene(gene_symbol: str) -> List[str]:
    """
    Search GWAS Catalog for associations related to a gene.
    
    Args:
        gene_symbol: Gene symbol
        
    Returns:
        List of GWAS association IDs
    """
    try:
        url = f"{GWAS_API_BASE}associations"
        params = {
            'gene_name': gene_symbol,
            'size': 100,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        associations = data.get('_embedded', {}).get('associations', [])
        
        association_ids = [assoc.get('associationId') for assoc in associations if assoc.get('associationId')]
        
        logger.info(f"Found {len(association_ids)} GWAS associations for {gene_symbol}")
        return association_ids
        
    except Exception as e:
        logger.error(f"Error searching GWAS for {gene_symbol}: {e}", exc_info=True)
        return []


def fetch_gwas_association(association_id: str) -> Optional[Dict]:
    """
    Fetch detailed information about a GWAS association.
    
    Args:
        association_id: GWAS association ID
        
    Returns:
        Dictionary with association information
    """
    try:
        url = f"{GWAS_API_BASE}associations/{association_id}"
        params = {'format': 'json'}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract trait information
        traits = []
        if 'efoTraits' in data:
            for trait in data['efoTraits']:
                traits.append(trait.get('trait', ''))
        
        # Extract p-value
        p_value = None
        if 'pvalue' in data:
            p_value = data['pvalue']
        
        # Extract effect size
        effect_size = None
        if 'beta' in data:
            effect_size = data['beta']
        elif 'or' in data:
            effect_size = data['or']
        
        # Extract population
        population = None
        if 'ancestries' in data and data['ancestries']:
            population = data['ancestries'][0].get('type', '')
        
        # Extract study information
        study_id = data.get('studyId', '')
        pubmed_id = None
        if 'study' in data and 'pubmedId' in data['study']:
            pubmed_id = data['study']['pubmedId']
        
        return {
            'association_id': association_id,
            'traits': traits,
            'p_value': p_value,
            'effect_size': effect_size,
            'population': population,
            'study_id': study_id,
            'pubmed_id': pubmed_id,
            'url': f"https://www.ebi.ac.uk/gwas/associations/{association_id}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching GWAS association {association_id}: {e}", exc_info=True)
        return None


def process_gene_gwas_data(gene_symbol: str, db: GeneticProfileDB) -> Dict:
    """
    Process GWAS data for a gene and add to database.
    
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
    
    association_ids = search_gwas_for_gene(gene_symbol)
    
    stats = {'processed': 0, 'added': 0, 'skipped': 0}
    
    for assoc_id in association_ids:
        stats['processed'] += 1
        
        # Fetch association details
        assoc_data = fetch_gwas_association(assoc_id)
        if not assoc_data:
            continue
        
        # Add to database_sources
        try:
            # Check if already exists
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT id FROM database_sources 
                WHERE gene_id = ? AND source_type = 'GWAS Catalog' AND source_url LIKE ?
            """, (gene['id'], f"%{assoc_id}%"))
            
            if cursor.fetchone():
                stats['skipped'] += 1
                continue
            
            # Build key information
            key_info_parts = []
            if assoc_data.get('traits'):
                key_info_parts.append(f"Traits: {', '.join(assoc_data['traits'][:3])}")
            if assoc_data.get('p_value'):
                key_info_parts.append(f"P-value: {assoc_data['p_value']}")
            if assoc_data.get('effect_size'):
                key_info_parts.append(f"Effect: {assoc_data['effect_size']}")
            if assoc_data.get('population'):
                key_info_parts.append(f"Population: {assoc_data['population']}")
            
            key_info = ' | '.join(key_info_parts)
            
            cursor.execute("""
                INSERT INTO database_sources (gene_id, source_type, source_url, key_information)
                VALUES (?, ?, ?, ?)
            """, (gene['id'], 'GWAS Catalog', assoc_data['url'], key_info))
            
            db.conn.commit()
            stats['added'] += 1
            logger.info(f"Added GWAS association {assoc_id} for {gene_symbol}")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error adding GWAS association {assoc_id}: {e}", exc_info=True)
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch association data from GWAS Catalog')
    parser.add_argument('--gene', type=str, help='Process specific gene')
    parser.add_argument('--all', action='store_true', help='Process all genes in database')
    
    args = parser.parse_args()
    
    db = GeneticProfileDB()
    
    try:
        if args.gene:
            stats = process_gene_gwas_data(args.gene, db)
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
                stats = process_gene_gwas_data(gene_symbol, db)
                
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

