#!/usr/bin/env python3
"""
Fetch SNP information from SNPedia
Extracts genotype interpretations, trait associations, and health condition links
"""

import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('fetch_snpedia')

SNPEDIA_BASE = "https://www.snpedia.com/index.php/"


def fetch_snpedia_page(rs_number: str) -> Optional[Dict]:
    """
    Fetch SNP information from SNPedia.
    
    Args:
        rs_number: SNP rs number (e.g., 'rs4680')
        
    Returns:
        Dictionary with SNP information
    """
    try:
        url = f"{SNPEDIA_BASE}Rs{rs_number}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return None
        
        # Extract genotype interpretations
        genotypes = {}
        genotype_section = content_div.find('div', class_='genotype')
        if genotype_section:
            for genotype_elem in genotype_section.find_all('div', class_='genotype'):
                genotype_text = genotype_elem.get_text(strip=True)
                # Parse genotype format: (A;G) = ...
                match = re.search(r'\(([^)]+)\)\s*=\s*(.+)', genotype_text)
                if match:
                    genotype = match.group(1)
                    interpretation = match.group(2)
                    genotypes[genotype] = interpretation
        
        # Extract trait associations
        traits = []
        trait_links = content_div.find_all('a', href=re.compile(r'/index.php/[A-Z]'))
        for link in trait_links:
            trait_text = link.get_text(strip=True)
            if trait_text and len(trait_text) > 2:
                traits.append(trait_text)
        
        # Extract health condition links
        conditions = []
        condition_links = content_div.find_all('a', href=re.compile(r'/index.php/[A-Z]'))
        for link in condition_links:
            link_text = link.get_text(strip=True)
            # Look for condition-related terms
            if any(term in link_text.lower() for term in ['disease', 'disorder', 'syndrome', 'condition']):
                conditions.append(link_text)
        
        # Extract research references
        references = []
        ref_section = content_div.find('div', class_='references')
        if ref_section:
            for ref_link in ref_section.find_all('a', href=re.compile(r'pubmed')):
                pubmed_match = re.search(r'pubmed/(\d+)', ref_link.get('href', ''))
                if pubmed_match:
                    references.append(pubmed_match.group(1))
        
        return {
            'rs_number': rs_number,
            'genotypes': genotypes,
            'traits': traits,
            'conditions': conditions,
            'references': references,
            'url': url
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching SNPedia page for {rs_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing SNPedia page for {rs_number}: {e}", exc_info=True)
        return None


def process_snp_snpedia_data(rs_number: str, db: GeneticProfileDB) -> Dict:
    """
    Process SNPedia data for a SNP and add to database.
    
    Args:
        rs_number: SNP rs number
        db: Database connection
        
    Returns:
        Dictionary with processing statistics
    """
    # Get SNP from database
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM snps WHERE rs_number = ?", (rs_number,))
    snp_row = cursor.fetchone()
    
    if not snp_row:
        logger.warning(f"SNP {rs_number} not found in database")
        return {'processed': 0, 'added': 0, 'skipped': 0}
    
    snp = dict(snp_row)
    gene_id = snp.get('gene_id')
    
    # Fetch SNPedia data
    snpedia_data = fetch_snpedia_page(rs_number)
    if not snpedia_data:
        return {'processed': 0, 'added': 0, 'skipped': 0}
    
    stats = {'processed': 1, 'added': 0, 'skipped': 0}
    
    # Add to database_sources
    try:
        # Check if already exists
        cursor.execute("""
            SELECT id FROM database_sources 
            WHERE gene_id = ? AND source_type = 'SNPedia' AND source_url LIKE ?
        """, (gene_id, f"%{rs_number}%"))
        
        if cursor.fetchone():
            stats['skipped'] += 1
            return stats
        
        # Build key information
        key_info_parts = []
        if snpedia_data.get('genotypes'):
            key_info_parts.append(f"Genotypes: {len(snpedia_data['genotypes'])}")
        if snpedia_data.get('traits'):
            key_info_parts.append(f"Traits: {', '.join(snpedia_data['traits'][:5])}")
        if snpedia_data.get('conditions'):
            key_info_parts.append(f"Conditions: {', '.join(snpedia_data['conditions'][:5])}")
        
        key_info = ' | '.join(key_info_parts)
        
        cursor.execute("""
            INSERT INTO database_sources (gene_id, source_type, source_url, key_information)
            VALUES (?, ?, ?, ?)
        """, (gene_id, 'SNPedia', snpedia_data['url'], key_info))
        
        db.conn.commit()
        stats['added'] += 1
        logger.info(f"Added SNPedia data for {rs_number}")
        
        # Rate limiting - be respectful
        time.sleep(1.0)
        
    except Exception as e:
        logger.error(f"Error adding SNPedia data for {rs_number}: {e}", exc_info=True)
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch SNP data from SNPedia')
    parser.add_argument('--rs', type=str, help='Process specific SNP (rs number)')
    parser.add_argument('--all', action='store_true', help='Process all SNPs in database')
    
    args = parser.parse_args()
    
    db = GeneticProfileDB()
    
    try:
        if args.rs:
            stats = process_snp_snpedia_data(args.rs, db)
            print(f"\nProcessing Summary for {args.rs}:")
            print(f"  Processed: {stats['processed']}")
            print(f"  Added: {stats['added']}")
            print(f"  Skipped: {stats['skipped']}")
        
        elif args.all:
            cursor = db.conn.cursor()
            cursor.execute("SELECT rs_number FROM snps")
            snps = [row[0] for row in cursor.fetchall()]
            
            print(f"Processing {len(snps)} SNPs...")
            
            total_stats = {'processed': 0, 'added': 0, 'skipped': 0}
            
            for rs_number in snps:
                print(f"\nProcessing {rs_number}...")
                stats = process_snp_snpedia_data(rs_number, db)
                
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

