#!/usr/bin/env python3
"""
Extract text from PDF files
Supports multiple extraction methods including OCR for image-based PDFs
"""

import sys
from pathlib import Path
from typing import Optional

def extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber"""
    import pdfplumber
    
    text_content = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                text_content.append(f"\n--- Page {i+1} ---\n")
                text_content.append(text)
    return "\n".join(text_content)


def extract_with_ocr(pdf_path: str) -> str:
    """
    Extract text from image-based PDFs using OCR.
    Converts PDF pages to images and runs OCR.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        return ""
    
    text_content = []
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path)
        
        for i, image in enumerate(images):
            # Run OCR on image
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text_content.append(f"\n--- Page {i+1} (OCR) ---\n")
                text_content.append(page_text)
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""
    
    return "\n".join(text_content)


def extract_pdf_text(pdf_path: str, use_ocr: bool = True) -> str:
    """
    Extract text from PDF file with fallback methods.
    
    Args:
        pdf_path: Path to PDF file
        use_ocr: Whether to use OCR if text extraction yields little text
        
    Returns:
        Extracted text string
    """
    # Try pdfplumber first
    text = extract_with_pdfplumber(pdf_path)
    
    # If text is very short, likely image-based PDF - try OCR
    if use_ocr and len(text.strip()) < 500:
        print(f"PDF appears to be image-based ({len(text)} chars), trying OCR...")
        ocr_text = extract_with_ocr(pdf_path)
        if len(ocr_text) > len(text):
            print(f"OCR extracted {len(ocr_text)} characters (vs {len(text)} from text extraction)")
            return ocr_text
        elif text:
            # Combine both
            return text + "\n\n--- OCR Text ---\n" + ocr_text
    
    return text

def extract_with_pypdf2(pdf_path):
    """Extract text using PyPDF2"""
    import PyPDF2
    
    text_content = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Total pages: {len(pdf_reader.pages)}")
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text:
                text_content.append(f"\n--- Page {i+1} ---\n")
                text_content.append(text)
    return "\n".join(text_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_pdf_text.py <file.pdf>")
        sys.exit(1)
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)
    
    print(f"Extracting text from {pdf_path}...")
    
    try:
        text = extract_with_pdfplumber(pdf_path)
        print("✅ Successfully extracted with pdfplumber")
    except ImportError:
        try:
            text = extract_with_pypdf2(pdf_path)
            print("✅ Successfully extracted with PyPDF2")
        except ImportError:
            print("❌ Error: No PDF library available")
            print("   Install with: pip3 install pdfplumber")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error extracting with PyPDF2: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error extracting with pdfplumber: {e}")
        sys.exit(1)
    
    # Save extracted text
    output_file = Path("center_for_human_genetics_extracted_text.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"✅ Text extracted to {output_file}")
    print(f"   Total characters: {len(text)}")
    
    # Look for genetic information
    import re
    
    # Find gene names
    gene_pattern = r'\b(ADRA2A|CES1A1|COMT|CYP1A2|CYP2B6|CYP2C9|CYP2C19|CYP2D6|CYP3A4|CYP3A5|HLA-A|HLA-B|HTR2A|SLC6A4|UGT1A1|UGT2B15|VKORC1)\b'
    genes = re.findall(gene_pattern, text, re.IGNORECASE)
    if genes:
        print(f"\nGenes found: {', '.join(set(genes))}")
    
    # Find rs numbers
    rs_pattern = r'rs\d+'
    rs_numbers = re.findall(rs_pattern, text)
    if rs_numbers:
        print(f"SNPs found: {len(set(rs_numbers))} unique")
        print(f"  Examples: {', '.join(list(set(rs_numbers))[:10])}")
    
    # Find dates
    date_pattern = r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}'
    dates = re.findall(date_pattern, text)
    if dates:
        print(f"Dates found: {len(set(dates))} unique")
        print(f"  Examples: {', '.join(list(set(dates))[:5])}")

