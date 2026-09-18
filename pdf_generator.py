#!/usr/bin/env python3
"""
PDF Generation Module
Generates PDFs from HTML content using WeasyPrint
All processing is local-only for privacy
"""

import html
import os
import shutil
import sys
import ctypes
import tempfile
from pathlib import Path
from typing import Optional

# Set library path for macOS Homebrew libraries before importing WeasyPrint
# This ensures WeasyPrint can find GTK+ and gobject libraries
if sys.platform == 'darwin':  # macOS
    homebrew_lib = '/opt/homebrew/lib'
    if os.path.exists(homebrew_lib):
        # Set DYLD_FALLBACK_LIBRARY_PATH (works with SIP)
        current_fallback = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
        if homebrew_lib not in current_fallback:
            os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = (
                f"{homebrew_lib}:{current_fallback}" if current_fallback else homebrew_lib
            )
        # Also try DYLD_LIBRARY_PATH (may not work with SIP but worth trying)
        current_lib = os.environ.get('DYLD_LIBRARY_PATH', '')
        if homebrew_lib not in current_lib:
            os.environ['DYLD_LIBRARY_PATH'] = (
                f"{homebrew_lib}:{current_lib}" if current_lib else homebrew_lib
            )
        
        # Try to preload gobject library using ctypes
        try:
            gobject_path = os.path.join(homebrew_lib, 'libgobject-2.0.0.dylib')
            if os.path.exists(gobject_path):
                ctypes.CDLL(gobject_path)
        except (OSError, AttributeError):
            # If preloading fails, continue anyway - WeasyPrint might still work
            pass

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

sys.path.insert(0, str(Path(__file__).parent))
from config import get_logger, BASE_DIR

logger = get_logger('pdf_generator')

# Relative stylesheet links in generated documents resolve against the
# project root, not the current working directory.
PDF_BASE_URL = str(BASE_DIR)


def wrap_pdf_document(title: str, body_html: str) -> str:
    """
    Wrap a body fragment in the full document the PDF stylesheets expect.

    Mirrors templates/pdf_base.html (pdf.css + print.css) for callers that
    run outside a Flask request context.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="static/css/pdf.css">
    <link rel="stylesheet" href="static/css/print.css">
</head>
<body>
    <div class="pdf-content">
{body_html}
    </div>
</body>
</html>
"""


def generate_pdf_from_html(html_content: str, output_path: str, 
                           base_url: Optional[str] = None) -> bool:
    """
    Generate PDF from HTML content.
    
    Args:
        html_content: HTML string to convert to PDF
        output_path: Path where PDF will be saved
        base_url: Base URL for resolving relative paths (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        font_config = FontConfiguration()
        
        # Generate PDF
        HTML(string=html_content, base_url=base_url).write_pdf(
            output,
            font_config=font_config
        )
        
        logger.info(f"PDF generated: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return False


def generate_summary_pdf(db, output_path: str) -> bool:
    """
    Generate PDF from personalized summary.
    
    Args:
        db: Database connection
        output_path: Path where PDF will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from scripts.generate_personalized_summary import generate_summary_html
        
        html_content = wrap_pdf_document('Genetic Profile Summary', generate_summary_html(db))
        return generate_pdf_from_html(html_content, output_path, base_url=PDF_BASE_URL)
        
    except Exception as e:
        logger.error(f"Error generating summary PDF: {e}", exc_info=True)
        return False


def generate_profile_pdf(db, output_path: str) -> bool:
    """
    Generate PDF from full genetic profile.
    
    Args:
        db: Database connection
        output_path: Path where PDF will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from profile_generator import generate_profile_html
        
        html_content = wrap_pdf_document('Genetic Profile', generate_profile_html(db))
        return generate_pdf_from_html(html_content, output_path, base_url=PDF_BASE_URL)
        
    except Exception as e:
        logger.error(f"Error generating profile PDF: {e}", exc_info=True)
        return False


def generate_source_pdf(db, source_id: int, output_path: str) -> bool:
    """
    Generate PDF from a primary source.
    
    Args:
        db: Database connection
        source_id: Primary source ID
        output_path: Path where PDF will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        source = db.get_primary_source_with_findings(source_id)
        if not source:
            logger.error(f"Source {source_id} not found")
            return False
        
        # Generate HTML for source. Everything from the record is escaped:
        # extracted text and findings are free text and may contain < or &.
        esc = html.escape
        name = source.get('source_name') or 'Source'
        findings_html = ''.join(
            f"<li><strong>{esc(f.get('finding_type') or 'Finding')}:</strong> {esc(f.get('finding_text') or '')}</li>"
            for f in source.get('findings', [])
        )
        body = f"""
            <h1>{esc(name)}</h1>
            <p><strong>Type:</strong> {esc(source.get('source_type') or 'Unknown')}</p>
            {f"<p><strong>Institution:</strong> {esc(source['institution'])}</p>" if source.get('institution') else ''}
            {f"<p><strong>Date:</strong> {esc(str(source['document_date']))}</p>" if source.get('document_date') else ''}
            <h2>Extracted Text</h2>
            <pre>{esc(source.get('extracted_text') or 'No text extracted')}</pre>
            <h2>Findings</h2>
            <ul>{findings_html}</ul>
        """
        html_content = wrap_pdf_document(name, body)
        
        return generate_pdf_from_html(html_content, output_path, base_url=PDF_BASE_URL)
        
    except Exception as e:
        logger.error(f"Error generating source PDF: {e}", exc_info=True)
        return False


def generate_doctor_pdf(db, doctor_type: str, output_path: str,
                       include_original: bool = True,
                       include_medications: bool = True,
                       include_stats: bool = True) -> bool:
    """
    Generate PDF for a specific doctor specialty.
    Includes original genetic test report at the end if available.
    
    Args:
        db: Database connection
        doctor_type: Doctor specialty (e.g., 'cardiologist', 'psychiatrist')
        output_path: Path where PDF will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    tmp_path = None
    separator_path = None
    try:
        from scripts.generate_doctor_document import generate_doctor_document_html
        
        # Generate main document HTML with options
        html_content = generate_doctor_document_html(db, doctor_type,
                                                     include_medications=include_medications,
                                                     include_stats=include_stats)
        
        # Create temporary file for main document
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp_path = tmp.name
        
        # Generate main PDF
        if not generate_pdf_from_html(html_content, tmp_path, base_url=PDF_BASE_URL):
            return False
        
        # Try to append original genetic test report if requested
        if include_original:
            test_info = db.get_genetic_test_info()
            if test_info and test_info.get('file_path'):
                original_pdf_path = Path(test_info['file_path'])
                if not original_pdf_path.is_absolute():
                    original_pdf_path = BASE_DIR / original_pdf_path
                if original_pdf_path.exists() and original_pdf_path.suffix.lower() == '.pdf':
                    try:
                        from PyPDF2 import PdfReader, PdfWriter
                        
                        # Read main PDF
                        main_pdf = PdfReader(tmp_path)
                        writer = PdfWriter()
                        
                        # Add all pages from main PDF
                        for page in main_pdf.pages:
                            writer.add_page(page)
                        
                        # Add separator page
                        separator_html = """
                        <!DOCTYPE html>
                        <html>
                        <head><meta charset="UTF-8"></head>
                        <body style="padding: 50px; text-align: center;">
                            <h1>Original Genetic Test Report</h1>
                            <p>Attached below is a copy of the original genetic test report.</p>
                        </body>
                        </html>
                        """
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as sep_tmp:
                            separator_path = sep_tmp.name
                        HTML(string=separator_html).write_pdf(separator_path)
                        separator_pdf = PdfReader(separator_path)
                        for page in separator_pdf.pages:
                            writer.add_page(page)
                        
                        # Add all pages from original PDF
                        original_pdf = PdfReader(str(original_pdf_path))
                        for page in original_pdf.pages:
                            writer.add_page(page)
                        
                        # Write merged PDF
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)
                        
                        logger.info(f"PDF generated with original test report appended: {output_path}")
                        return True
                        
                    except ImportError:
                        logger.warning("PyPDF2 not available, cannot append original PDF. Install with: pip install PyPDF2")
                    except Exception as e:
                        logger.warning(f"Could not append original PDF: {e}. Using main document only.")
        
        # No original PDF appended: use the main document as-is
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(tmp_path, output_path)
        return True
        
    except Exception as e:
        logger.error(f"Error generating doctor PDF: {e}", exc_info=True)
        return False
    finally:
        for path in (tmp_path, separator_path):
            if path:
                Path(path).unlink(missing_ok=True)

