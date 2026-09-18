#!/usr/bin/env python3
"""
Unified Extraction Interface
Single entry point for extracting from ALL file types in primary_sources folder
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import get_logger

logger = get_logger('unified_extractor')


def detect_file_type(file_path: Path) -> str:
    """
    Detect file type by extension and content.
    
    Args:
        file_path: Path to file
        
    Returns:
        File type string
    """
    ext = file_path.suffix.lower()
    
    type_map = {
        '.pdf': 'pdf',
        '.tif': 'image',
        '.tiff': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.bmp': 'image',
        '.txt': 'text',
        '.log': 'text',
        '.dcm': 'dicom',
        '.dicom': 'dicom'
    }
    
    return type_map.get(ext, 'unknown')


def extract_file(file_path: Path) -> Optional[Dict]:
    """
    Extract information from a file based on its type.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with extracted information, or None if failed
    """
    file_type = detect_file_type(file_path)
    
    try:
        if file_type == 'pdf':
            from scripts.extract_all_primary_sources import extract_pdf_text, extract_metadata_from_filename
            text = extract_pdf_text(str(file_path))
            metadata = extract_metadata_from_filename(file_path)
            return {
                'file_path': str(file_path),
                'file_type': 'pdf',
                'text': text,
                'metadata': metadata
            }
        
        elif file_type == 'image':
            from scripts.extract_images import process_image_file
            result = process_image_file(file_path)
            return {
                'file_path': str(file_path),
                'file_type': 'image',
                'text': result.get('extracted_text', ''),
                'metadata': result.get('metadata', {})
            }
        
        elif file_type == 'text':
            from scripts.extract_text_files import process_text_file
            result = process_text_file(file_path)
            return {
                'file_path': str(file_path),
                'file_type': 'text',
                'text': result.get('extracted_text', ''),
                'metadata': result
            }
        
        elif file_type == 'dicom':
            from scripts.extract_dicom import process_dicom_file
            result = process_dicom_file(file_path)
            return {
                'file_path': str(file_path),
                'file_type': 'dicom',
                'text': result.get('extracted_text', ''),
                'metadata': result.get('metadata', {})
            }
        
        else:
            logger.warning(f"Unknown file type: {file_path.suffix}")
            return {
                'file_path': str(file_path),
                'file_type': 'unknown',
                'text': '',
                'metadata': {}
            }
    
    except Exception as e:
        logger.error(f"Error extracting {file_path}: {e}", exc_info=True)
        return None


def process_all_files(primary_sources_dir: Path, db: Optional[GeneticProfileDB] = None) -> Dict:
    """
    Process all files in primary_sources directory.
    
    Args:
        primary_sources_dir: Directory containing source files
        db: Optional database connection (if None, only extracts, doesn't save)
        
    Returns:
        Dictionary with processing statistics
    """
    if not primary_sources_dir.exists():
        logger.error(f"Directory not found: {primary_sources_dir}")
        return {'error': 'Directory not found'}
    
    # Get all files
    all_files = []
    extensions = ['.pdf', '.tif', '.TIF', '.jpg', '.jpeg', '.png', '.txt', '.log', '.dcm', '.DCM']
    for ext in extensions:
        all_files.extend(primary_sources_dir.glob(f"*{ext}"))
        # Also check subdirectories (but skip DICOM directories for now)
        if ext not in ['.dcm', '.DCM']:
            all_files.extend(primary_sources_dir.rglob(f"*{ext}"))
    
    # Remove directories and duplicates
    all_files = list(set([f for f in all_files if f.is_file()]))
    all_files.sort()
    
    logger.info(f"Found {len(all_files)} files to process")
    
    stats = {
        'total': len(all_files),
        'processed': 0,
        'failed': 0,
        'by_type': {}
    }
    
    for file_path in all_files:
        file_type = detect_file_type(file_path)
        stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
        
        result = extract_file(file_path)
        if result:
            stats['processed'] += 1
            if db:
                # Save to database using extract_all_primary_sources logic
                from scripts.extract_all_primary_sources import process_file
                cross_ref_data = {'lab_results': {}, 'test_results': {}, 'visit_dates': []}
                process_file(file_path, db, cross_ref_data)
        else:
            stats['failed'] += 1
    
    return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified file extraction from primary_sources')
    parser.add_argument('--dir', type=str, default='primary_sources',
                       help='Directory containing source files')
    parser.add_argument('--save', action='store_true',
                       help='Save extracted data to database')
    parser.add_argument('--file', type=str,
                       help='Process single file instead of directory')
    
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        result = extract_file(file_path)
        if result:
            print(f"Extracted from {file_path.name}:")
            print(f"  Type: {result['file_type']}")
            print(f"  Text length: {len(result.get('text', ''))}")
            print(f"  Metadata: {result.get('metadata', {})}")
        else:
            print("Failed to extract file")
            sys.exit(1)
    
    else:
        sources_dir = Path(args.dir)
        db = GeneticProfileDB() if args.save else None
        
        try:
            stats = process_all_files(sources_dir, db)
            print(f"\nProcessing Summary:")
            print(f"  Total files: {stats['total']}")
            print(f"  Processed: {stats['processed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"\nBy type:")
            for file_type, count in stats['by_type'].items():
                print(f"  {file_type}: {count}")
        finally:
            if db:
                db.close()


if __name__ == '__main__':
    main()

