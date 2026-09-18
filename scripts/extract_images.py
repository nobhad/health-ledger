#!/usr/bin/env python3
"""
Extract text from image files using OCR
Supports TIF, JPG, PNG, BMP formats
"""

import sys
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
import pytesseract
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_logger

logger = get_logger('extract_images')


def extract_text_from_image(image_path: Path) -> str:
    """
    Extract text from an image file using OCR.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Extracted text string
    """
    try:
        # Open image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run OCR
        text = pytesseract.image_to_string(image)
        
        logger.info(f"Extracted {len(text)} characters from {image_path.name}")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from {image_path}: {e}", exc_info=True)
        return ""


def extract_image_metadata(image_path: Path) -> Dict:
    """
    Extract metadata from image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with metadata
    """
    metadata = {
        'file_name': image_path.name,
        'file_size': image_path.stat().st_size,
        'created': datetime.fromtimestamp(image_path.stat().st_mtime).isoformat(),
        'format': image_path.suffix.lower()
    }
    
    try:
        from PIL.ExifTags import TAGS
        image = Image.open(image_path)
        
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTime':
                    metadata['exif_date'] = value
                elif tag == 'DateTimeOriginal':
                    metadata['exif_date_original'] = value
        
        metadata['width'] = image.width
        metadata['height'] = image.height
        metadata['mode'] = image.mode
        
    except Exception as e:
        logger.debug(f"Could not extract EXIF data from {image_path}: {e}")
    
    return metadata


def process_image_file(image_path: Path) -> Dict:
    """
    Process an image file and extract all information.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with extracted text and metadata
    """
    result = {
        'file_path': str(image_path),
        'file_name': image_path.name,
        'extracted_text': extract_text_from_image(image_path),
        'metadata': extract_image_metadata(image_path)
    }
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract text from image files')
    parser.add_argument('image_path', type=str, help='Path to image file')
    
    args = parser.parse_args()
    
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    result = process_image_file(image_path)
    print(f"Extracted text ({len(result['extracted_text'])} characters):")
    print(result['extracted_text'])
    print(f"\nMetadata: {result['metadata']}")

