#!/usr/bin/env python3
"""
Check variant_reference.py against public reference databases.

Three passes, in order of how firmly they can judge:

  1. GENE (NCBI dbSNP, automatic gate)
     Every rs number must resolve to the gene symbol the table pairs it
     with. A disagreement fails the run.

  2. STAR ALLELE AND FUNCTION (CPIC, automatic gate)
     For the pharmacogenes CPIC curates, a description beginning with a
     star allele such as "*2, no function" must name an allele CPIC
     actually defines at that position, and any function wording must
     match CPIC's clinical function for it. A disagreement fails the run.
     CPIC covers only pharmacogenes; everything else is skipped here.

  3. PROTEIN CHANGE (Ensembl VEP, review only)
     For the remaining variants the descriptions are free text
     ("Val158Met", "C282Y", "Factor V Leiden"), too varied to match
     mechanically. The script prints Ensembl's amino-acid changes beside
     the description so a person can compare them. This never fails the
     run; it is a worksheet, not a gate.

    python3 scripts/check_variant_reference.py          # passes 1 and 2
    python3 scripts/check_variant_reference.py --review # adds pass 3

Exit code 0 when the two gates agree, 1 on any disagreement, 2 if a
service could not be reached.

PRIVACY: this sends only the hardcoded public rs numbers in
variant_reference.py. It never opens the database and never sends
anything from anyone's records.

Network-bound, so it is NOT part of the test suite. Run it by hand after
editing the table.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from variant_reference import KNOWN_VARIANTS

ESUMMARY = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
CPIC = 'https://api.cpicpgx.org/v1/'
ENSEMBL = 'https://rest.ensembl.org/vep/human/id/'
BATCH = 20
STAR_FUNCTIONS = ('no function', 'decreased function', 'increased function',
                  'normal function', 'uncertain function', 'unknown function')


def fetch(url, timeout=40):
    request = urllib.request.Request(
        url, headers={'User-Agent': 'health-ledger-check', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def cpic(table, **params):
    return fetch(CPIC + table + '?' + urllib.parse.urlencode(params))


# --- pass 1: gene symbols, from dbSNP -----------------------------------------

def dbsnp_genes(rsids):
    """{rsid: [gene symbols]} from dbSNP."""
    found = {}
    numeric = [r[2:] for r in rsids if r.startswith('rs') and r[2:].isdigit()]
    for start in range(0, len(numeric), BATCH):
        chunk = numeric[start:start + BATCH]
        url = f'{ESUMMARY}?db=snp&retmode=json&id=' + ','.join(chunk)
        result = fetch(url).get('result', {})
        for uid in result.get('uids', []):
            found['rs' + uid] = [g.get('name') for g in result[uid].get('genes', []) if g.get('name')]
        time.sleep(0.4)
    return found


def check_genes(found):
    problems = []
    for rsid, (gene, _) in sorted(KNOWN_VARIANTS.items()):
        genes = found.get(rsid)
        if genes is None:
            problems.append(f'{rsid:13} not found in dbSNP (table says {gene})')
        elif not genes:
            problems.append(f'{rsid:13} dbSNP assigns no gene (table says {gene})')
        elif gene.upper() not in [g.upper() for g in genes]:
            problems.append(f'{rsid:13} table says {gene}, dbSNP says {", ".join(genes)}')
    return problems


# --- pass 2: star alleles and function, from CPIC -----------------------------

def claimed_star(description):
    """The leading star allele in a description, or None."""
    if not description.startswith('*'):
        return None
    token = description.split(',')[0].split()[0].split('(')[0]
    return token.strip() or None


def claimed_function(description):
    lowered = description.lower()
    for phrase in STAR_FUNCTIONS:
        if phrase in lowered:
            return phrase
    return None


def cpic_index(rsids):
    """{rsid: {'gene', 'alleles': {name: clinical function}}} for what CPIC curates."""
    locations = []
    rsids = sorted(rsids)
    for start in range(0, len(rsids), 25):
        chunk = rsids[start:start + 25]
        locations += cpic('sequence_location', dbsnpid=f'in.({",".join(chunk)})',
                          select='id,genesymbol,dbsnpid')
    if not locations:
        return {}

    location_ids = [str(l['id']) for l in locations]
    values = []
    for start in range(0, len(location_ids), 25):
        chunk = location_ids[start:start + 25]
        values += cpic('allele_location_value', locationid=f'in.({",".join(chunk)})',
                       select='locationid,allele_definition(id,name)')

    definition_ids = sorted({str(v['allele_definition']['id']) for v in values
                             if v.get('allele_definition')})
    functions = {}
    for start in range(0, len(definition_ids), 25):
        chunk = definition_ids[start:start + 25]
        for row in cpic('allele', definitionid=f'in.({",".join(chunk)})',
                        select='definitionid,name,clinicalfunctionalstatus'):
            # Keyed by definition AND name: a CYP2D6 duplication such as *2x2
            # shares its definition id with *2, so keying on the id alone lets
            # the duplication's "Increased function" overwrite *2's "Normal".
            functions[(row['definitionid'], row['name'])] = row.get('clinicalfunctionalstatus')

    names_at = {}
    for value in values:
        definition = value.get('allele_definition') or {}
        if definition.get('name'):
            names_at.setdefault(value['locationid'], {})[definition['name']] = \
                functions.get((definition['id'], definition['name']))

    index = {}
    for location in locations:
        index[location['dbsnpid']] = {'gene': location['genesymbol'],
                                      'alleles': names_at.get(location['id'], {})}
    return index


def check_stars(index):
    """Star allele must be one CPIC defines here; stated function must match CPIC's."""
    problems = []
    for rsid, (gene, description) in sorted(KNOWN_VARIANTS.items()):
        entry = index.get(rsid)
        star = claimed_star(description)
        if entry is None or star is None:
            continue
        # CPIC sometimes writes the star inside a longer name, as in
        # "c.1905+1G>A (*2A)", so match on containment rather than equality.
        matches = [name for name in entry['alleles'] if star == name or f'({star})' in name]
        if not matches:
            defined = ', '.join(sorted(entry['alleles'])) or '(none)'
            problems.append(f'{rsid:13} table claims {gene}{star}; CPIC defines: {defined}')
            continue
        stated = claimed_function(description)
        actual = entry['alleles'].get(matches[0])
        if stated and actual and stated != actual.strip().lower():
            problems.append(f'{rsid:13} table says {gene}{star} is "{stated}"; '
                            f'CPIC says "{actual}"')
    return problems


# --- pass 3: protein changes, from Ensembl (review only) ----------------------

def protein_changes(rsid):
    """Every amino-acid change Ensembl reports for this variant, across transcripts."""
    try:
        record = fetch(ENSEMBL + rsid + '?content-type=application/json')[0]
    except (urllib.error.HTTPError, urllib.error.URLError, IndexError, KeyError):
        return None
    changes = set()
    for consequence in record.get('transcript_consequences', []):
        amino = consequence.get('amino_acids')
        position = consequence.get('protein_start')
        symbol = consequence.get('gene_symbol')
        if amino and position and '/' in amino:
            before, after = amino.split('/')[:2]
            changes.add(f'{symbol} {before}{position}{after}')
    return sorted(changes)


def review(index):
    print('\nPass 3: protein changes from Ensembl, for eye comparison only.')
    print('CPIC does not cover these, so nothing here passes or fails.\n')
    for rsid, (gene, description) in sorted(KNOWN_VARIANTS.items()):
        if rsid in index and claimed_star(description):
            continue
        changes = protein_changes(rsid)
        if changes is None:
            print(f'  {rsid:12} {gene:9} {description[:44]:46} (Ensembl: no answer)')
            continue
        mine = [c for c in changes if c.startswith(gene + ' ')] or changes
        print(f'  {rsid:12} {gene:9} {description[:44]:46} {", ".join(mine[:6]) or "(no coding change)"}')
        time.sleep(0.2)


def main() -> int:
    parser = argparse.ArgumentParser(description='Check variant_reference.py against dbSNP and CPIC.')
    parser.add_argument('--review', action='store_true',
                        help='also print Ensembl protein changes for the variants CPIC does not cover')
    args = parser.parse_args()

    total = len(KNOWN_VARIANTS)
    try:
        genes = dbsnp_genes(list(KNOWN_VARIANTS))
    except Exception as e:
        print(f'Could not reach dbSNP: {e}')
        return 2
    gene_problems = check_genes(genes)
    print(f'Pass 1, gene symbols: {total - len(gene_problems)} of {total} agree with dbSNP.')
    for line in gene_problems:
        print('  ' + line)

    try:
        index = cpic_index(list(KNOWN_VARIANTS))
    except Exception as e:
        print(f'Could not reach CPIC: {e}')
        return 2
    star_problems = check_stars(index)
    claimed = sum(1 for r, (_, d) in KNOWN_VARIANTS.items() if r in index and claimed_star(d))
    print(f'Pass 2, star alleles: CPIC covers {len(index)} of {total} variants; '
          f'{claimed - len(star_problems)} of {claimed} star claims agree.')
    for line in star_problems:
        print('  ' + line)

    if args.review:
        try:
            review(index)
        except Exception as e:
            print(f'Ensembl review stopped: {e}')

    problems = gene_problems + star_problems
    if problems:
        print(f'\n{len(problems)} disagreement(s). Fix the table or the source note.')
        return 1
    print('\nBoth gates agree. Descriptions not covered by CPIC remain '
          'unverified; run with --review to compare them by eye.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
