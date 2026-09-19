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
"""

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import config
from scripts.extract_health_metrics import (collect_health_log_metrics, collect_lab_metrics,
                                            parse_date, write_metrics)

READABLE_SUFFIXES = {'.pdf', '.txt', '.log', '.md', '.csv'}
MAX_STORED_TEXT = 50000          # what a primary source row keeps, as the older extractor did
EXCERPT_CHARACTERS = 600
MIN_MEANINGFUL_TEXT = 10

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

    @property
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.kind, KIND_LABELS['document'])

    @property
    def metric_count(self) -> int:
        return len(self.metrics)

    @property
    def abnormal_count(self) -> int:
        return sum(1 for metric in self.metrics if metric.get('is_abnormal'))


# --- reading ----------------------------------------------------------------

def read_text(path: Path) -> tuple:
    """
    The text of a document, and its page count when it has pages.

    PDFs go through pdfplumber, which reads the text layer. A scanned page
    has no text layer, so a PDF of photographs comes back empty; the caller
    says so rather than storing a blank record.
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
        return '\n'.join(pages), len(pages)

    try:
        return path.read_text(encoding='utf-8', errors='replace'), None
    except OSError as e:
        raise UnreadableDocument(f'The file could not be read: {e}')


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
    """Read a document and describe it. Nothing is written."""
    path = Path(path)
    name = original_name or path.name
    text, page_count = read_text(path)

    if len(text.strip()) < MIN_MEANINGFUL_TEXT:
        raise UnreadableDocument(
            'No text could be read from that file. A scanned or photographed '
            'page has no text in it to extract.')

    kind = classify(text)
    document_date = first_date(text)
    excerpt = ' '.join(text.split())[:EXCERPT_CHARACTERS]
    return DocumentSummary(
        file_name=name, kind=kind, document_date=document_date,
        text_characters=len(text), page_count=page_count, excerpt=excerpt,
        metrics=metrics_in(text, kind, document_date))


# --- writing ----------------------------------------------------------------

def import_file(db, path: Path, original_name: Optional[str] = None,
                dry_run: bool = False) -> DocumentSummary:
    """
    Bring a document into the ledger.

    Copies the file into the data folder's primary_sources/documents/, writes
    a primary source holding the extracted text, and replaces that source's
    health metrics with the readings found. A file imported before, under the
    same name, is updated in place. Nothing is written on a dry run.
    """
    path = Path(path)
    original_name = original_name or path.name
    summary = read(path, original_name)
    stored_name = _safe_name(original_name)
    existing = db.get_primary_source_by_file_name(stored_name)
    summary.replaces = existing
    summary.dry_run = dry_run
    if dry_run:
        return summary

    text, _ = read_text(path)
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
        extracted_text=text[:MAX_STORED_TEXT],
    )
    if existing:
        source_id = existing['id']
        db.update_primary_source(source_id, **fields)
    else:
        source_id = db.add_primary_source(**fields)

    write_metrics(source_id, summary.metrics, db)
    summary.source_id = source_id
    return summary


def _safe_name(name: str) -> str:
    """A file name safe to store: the same rule raw_dna.py uses."""
    return re.sub(r'[^A-Za-z0-9._-]+', '_', Path(name).name).strip('._') or 'document'
