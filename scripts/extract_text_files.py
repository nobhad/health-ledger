#!/usr/bin/env python3
"""
Extract content from text files (.txt, .log)
Handles various encodings and parses structured log files
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_logger

logger = get_logger('extract_text')


def detect_encoding(file_path: Path) -> str:
    """
    Detect file encoding.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Detected encoding name
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Fallback to utf-8 with errors='replace'
    return 'utf-8'


def extract_text_content(file_path: Path) -> str:
    """
    Extract text content from a file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        File content as string
    """
    encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        logger.info(f"Extracted {len(content)} characters from {file_path.name}")
        return content
        
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}", exc_info=True)
        return ""


def extract_dates_from_text(text: str) -> List[str]:
    """
    Extract dates from text content.
    
    Args:
        text: Text content
        
    Returns:
        List of date strings found
    """
    dates = []
    
    # Common date patterns
    patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # M/D/YY or MM/DD/YYYY
        r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}',  # Month Day, Year
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    
    return list(set(dates))  # Remove duplicates


def parse_log_entries(text: str) -> List[Dict]:
    """
    Parse structured log entries from text.
    
    Args:
        text: Log file content
        
    Returns:
        List of log entry dictionaries
    """
    entries = []
    lines = text.split('\n')
    
    current_entry = None
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(current_entry)
                current_entry = None
            continue
        
        # Try to detect log entry patterns
        # Common patterns: timestamp at start, or date followed by text
        date_match = re.match(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', line)
        if date_match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                'date': date_match.group(1),
                'text': line,
                'raw_line': line
            }
        elif current_entry:
            current_entry['text'] += '\n' + line
        else:
            # Start new entry without clear date
            current_entry = {
                'text': line,
                'raw_line': line
            }
    
    if current_entry:
        entries.append(current_entry)
    
    return entries


def process_text_file(file_path: Path) -> Dict:
    """
    Process a text file and extract all information.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Dictionary with extracted content and metadata
    """
    content = extract_text_content(file_path)
    
    result = {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'extracted_text': content,
        'encoding': detect_encoding(file_path),
        'file_size': file_path.stat().st_size,
        'created': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
        'dates_found': extract_dates_from_text(content),
        'log_entries': parse_log_entries(content) if file_path.suffix.lower() == '.log' else []
    }
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract content from text files')
    parser.add_argument('text_path', type=str, help='Path to text file')
    
    args = parser.parse_args()
    
    text_path = Path(args.text_path)
    if not text_path.exists():
        print(f"Error: Text file not found: {text_path}")
        sys.exit(1)
    
    result = process_text_file(text_path)
    print(f"Extracted text ({len(result['extracted_text'])} characters):")
    print(result['extracted_text'][:500])  # Print first 500 chars
    if result['dates_found']:
        print(f"\nDates found: {result['dates_found']}")
    if result['log_entries']:
        print(f"\nLog entries: {len(result['log_entries'])}")

