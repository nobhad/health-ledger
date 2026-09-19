"""
Consumer DNA raw-data files: reading them and bringing them into the ledger.

Reads the download that 23andMe, AncestryDNA, MyHeritage, FamilyTreeDNA and
Living DNA give their customers: a text or CSV file (often zipped) with one
variant per line, as an rs number, a chromosome, a position and a genotype.
No two providers agree on the layout, so the header is sniffed first.

An import stores every called variant in snp_genotypes (one row per rs
number; a later import replaces an earlier one), records the file in
dna_imports and as a primary source, and reports which variants fall in
genes the ledger already tracks (variant_reference.py). Nothing is written
on a dry run.
"""

import csv
import gzip
import io
import json
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, TextIO, Tuple

import config
from variant_reference import KNOWN_VARIANTS

PROVIDER_NAMES = {
    '23andme': '23andMe',
    'ancestry': 'AncestryDNA',
    'myheritage': 'MyHeritage',
    'ftdna': 'FamilyTreeDNA',
    'livingdna': 'Living DNA',
    'generic': 'DNA raw data',
}
NO_CALLS = {'--', '00', '0', '', 'NN', 'DD', 'II', '-'}
ANCESTRY_CHROMOSOMES = {'23': 'X', '24': 'Y', '25': 'XY', '26': 'MT'}
SOURCE_TYPE = 'dna_raw_data'
MAX_HEADER_LINES = 100


class UnreadableRawData(ValueError):
    """The file is not a DNA raw-data download this ledger can read."""


@dataclass
class Variant:
    rsid: str
    chromosome: str
    position: str
    genotype: str


@dataclass
class RawDnaFile:
    provider: str            # key into PROVIDER_NAMES
    build: Optional[str]     # reference build stated in the header, if any
    variants: List[Variant] = field(default_factory=list)
    no_calls: int = 0        # lines with no genotype called

    @property
    def provider_name(self) -> str:
        return PROVIDER_NAMES.get(self.provider, self.provider)


@dataclass
class KnownMatch:
    rsid: str
    gene: str
    description: str
    genotype: str
    in_ledger: bool          # the gene already has a row in `genes`


@dataclass
class ImportSummary:
    file_name: str
    provider: str
    build: Optional[str]
    variant_count: int
    no_calls: int
    matches: List[KnownMatch]
    dry_run: bool
    import_id: Optional[int] = None

    @property
    def provider_name(self) -> str:
        return PROVIDER_NAMES.get(self.provider, self.provider)

    @property
    def in_ledger(self) -> List[KnownMatch]:
        return [m for m in self.matches if m.in_ledger]

    @property
    def not_in_ledger(self) -> List[KnownMatch]:
        return [m for m in self.matches if not m.in_ledger]

    @property
    def genes_in_ledger(self) -> List[str]:
        return sorted({m.gene for m in self.in_ledger})

    @property
    def genes_not_in_ledger(self) -> List[str]:
        return sorted({m.gene for m in self.not_in_ledger})


# --- reading -----------------------------------------------------------------

def open_text(path: Path) -> TextIO:
    """The file's text, whether it is plain, gzipped or a zip with one file inside."""
    suffix = path.suffix.lower()
    if suffix == '.zip':
        archive = zipfile.ZipFile(path)
        members = [m for m in archive.namelist()
                   if not m.endswith('/') and not m.startswith('__MACOSX')]
        if len(members) != 1:
            raise UnreadableRawData(
                'The zip file should hold one raw-data file; this one holds '
                f'{len(members)}.')
        return io.TextIOWrapper(archive.open(members[0]), encoding='utf-8', errors='replace')
    if suffix == '.gz':
        return io.TextIOWrapper(gzip.open(path), encoding='utf-8', errors='replace')
    return open(path, encoding='utf-8', errors='replace', newline='')


def _detect(comments: List[str], header: str) -> Tuple[str, str]:
    """(provider key, layout) from the comment lines and the column header."""
    blob = ' '.join(comments).lower()
    columns = [c.strip().strip('"').lower() for c in re.split(r'[\t,]', header.lstrip('#').strip())]
    if columns[:5] == ['rsid', 'chromosome', 'position', 'allele1', 'allele2']:
        return ('ancestry', 'alleles')
    if columns[:4] == ['rsid', 'chromosome', 'position', 'genotype']:
        if '23andme' in blob:
            return ('23andme', 'genotype')
        if 'living dna' in blob or 'livingdna' in blob:
            return ('livingdna', 'genotype')
        return ('generic', 'genotype')
    if columns[:4] == ['rsid', 'chromosome', 'position', 'result']:
        if 'myheritage' in blob:
            return ('myheritage', 'genotype')
        if 'familytreedna' in blob or 'family tree dna' in blob:
            return ('ftdna', 'genotype')
        return ('myheritage', 'genotype')
    raise UnreadableRawData(
        'This does not look like a DNA raw-data download. Expected columns like '
        '"rsid, chromosome, position, genotype" (23andMe), "rsid, chromosome, '
        'position, allele1, allele2" (AncestryDNA) or "RSID, CHROMOSOME, '
        'POSITION, RESULT" (MyHeritage, FamilyTreeDNA).')


def _build(comments: List[str]) -> Optional[str]:
    blob = ' '.join(comments)
    m = re.search(r'(?:build|GRCh)\s*(\d{2})', blob, re.IGNORECASE)
    return m.group(1) if m else None


def parse(path: Path) -> RawDnaFile:
    """Read a raw-data file into memory. Raises UnreadableRawData."""
    path = Path(path)
    with open_text(path) as text:
        comments: List[str] = []
        header = None
        for _ in range(MAX_HEADER_LINES):
            line = text.readline()
            if not line:
                break
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('#'):
                comments.append(stripped)
                # 23andMe puts the column header in a comment line
                if re.match(r'#\s*rsid', stripped, re.IGNORECASE):
                    header = stripped
                    break
                continue
            header = stripped
            break
        if header is None:
            raise UnreadableRawData('The file has no column header.')
        provider, layout = _detect(comments, header)
        result = RawDnaFile(provider=provider, build=_build(comments))
        delimiter = ',' if ',' in header and '\t' not in header else '\t'
        reader = csv.reader(text, delimiter=delimiter)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            row = [c.strip() for c in row]
            if len(row) < 4 or not row[0]:
                continue
            rsid, chromosome, position = row[0], row[1], row[2]
            if layout == 'alleles':
                if len(row) < 5:
                    continue
                genotype = (row[3] + row[4]).upper()
                chromosome = ANCESTRY_CHROMOSOMES.get(chromosome, chromosome)
            else:
                genotype = row[3].upper()
            if genotype in NO_CALLS or set(genotype) <= {'0', '-'}:
                result.no_calls += 1
                continue
            result.variants.append(Variant(rsid, chromosome, position, genotype))
    if not result.variants:
        raise UnreadableRawData('The file lists no called variants.')
    return result


# --- matching and writing ---------------------------------------------------

def known_matches(db, variants: List[Variant]) -> List[KnownMatch]:
    """The variants that variant_reference.py knows, flagged by whether the gene is in the ledger."""
    ledger_genes = {g['gene_symbol'].upper() for g in db.get_all_genes()}
    matches = []
    for v in variants:
        known = KNOWN_VARIANTS.get(v.rsid)
        if known:
            gene, description = known
            matches.append(KnownMatch(v.rsid, gene, description, v.genotype,
                                      gene.upper() in ledger_genes))
    matches.sort(key=lambda m: (not m.in_ledger, m.gene, m.rsid))
    return matches


def import_file(db, path: Path, original_name: Optional[str] = None,
                dry_run: bool = False) -> ImportSummary:
    """
    Bring a raw-data file into the ledger.

    Writes snp_genotypes (replacing rows for the same rs numbers), a
    dna_imports row, a primary source, and an snps row for each matched
    variant whose gene is in the ledger. Copies the file into the data
    folder's primary_sources/dna/. Nothing is written on a dry run.
    """
    path = Path(path)
    original_name = original_name or path.name
    parsed = parse(path)
    matches = known_matches(db, parsed.variants)
    summary = ImportSummary(original_name, parsed.provider, parsed.build,
                            len(parsed.variants), parsed.no_calls, matches, dry_run)
    if dry_run:
        return summary

    dna_dir = Path(config.PRIMARY_SOURCES_DIR) / 'dna'
    dna_dir.mkdir(parents=True, exist_ok=True)
    stored = dna_dir / _safe_name(original_name)
    if path.resolve() != stored.resolve():
        shutil.copy(path, stored)

    metadata = json.dumps({'provider': summary.provider_name, 'build': parsed.build,
                           'variants': summary.variant_count, 'no_calls': parsed.no_calls})
    source_id = db.add_primary_source(
        source_name=f'{summary.provider_name} raw data', source_type=SOURCE_TYPE,
        institution=summary.provider_name, document_date=datetime.now().strftime('%Y-%m-%d'),
        file_path=str(stored), file_name=stored.name, metadata=metadata,
        extracted_text=(f'{summary.variant_count} called variants, {parsed.no_calls} not called. '
                        f'Reference build {parsed.build or "unknown"}.'))
    import_id = db.add_dna_import(
        file_name=stored.name, provider=summary.provider_name, build=parsed.build,
        variant_count=summary.variant_count, no_call_count=parsed.no_calls,
        matched_count=len(summary.in_ledger), primary_source_id=source_id)
    db.replace_snp_genotypes(import_id, ((v.rsid, v.chromosome, v.position, v.genotype)
                                         for v in parsed.variants))
    for match in summary.in_ledger:
        gene = db.get_gene_by_symbol(match.gene)
        if gene:
            db.ensure_snp(match.rsid, gene['id'])
    summary.import_id = import_id
    return summary


def _safe_name(name: str) -> str:
    stem = re.sub(r'[^A-Za-z0-9._-]+', '_', Path(name).name).strip('._') or 'raw_data'
    return stem
