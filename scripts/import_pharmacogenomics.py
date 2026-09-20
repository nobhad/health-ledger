#!/usr/bin/env python3
"""
Fill the pharmacogenomic tables from a genetic test report's extracted text.

A pharmacogenomic panel report states two things this ledger can use:

  1. A phenotype per gene ("CYP2D6 Extensive (Normal) Metabolizer",
     "HTR2A Increased Sensitivity", "HLA-B*1502 Normal Risk").
  2. Its medication lists, each under a category heading: "Use as
     Directed", "Moderate Gene-Drug Interaction", "Significant Gene-Drug
     Interaction".

The Import page does this now: adding a report there fills these tables in
the same preview-then-confirm step (documents.py calls plan_import and
apply_import below). This script stays for a report already in the ledger,
for --set, and for anyone who prefers the terminal.

This script reads both from the extracted text of the ledger's test-report
sources, pairs each gene's phenotype with the genotype already on file and
the medications the gene is known to affect (pharmacogenomic_reference.py),
and writes:

  - one pharmacogenomic_data row per gene (+ gene_pharmacogenomic_drugs)
  - the report's medication categories into medication_interactions

Both writes replace what an earlier run stored, so the script is safe to
run again. Nothing is written with --dry-run.

    python3 scripts/import_pharmacogenomics.py --dry-run
    python3 scripts/import_pharmacogenomics.py
    python3 scripts/import_pharmacogenomics.py --source 9
    python3 scripts/import_pharmacogenomics.py --set VKORC1="Increased Sensitivity"
    python3 scripts/import_pharmacogenomics.py --add-missing-genes

--set records a phenotype the text did not yield (a gene the report shows
only as a figure, say), and is applied on top of what was parsed.

The patterns are generic to this style of report. A gene the ledger does
not list is reported and skipped; add it to the genes table first.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB
from pharmacogenomic_reference import drugs_for_gene
from config import get_logger

logger = get_logger('import_pharmacogenomics')

# A gene symbol as reports print it, with an optional allele suffix that is
# kept apart (HLA-B*1502 -> gene HLA-B, allele *1502).
GENE_TOKEN = r'(?P<gene>[A-Z][A-Z0-9]{1,7}(?:-[A-Z0-9]{1,3})?)(?P<allele>\*[0-9:]+)?'

PHENOTYPE_PHRASES = [
    r'Extensive \(Normal\) Metabolizer', r'Ultrarapid Metabolizer', r'Ultra-rapid Metabolizer',
    r'Rapid Metabolizer', r'Normal Metabolizer', r'Intermediate Metabolizer',
    r'Poor Metabolizer', r'Likely (?:Poor|Intermediate|Normal|Rapid) Metabolizer',
    r'Normal Response', r'Reduced Response', r'Increased Response',
    r'Increased Sensitivity', r'Reduced Sensitivity', r'Normal Sensitivity',
    r'Normal Risk', r'Increased Risk', r'High Risk',
    r'Normal Activity', r'Reduced Activity', r'Low Activity', r'Intermediate Activity',
    r'Normal Function', r'Decreased Function', r'Poor Function', r'Increased Function',
    r'Positive', r'Negative',
]
PHENOTYPE_RE = re.compile(
    GENE_TOKEN + r'\s+(?P<phenotype>' + '|'.join(PHENOTYPE_PHRASES) + r')\b'
)

CATEGORY_HEADINGS = [
    ('significant', re.compile(r'^Significant Gene-Drug Interactions?(?: \(Continued\))?$', re.I)),
    ('moderate', re.compile(r'^Moderate Gene-Drug Interactions?(?: \(Continued\))?$', re.I)),
    ('use_as_directed', re.compile(r'^Use as Directed(?: \(Continued\))?$', re.I)),
]
CATEGORY_LABELS = {
    'significant': 'Significant gene-drug interaction',
    'moderate': 'Moderate gene-drug interaction',
    'use_as_directed': 'Use as directed',
}
SEVERITY = {'significant': 0, 'moderate': 1, 'use_as_directed': 2}

# One medication on a line: "sertraline (Zoloft®) 6". Lines carrying two
# medications are a table row whose columns collapsed; they cannot be
# assigned to a category and end the list.
DRUG_LINE_RE = re.compile(
    r'^(?P<drug>[a-z][a-z0-9\-/ ]*[a-z0-9])\s*\((?P<brand>[^()]*?)\s*[®™]?\)\s*(?P<notes>[\d, ]*)$'
)
DRUG_ANYWHERE_RE = re.compile(r'[a-z][a-z0-9\-/ ]*\([^()]*[®™]\)')

# Between a heading and its medications a report prints page furniture: a
# strip of gene symbols, a strip of phenotypes, a drug-class label
# ("Antidepressants"). Those keep the list open. Running text, a footnote
# ("6: Use of this drug ...") or a non-canonical "Gene-drug Interaction"
# table header closes it.
PROSE_RE = re.compile(r'(\. |\.$|^\d+:)')
TABLE_HEADER_RE = re.compile(r'gene-drug interaction', re.I)


def _lines(text: str) -> List[str]:
    out = []
    for raw in text.splitlines():
        line = re.sub(r'\s+', ' ', raw).strip()
        if line:
            out.append(line)
    return out


def parse_phenotypes(text: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Gene -> {'phenotype', 'allele'} from a report's text. The first
    statement per gene wins: reports lead with their summary table.
    """
    found: Dict[str, Dict[str, Optional[str]]] = {}
    for line in _lines(text):
        for m in PHENOTYPE_RE.finditer(line):
            gene = m.group('gene')
            if gene in found:
                continue
            found[gene] = {'phenotype': m.group('phenotype'), 'allele': m.group('allele')}
    return found


def _closes_list(line: str) -> bool:
    return (bool(PROSE_RE.search(line)) or len(line) > 70
            or bool(TABLE_HEADER_RE.search(line))
            or len(DRUG_ANYWHERE_RE.findall(line)) >= 2)


def parse_medication_categories(text: str) -> List[Dict[str, Optional[str]]]:
    """
    Medications under the report's category headings. A heading sets the
    category for the single-medication lines that follow it, short labels
    in between are ignored, and running text or a collapsed table row ends
    the list. A medication named under more than one category keeps the
    most significant.
    """
    best: Dict[str, Dict[str, Optional[str]]] = {}
    category: Optional[str] = None
    for line in _lines(text):
        heading = next((name for name, pattern in CATEGORY_HEADINGS if pattern.match(line)), None)
        if heading:
            category = heading
            continue
        m = DRUG_LINE_RE.match(line)
        if not m:
            if _closes_list(line):
                category = None
            continue
        if category is None:
            continue
        drug = m.group('drug').strip()
        item = {
            'drug_name': drug,
            'brand_name': m.group('brand').strip() or None,
            'category': category,
            'notes': m.group('notes').strip() or None,
        }
        current = best.get(drug)
        if current is None or SEVERITY[category] < SEVERITY[current['category']]:
            best[drug] = item
    return sorted(best.values(), key=lambda i: (SEVERITY[i['category']], i['drug_name']))


def test_report_sources(db: GeneticProfileDB) -> List[Dict]:
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id, source_name, document_date, extracted_text
        FROM primary_sources
        WHERE source_type = 'test_report' AND extracted_text IS NOT NULL
        ORDER BY document_date DESC, id DESC
    """)
    return [dict(row) for row in cursor.fetchall()]


def genotype_for(db: GeneticProfileDB, gene_id: int) -> Optional[str]:
    genotypes = db.get_genotypes_for_gene(gene_id)
    if not genotypes:
        return None
    # Prefer the longer spelling, which carries the zygosity note.
    return max((g.get('genotype') or '' for g in genotypes), key=len) or None


def plan_import(db: GeneticProfileDB, sources: List[Dict],
                overrides: Optional[Dict[str, str]] = None,
                add_missing_genes: bool = False) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    What an import would write: per-gene records, per-source medication
    lists, and the gene symbols the report names that the ledger lacks.
    With add_missing_genes those symbols are planned as new genes
    (gene_id None until apply_import creates them) instead of skipped.
    """
    phenotypes: Dict[str, Dict[str, Optional[str]]] = {}
    medication_plans = []
    for source in sources:
        text = source['extracted_text'] or ''
        for gene, info in parse_phenotypes(text).items():
            phenotypes.setdefault(gene, info)
        items = parse_medication_categories(text)
        if items:
            medication_plans.append({'source': source, 'items': items})
    for gene, phenotype in (overrides or {}).items():
        phenotypes[gene.upper()] = {'phenotype': phenotype, 'allele': None}

    gene_plans, unknown = [], []
    for gene, info in sorted(phenotypes.items()):
        record = db.get_gene_by_symbol(gene)
        if not record and not add_missing_genes:
            unknown.append(gene + (info['allele'] or ''))
            continue
        genotype = genotype_for(db, record['id']) if record else None
        parts = [p for p in (genotype, (gene + info['allele']) if info['allele'] else None) if p]
        genotype_phenotype = (' | '.join(parts) + ' — ' if parts else '') + info['phenotype']
        gene_plans.append({
            'gene': gene,
            'gene_id': record['id'] if record else None,
            'metabolism_status': info['phenotype'],
            'genotype_phenotype': genotype_phenotype,
            'drugs': drugs_for_gene(gene),
        })
    return gene_plans, medication_plans, unknown


def apply_import(db: GeneticProfileDB, gene_plans: List[Dict], medication_plans: List[Dict]) -> Tuple[int, int]:
    for plan in gene_plans:
        if plan['gene_id'] is None:
            plan['gene_id'] = db.add_gene(plan['gene'], plan['gene'])
        db.replace_pharmacogenomic_data_for_gene(
            plan['gene_id'], plan['metabolism_status'], plan['genotype_phenotype'], plan['drugs'])
    rows = 0
    for plan in medication_plans:
        rows += db.replace_medication_interactions_for_source(plan['source']['id'], plan['items'])
    return len(gene_plans), rows


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dry-run', action='store_true', help='show what would be written, write nothing')
    parser.add_argument('--source', type=int, action='append', help='only this test-report source id (repeatable)')
    parser.add_argument('--set', action='append', default=[], metavar='GENE=PHENOTYPE',
                        help='record a phenotype the text did not yield')
    parser.add_argument('--add-missing-genes', action='store_true',
                        help='create a gene the report names but the ledger lacks, instead of skipping it')
    parser.add_argument('--db', help='database path (default: the configured one)')
    args = parser.parse_args(argv)

    overrides = {}
    for item in args.set:
        if '=' not in item:
            parser.error(f'--set expects GENE=PHENOTYPE, got {item!r}')
        gene, phenotype = item.split('=', 1)
        overrides[gene.strip()] = phenotype.strip()

    db = GeneticProfileDB(args.db) if args.db else GeneticProfileDB()
    try:
        sources = test_report_sources(db)
        if args.source:
            sources = [s for s in sources if s['id'] in set(args.source)]
        if not sources and not overrides:
            print('No test-report sources with extracted text. Nothing to do.')
            return 1

        gene_plans, medication_plans, unknown = plan_import(db, sources, overrides, args.add_missing_genes)

        print(f'Test reports read: {len(sources)}')
        for s in sources:
            print(f'  #{s["id"]}  {s["source_name"]}  ({s["document_date"] or "undated"})')
        print(f'\nGenes with a phenotype: {len(gene_plans)}')
        for plan in gene_plans:
            added = '  (new gene)' if plan['gene_id'] is None else ''
            print(f'  {plan["gene"]:<9} {plan["metabolism_status"]:<32} '
                  f'{len(plan["drugs"])} reference drug{"" if len(plan["drugs"]) == 1 else "s"}{added}')
        if unknown:
            print(f'\nNamed in the report but not in the ledger (skipped): {", ".join(unknown)}')
        for plan in medication_plans:
            counts = {}
            for item in plan['items']:
                counts[item['category']] = counts.get(item['category'], 0) + 1
            summary = ', '.join(f'{CATEGORY_LABELS[c].lower()}: {n}' for c, n in sorted(counts.items(), key=lambda kv: SEVERITY[kv[0]]))
            print(f'\nMedication categories from #{plan["source"]["id"]}: {len(plan["items"])} ({summary})')
            for item in plan['items']:
                if item['category'] != 'use_as_directed':
                    brand = f' ({item["brand_name"]})' if item['brand_name'] else ''
                    print(f'  {CATEGORY_LABELS[item["category"]]:<34} {item["drug_name"]}{brand}')

        if args.dry_run:
            print('\nDry run: nothing written.')
            return 0
        genes, rows = apply_import(db, gene_plans, medication_plans)
        print(f'\nWritten: {genes} gene records, {rows} medication rows.')
        return 0
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
