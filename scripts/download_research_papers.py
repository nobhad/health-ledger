#!/usr/bin/env python3
"""
Download research papers as PDFs from PubMed and other sources
Saves PDFs to research_papers/ folder and links them to database records
"""

import json
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('download_papers')

# Create research_papers directory
RESEARCH_PAPERS_DIR = Path('research_papers')
RESEARCH_PAPERS_DIR.mkdir(exist_ok=True)


def download_pdf_from_url(url: str, output_path: Path) -> bool:
    """Download PDF from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if content is PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            logger.warning(f"URL does not appear to be a PDF: {url}")
            return False
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded PDF: {output_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading PDF from {url}: {e}")
        return False


def get_pubmed_pdf_url(pubmed_id: str) -> Optional[str]:
    """
    Get PDF URL for a PubMed article.
    Note: Many PubMed articles don't have free PDFs available.
    This attempts to find open access or publisher links.
    """
    try:
        # Try PMC (PubMed Central) for open access articles
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pubmed_id}/pdf/"
        response = requests.head(pmc_url, timeout=10)
        if response.status_code == 200:
            return pmc_url
        
        # Try direct PubMed link (usually redirects to publisher)
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
        # Note: Most publishers require subscription, so this often won't work
        
        return None
        
    except Exception as e:
        logger.debug(f"Could not get PubMed PDF URL for {pubmed_id}: {e}")
        return None


def download_pubmed_paper(pubmed_id: str) -> Optional[Path]:
    """
    Attempt to download a paper from PubMed.
    Returns path to downloaded PDF if successful, None otherwise.
    """
    pdf_path = RESEARCH_PAPERS_DIR / f"PMID_{pubmed_id}.pdf"
    
    # Skip if already downloaded
    if pdf_path.exists():
        logger.info(f"PDF already exists: {pdf_path.name}")
        return pdf_path
    
    # Try to get PDF URL
    pdf_url = get_pubmed_pdf_url(pubmed_id)
    
    if pdf_url:
        if download_pdf_from_url(pdf_url, pdf_path):
            return pdf_path
    
    # If direct download fails, log for manual download
    logger.warning(f"Could not download PDF for PubMed ID {pubmed_id}")
    logger.info(f"  Manual download: https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/")
    
    return None


def download_doi_paper(doi: str) -> Optional[Path]:
    """
    Attempt to download a paper using DOI.
    Many DOIs resolve to publisher pages that require subscription.
    """
    try:
        # Try to resolve DOI to URL
        doi_url = f"https://doi.org/{doi}"
        response = requests.get(doi_url, allow_redirects=True, timeout=10)
        
        final_url = response.url
        
        # Check if final URL is a PDF
        if final_url.lower().endswith('.pdf'):
            # Extract filename from URL or use DOI
            safe_doi = doi.replace('/', '_')
            pdf_path = RESEARCH_PAPERS_DIR / f"DOI_{safe_doi}.pdf"
            
            if download_pdf_from_url(final_url, pdf_path):
                return pdf_path
        
        # If not a direct PDF, log for manual download
        logger.warning(f"DOI {doi} resolves to non-PDF page: {final_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving DOI {doi}: {e}")
        return None


def process_citations_from_json(json_file: Path, db: GeneticProfileDB) -> Dict:
    """
    Process citations from extracted_citations.json and download PDFs.
    
    Returns:
        Dictionary with download statistics
    """
    if not json_file.exists():
        logger.error(f"Citations file not found: {json_file}")
        return {'total': 0, 'downloaded': 0, 'skipped': 0, 'failed': 0}
    
    with open(json_file, 'r', encoding='utf-8') as f:
        citations = json.load(f)
    
    stats = {'total': len(citations), 'downloaded': 0, 'skipped': 0, 'failed': 0, 'updated': 0}
    
    logger.info(f"Processing {len(citations)} citations...")
    
    for citation in citations:
        pubmed_id = citation.get('pubmed_id')
        doi = citation.get('doi')
        citation_number = citation.get('citation_number')
        
        pdf_path = None
        
        # Try to download PDF
        if pubmed_id:
            pdf_path = download_pubmed_paper(pubmed_id)
            time.sleep(1)  # Rate limiting
        elif doi:
            pdf_path = download_doi_paper(doi)
            time.sleep(1)  # Rate limiting
        
        # Update database with PDF path
        if pdf_path and pdf_path.exists():
            pdf_relative_path = str(pdf_path.relative_to(Path.cwd()))
            
            # Check if citation exists and update it
            existing = db.check_citation_exists(pubmed_id=pubmed_id, doi=doi,
                                               citation_number=citation_number)
            
            if existing:
                # Update existing citation with PDF path
                cursor = db.conn.cursor()
                cursor.execute("""
                    UPDATE citations 
                    SET pdf_file_path = ? 
                    WHERE id = ?
                """, (pdf_relative_path, existing['id']))
                db.conn.commit()
                stats['updated'] += 1
            else:
                # Add new citation if it doesn't exist
                try:
                    db.add_reference_if_not_exists(
                        citation_number=citation_number or 0,
                        authors=citation.get('authors'),
                        year=citation.get('year'),
                        title=citation.get('title'),
                        journal=citation.get('journal'),
                        volume=citation.get('volume'),
                        pages=citation.get('pages'),
                        doi=doi,
                        pubmed_id=pubmed_id,
                        url=citation.get('url'),
                        reference_type=citation.get('reference_type', 'journal'),
                        pdf_file_path=pdf_relative_path
                    )
                    stats['updated'] += 1
                except Exception as e:
                    logger.error(f"Error adding citation to database: {e}")
            
            stats['downloaded'] += 1
        else:
            if pubmed_id or doi:
                stats['failed'] += 1
            else:
                stats['skipped'] += 1
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download research papers as PDFs')
    parser.add_argument('--json', type=str, default='extracted_citations.json',
                       help='Path to extracted citations JSON file')
    parser.add_argument('--pubmed-id', type=str, help='Download specific PubMed ID')
    parser.add_argument('--doi', type=str, help='Download specific DOI')
    
    args = parser.parse_args()
    
    db = GeneticProfileDB()
    
    try:
        if args.pubmed_id:
            pdf_path = download_pubmed_paper(args.pubmed_id)
            if pdf_path:
                print(f"Downloaded: {pdf_path}")
            else:
                print(f"Could not download PubMed ID {args.pubmed_id}")
        
        elif args.doi:
            pdf_path = download_doi_paper(args.doi)
            if pdf_path:
                print(f"Downloaded: {pdf_path}")
            else:
                print(f"Could not download DOI {args.doi}")
        
        else:
            json_file = Path(args.json)
            stats = process_citations_from_json(json_file, db)
            
            print(f"\nDownload Summary:")
            print(f"  Total citations: {stats['total']}")
            print(f"  Downloaded: {stats['downloaded']}")
            print(f"  Updated in database: {stats['updated']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Skipped: {stats['skipped']}")
    
    finally:
        db.close()


if __name__ == '__main__':
    main()

