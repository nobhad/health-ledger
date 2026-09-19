#!/usr/bin/env python3
"""
Bring a consumer DNA raw-data file (23andMe, AncestryDNA, MyHeritage,
FamilyTreeDNA, Living DNA; plain, .gz or .zip) into the ledger.

    python3 scripts/import_raw_dna.py path/to/raw_data.zip --dry-run
    python3 scripts/import_raw_dna.py path/to/raw_data.zip

The Import page in the app does the same with a file picker. Every called
variant is stored in snp_genotypes; the variants in genes the ledger tracks
are listed. Nothing is written on a dry run.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import raw_dna
from database_manager import GeneticProfileDB


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='the raw-data download (.txt, .csv, .zip or .gz)')
    parser.add_argument('--dry-run', action='store_true', help='read and report, write nothing')
    parser.add_argument('--db', help='database path (default: the configured one)')
    args = parser.parse_args()

    db = GeneticProfileDB(args.db) if args.db else GeneticProfileDB()
    try:
        summary = raw_dna.import_file(db, Path(args.file), dry_run=args.dry_run)
    except raw_dna.UnreadableRawData as e:
        print(f'Cannot read {args.file}: {e}')
        return 1
    finally:
        db.close()

    print(f'{summary.provider_name} file, reference build {summary.build or "unknown"}')
    print(f'{summary.variant_count:,} variants called, {summary.no_calls:,} not called')
    if summary.in_ledger:
        print(f'Found {len(summary.in_ledger)} of your variants in '
              f'{len(summary.genes_in_ledger)} genes this ledger tracks:')
        for m in summary.in_ledger:
            print(f'  {m.gene:10} {m.rsid:12} {m.genotype:4} {m.description}')
    else:
        print('None of the well-known variants fall in genes this ledger tracks yet.')
    if summary.not_in_ledger:
        print(f'Also found {len(summary.not_in_ledger)} variants in well-known genes not in '
              f'the ledger: {", ".join(summary.genes_not_in_ledger)}')
    print('Dry run: nothing written.' if summary.dry_run else f'Written (import #{summary.import_id}).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
