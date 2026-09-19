#!/usr/bin/env python3
"""
Check variant_reference.py against NCBI dbSNP.

For every rs number in the table, ask dbSNP which gene it sits in and compare
that with the gene symbol the table pairs it with. Prints a line per
disagreement and exits non-zero if there is one.

    python3 scripts/check_variant_reference.py

PRIVACY: this sends only the hardcoded public rs numbers in
variant_reference.py. It never opens the database and never sends anything
from anyone's records.

This talks to the network, so it is NOT part of the test suite. Run it by
hand after editing the table.
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from variant_reference import KNOWN_VARIANTS

ESUMMARY = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=snp&retmode=json&id='
BATCH = 20


def dbsnp_genes(rsids):
    """{rsid: [gene symbols]} from dbSNP, in batches."""
    found = {}
    numeric = [r[2:] for r in rsids if r.startswith('rs') and r[2:].isdigit()]
    for start in range(0, len(numeric), BATCH):
        chunk = numeric[start:start + BATCH]
        with urllib.request.urlopen(ESUMMARY + ','.join(chunk), timeout=30) as response:
            result = json.load(response).get('result', {})
        for uid in result.get('uids', []):
            found['rs' + uid] = [g.get('name') for g in result[uid].get('genes', []) if g.get('name')]
        time.sleep(0.4)
    return found


def main() -> int:
    try:
        found = dbsnp_genes(list(KNOWN_VARIANTS))
    except Exception as e:
        print(f'Could not reach dbSNP: {e}')
        return 2

    problems = []
    for rsid, (gene, _) in sorted(KNOWN_VARIANTS.items()):
        genes = found.get(rsid)
        if genes is None:
            problems.append(f'{rsid:13} not found in dbSNP (table says {gene})')
        elif not genes:
            problems.append(f'{rsid:13} dbSNP assigns no gene (table says {gene})')
        elif gene.upper() not in [g.upper() for g in genes]:
            problems.append(f'{rsid:13} table says {gene}, dbSNP says {", ".join(genes)}')

    checked = len(KNOWN_VARIANTS)
    print(f'{checked - len(problems)} of {checked} gene assignments agree with dbSNP.')
    for line in problems:
        print('  ' + line)
    if problems:
        print('\nThe descriptions are not checked here; confirm those against CPIC or PharmGKB.')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
