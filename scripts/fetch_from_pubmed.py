#!/usr/bin/env python3
"""
Fetch research data from PubMed using NCBI Entrez API
Extracts structured data about genes, traits, and conditions
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('fetch_pubmed')

try:
    from Bio import Entrez
    from Bio.Entrez import efetch, esearch
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logger.warning("biopython not available. Install with: pip install biopython")


def setup_entrez(email: str = "user@example.com"):
    """Setup Entrez with email (required by NCBI)"""
    if BIOPYTHON_AVAILABLE:
        Entrez.email = email
        Entrez.tool = "GeneticProfileDatabase"


def search_pubmed_for_gene(gene_symbol: str, max_results: int = 20) -> List[str]:
    """
    Search PubMed for articles related to a gene.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'COMT')
        max_results: Maximum number of results to return
        
    Returns:
        List of PubMed IDs
    """
    if not BIOPYTHON_AVAILABLE:
        logger.error("biopython not available")
        return []
    
    try:
        # Search for gene symbol in title/abstract
        query = f"{gene_symbol}[Title/Abstract] AND (genetic OR genotype OR polymorphism OR variant)"
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        pubmed_ids = record.get("IdList", [])
        logger.info(f"Found {len(pubmed_ids)} PubMed articles for {gene_symbol}")
        return pubmed_ids
        
    except Exception as e:
        logger.error(f"Error searching PubMed for {gene_symbol}: {e}", exc_info=True)
        return []


def fetch_pubmed_article(pubmed_id: str) -> Optional[Dict]:
    """
    Fetch detailed information about a PubMed article.
    
    Args:
        pubmed_id: PubMed ID
        
    Returns:
        Dictionary with article information
    """
    if not BIOPYTHON_AVAILABLE:
        return None
    
    try:
        handle = Entrez.efetch(db="pubmed", id=pubmed_id, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        if not records:
            return None
        
        article = records['PubmedArticle'][0]['MedlineCitation']
        
        # Extract information
        title = article.get('Article', {}).get('ArticleTitle', '')
        abstract = ""
        if 'Abstract' in article.get('Article', {}):
            abstract_parts = article['Article']['Abstract'].get('AbstractText', [])
            if isinstance(abstract_parts, list):
                abstract = ' '.join([str(part) for part in abstract_parts])
            else:
                abstract = str(abstract_parts)
        
        # Extract authors
        authors = []
        if 'AuthorList' in article.get('Article', {}):
            for author in article['Article']['AuthorList']:
                if 'LastName' in author and 'ForeName' in author:
                    authors.append(f"{author['LastName']}, {author['ForeName']}")
        
        # Extract publication date
        pub_date = article.get('Article', {}).get('ArticleDate', {})
        year = None
        if pub_date:
            year = pub_date.get('Year')
        
        # Extract journal
        journal = article.get('MedlineJournalInfo', {}).get('MedlineTA', '')
        
        # Extract MeSH terms
        mesh_terms = []
        if 'MeshHeadingList' in article:
            for mesh in article['MeshHeadingList']:
                if 'DescriptorName' in mesh:
                    mesh_terms.append(str(mesh['DescriptorName']))
        
        # Extract keywords
        keywords = []
        if 'KeywordList' in article:
            for kw_list in article['KeywordList']:
                keywords.extend([str(kw) for kw in kw_list])
        
        return {
            'pubmed_id': pubmed_id,
            'title': title,
            'abstract': abstract,
            'authors': ', '.join(authors) if authors else None,
            'year': int(year) if year else None,
            'journal': journal,
            'mesh_terms': mesh_terms,
            'keywords': keywords
        }
        
    except Exception as e:
        logger.error(f"Error fetching PubMed article {pubmed_id}: {e}", exc_info=True)
        return None


def extract_gene_mentions(text: str, known_genes: List[str]) -> List[str]:
    """
    Extract gene symbols mentioned in text.
    
    Args:
        text: Text to search
        known_genes: List of known gene symbols
        
    Returns:
        List of gene symbols found
    """
    found_genes = []
    text_upper = text.upper()
    
    for gene in known_genes:
        # Look for gene symbol as whole word
        pattern = r'\b' + gene.upper() + r'\b'
        import re
        if re.search(pattern, text_upper):
            found_genes.append(gene)
    
    return found_genes


def process_gene_pubmed_data(gene_symbol: str, db: GeneticProfileDB) -> Dict:
    """
    Process PubMed data for a gene and add to database.
    
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
    
    pubmed_ids = search_pubmed_for_gene(gene_symbol)
    
    stats = {'processed': 0, 'added': 0, 'skipped': 0}
    
    for pubmed_id in pubmed_ids:
        stats['processed'] += 1
        
        # Check if already in database
        existing = db.check_research_reference_exists(pubmed_id=pubmed_id)
        if existing:
            stats['skipped'] += 1
            continue
        
        # Fetch article details
        article = fetch_pubmed_article(pubmed_id)
        if not article:
            continue
        
        # Add to database
        try:
            # Get next reference number
            cursor = db.conn.cursor()
            cursor.execute("SELECT MAX(reference_number) FROM research_references")
            result = cursor.fetchone()
            next_ref = (result[0] if result[0] else 0) + 1
            
            ref_id = db.add_research_reference_if_not_exists(
                reference_number=next_ref,
                authors=article.get('authors'),
                year=article.get('year'),
                title=article.get('title'),
                journal=article.get('journal'),
                pubmed_id=pubmed_id,
                abstract=article.get('abstract'),
                keywords=', '.join(article.get('keywords', [])) if article.get('keywords') else None,
                reference_type='journal'
            )
            
            if ref_id:
                stats['added'] += 1
                logger.info(f"Added PubMed article {pubmed_id} for {gene_symbol}")
            
            # Rate limiting - respect PubMed API limits (3 requests/second)
            time.sleep(0.4)
            
        except Exception as e:
            logger.error(f"Error adding PubMed article {pubmed_id}: {e}", exc_info=True)
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch research data from PubMed')
    parser.add_argument('--gene', type=str, help='Process specific gene')
    parser.add_argument('--all', action='store_true', help='Process all genes in database')
    parser.add_argument('--email', type=str, default='user@example.com',
                       help='Email for NCBI Entrez (required)')
    
    args = parser.parse_args()
    
    if not BIOPYTHON_AVAILABLE:
        print("Error: biopython not available. Install with: pip install biopython")
        sys.exit(1)
    
    setup_entrez(args.email)
    
    db = GeneticProfileDB()
    
    try:
        if args.gene:
            stats = process_gene_pubmed_data(args.gene, db)
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
                stats = process_gene_pubmed_data(gene_symbol, db)
                
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

