"""
Documents from a person's care: reading them and bringing them into the ledger.

A lab report, a visit note or a health-app export arrives as a PDF or a text
file. This module reads one, says what it holds, and — only when the person
confirms — stores it: the file copied into the data folder, a primary source
row holding the extracted text, and every reading it offers as a health
metric. Nothing is written on a dry run, which is what the import page shows
before asking.

What kind of document it is comes from the text, never from the file name:
one person's naming convention is not everybody's. A file imported again
replaces its earlier import rather than adding a second copy.

A scanned page has no text in it to read. Those go to OCR when the optional
extras are installed (requirements-extras.txt), and when they are not the
file is still worth keeping: it is filed with the records, plainly marked as
holding no searchable text, rather than turned away.
"""

import re
import shutil
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import config
from scripts.extract_health_metrics import (collect_health_log_metrics, collect_lab_metrics,
                                            parse_date, write_metrics)

READABLE_SUFFIXES = {'.pdf', '.txt', '.log', '.md', '.csv'}
MAX_STORED_TEXT = 50000          # what a primary source row keeps, as the older extractor did
EXCERPT_CHARACTERS = 600
MIN_MEANINGFUL_TEXT = 10

# Where a document's text came from, which decides what the page says about it.
TEXT_FROM_DOCUMENT = 'text'      # the file's own text layer
TEXT_FROM_OCR = 'ocr'            # read off the page picture by OCR
TEXT_FROM_NOTHING = 'none'       # a scan, with no OCR available to read it

KIND_LABELS = {
    'lab_result': 'Lab results',
    'health_log': 'Health log',
    'test_report': 'Test report',
    'document': 'Document',
}

# Words that say what a document is. Checked in this order; the first kind
# whose markers appear wins.
KIND_MARKERS = [
    ('test_report', ('pharmacogenomic', 'pharmacogenetic', 'genotype', 'phenotype',
                     'gene report', 'star allele')),
    ('lab_result', ('reference range', 'reference interval', 'specimen', 'collected',
                    'ordering provider', 'lab results', 'final report')),
    ('health_log', ('blood pressure', 'health log', 'vitals', 'chief complaint',
                    'visit', 'appointment')),
]

OCR_PAGE_MARKER = re.compile(r'^\s*---\s*Page\s+\d+\s*\(OCR\)\s*---\s*$', re.MULTILINE)

DATE_IN_TEXT = re.compile(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})')


class UnreadableDocument(ValueError):
    """The file is not a document this ledger can read."""


@dataclass
class DocumentSummary:
    """What a document holds, and what importing it would add."""
    file_name: str
    kind: str
    document_date: Optional[str]
    text_characters: int
    page_count: Optional[int]
    excerpt: str
    metrics: List[Dict] = field(default_factory=list)
    replaces: Optional[Dict] = None
    dry_run: bool = False
    source_id: Optional[int] = None
    text_source: str = TEXT_FROM_DOCUMENT
    text: str = field(default='', repr=False)
    gene_findings: List[Dict] = field(default_factory=list)
    medication_lists: List[Dict] = field(default_factory=list)
    unknown_genes: List[str] = field(default_factory=list)

    @property
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.kind, KIND_LABELS['document'])

    @property
    def has_text(self) -> bool:
        return self.text_source != TEXT_FROM_NOTHING

    @property
    def read_by_ocr(self) -> bool:
        return self.text_source == TEXT_FROM_OCR

    @property
    def metric_count(self) -> int:
        return len(self.metrics)

    @property
    def abnormal_count(self) -> int:
        return sum(1 for metric in self.metrics if metric.get('is_abnormal'))

    @property
    def medication_count(self) -> int:
        return sum(len(plan['items']) for plan in self.medication_lists)


# --- reading ----------------------------------------------------------------

@lru_cache(maxsize=1)
def ocr_available() -> bool:
    """Whether the optional OCR extras are installed, with the programs they need."""
    try:
        import pdf2image  # noqa: F401
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        return False
    return True


def read_by_ocr(path: Path) -> str:
    """
    The text OCR can read off a scanned PDF, or empty when it cannot.

    scripts/extract_pdf_text.extract_with_ocr already does this and returns
    nothing when the extras are missing, so there is one OCR path, not two.
    """
    try:
        from scripts.extract_pdf_text import extract_with_ocr
        text = extract_with_ocr(str(path)) or ''
    except Exception:
        return ''
    # That helper marks each page it OCRs; the summary already says the text
    # was read that way, so the markers are noise in the stored text.
    return OCR_PAGE_MARKER.sub('', text).strip()


def read_text(path: Path) -> Tuple[str, Optional[int], str]:
    """
    A document's text, its page count, and where the text came from.

    A PDF's own text layer is read first. A scanned page has no text layer,
    so an empty result is handed to OCR, which needs the optional extras.
    Without them, or when OCR finds nothing either, the text is empty and
    the source is TEXT_FROM_NOTHING: the file can still be kept with the
    records, it just cannot be searched.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in READABLE_SUFFIXES:
        raise UnreadableDocument(
            f'{suffix or "That file"} is not a kind this page reads. '
            f'Choose a PDF or a text file.')

    if suffix == '.pdf':
        try:
            import pdfplumber
        except ImportError as e:      # pragma: no cover - pdfplumber is a core requirement
            raise UnreadableDocument(f'PDF reading is unavailable: {e}')
        try:
            with pdfplumber.open(path) as pdf:
                pages = [page.extract_text() or '' for page in pdf.pages]
        except Exception as e:
            raise UnreadableDocument(f'The PDF could not be read: {e}')
        text = '\n'.join(pages)
        if len(text.strip()) >= MIN_MEANINGFUL_TEXT:
            return text, len(pages), TEXT_FROM_DOCUMENT
        scanned = read_by_ocr(path)
        if scanned.strip():
            return scanned, len(pages), TEXT_FROM_OCR
        return '', len(pages), TEXT_FROM_NOTHING

    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        raise UnreadableDocument(f'The file could not be read: {e}')
    if len(text.strip()) < MIN_MEANINGFUL_TEXT:
        # Whitespace is not text; reporting it as characters read would flatter
        # the file. Nothing found means nothing found.
        return '', None, TEXT_FROM_NOTHING
    return text, None, TEXT_FROM_DOCUMENT


def classify(text: str) -> str:
    """Which kind of document the text reads like."""
    lowered = text.lower()
    for kind, markers in KIND_MARKERS:
        if any(marker in lowered for marker in markers):
            return kind
    return 'document'


def first_date(text: str) -> Optional[str]:
    """The first date the document states, as YYYY-MM-DD."""
    for match in DATE_IN_TEXT.finditer(text):
        parsed = parse_date(match.group(1))
        if parsed:
            return parsed
    return None


def metrics_in(text: str, kind: str, document_date: Optional[str]) -> List[Dict]:
    """
    The readings this document offers, as rows ready for db.add_health_metric.

    A health log is a run of dated entries; a lab report is a list of
    analytes. Anything else is filed for its text alone.
    """
    if kind == 'health_log':
        return collect_health_log_metrics(text)
    if kind == 'lab_result':
        return collect_lab_metrics(text, document_date)
    return []


def read(path: Path, original_name: Optional[str] = None) -> DocumentSummary:
    """
    Read a document and describe it. Nothing is written.

    A file whose text could not be read is described too, rather than
    refused: the page offers to keep it with the records and says plainly
    that there is nothing in it to search.
    """
    path = Path(path)
    name = original_name or path.name
    text, page_count, text_source = read_text(path)

    kind = classify(text)
    document_date = first_date(text)
    excerpt = ' '.join(text.split())[:EXCERPT_CHARACTERS]
    return DocumentSummary(
        file_name=name, kind=kind, document_date=document_date,
        text_characters=len(text), page_count=page_count, excerpt=excerpt,
        metrics=metrics_in(text, kind, document_date),
        text_source=text_source, text=text)


def pharmacogenomic_plans(db, text: str, source_id=None, document_date=None,
                          source_name: str = '', add_genes: bool = False):
    """
    What a pharmacogenomic report offers: a phenotype per gene and the
    report's own medication lists.

    scripts/import_pharmacogenomics.py already reads both out of a report's
    text and splits the work into a plan and a write, so the page previews
    the plan and confirming applies it. The source is passed as a row
    because that is what the planner takes; on a preview it has no id yet.
    """
    from scripts.import_pharmacogenomics import plan_import
    source = {'id': source_id, 'source_name': source_name,
              'document_date': document_date, 'extracted_text': text}
    return plan_import(db, [source], add_missing_genes=add_genes)


# --- writing ----------------------------------------------------------------

def import_file(db, path: Path, original_name: Optional[str] = None,
                dry_run: bool = False, add_genes: bool = False) -> DocumentSummary:
    """
    Bring a document into the ledger.

    Copies the file into the data folder's primary_sources/documents/, writes
    a primary source holding the extracted text, and replaces that source's
    health metrics with the readings found. A pharmacogenomic report also
    fills the drug-metabolism tables, and with add_genes the genes it names
    that the ledger does not track yet are started. A file imported before,
    under the same name, is updated in place. Nothing is written on a dry run.
    """
    path = Path(path)
    original_name = original_name or path.name
    summary = read(path, original_name)
    stored_name = _safe_name(original_name)
    existing = db.get_primary_source_by_file_name(stored_name)
    summary.replaces = existing
    summary.dry_run = dry_run
    if summary.kind == 'test_report' and summary.has_text:
        summary.gene_findings, summary.medication_lists, summary.unknown_genes = (
            pharmacogenomic_plans(db, summary.text, source_id=existing['id'] if existing else None,
                                  document_date=summary.document_date,
                                  source_name=original_name, add_genes=add_genes))
    if dry_run:
        return summary

    text = summary.text
    documents_dir = Path(config.PRIMARY_SOURCES_DIR) / 'documents'
    documents_dir.mkdir(parents=True, exist_ok=True)
    stored = documents_dir / stored_name
    if path.resolve() != stored.resolve():
        shutil.copy(path, stored)

    fields = dict(
        source_name=Path(original_name).stem or stored_name,
        source_type=summary.kind,
        document_date=summary.document_date or datetime.now().strftime('%Y-%m-%d'),
        file_path=str(stored),
        file_name=stored_name,
        extracted_text=text[:MAX_STORED_TEXT] if summary.has_text else None,
    )
    if existing:
        source_id = existing['id']
        db.update_primary_source(source_id, **fields)
    else:
        source_id = db.add_primary_source(**fields)

    write_metrics(source_id, summary.metrics, db)

    # A pharmacogenomic report fills the drug-metabolism tables too. The plan
    # is made again now the source has an id, so its medication lists are
    # stored against the row that was just written.
    if summary.kind == 'test_report' and summary.has_text:
        from scripts.import_pharmacogenomics import apply_import
        gene_plans, medication_plans, unknown = pharmacogenomic_plans(
            db, text, source_id=source_id, document_date=summary.document_date,
            source_name=original_name, add_genes=add_genes)
        apply_import(db, gene_plans, medication_plans)
        summary.gene_findings, summary.medication_lists, summary.unknown_genes = (
            gene_plans, medication_plans, unknown)

    summary.source_id = source_id
    return summary


def _safe_name(name: str) -> str:
    """A file name safe to store: the same rule raw_dna.py uses."""
    return re.sub(r'[^A-Za-z0-9._-]+', '_', Path(name).name).strip('._') or 'document'
