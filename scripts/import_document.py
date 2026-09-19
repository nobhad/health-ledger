#!/usr/bin/env python3
"""
Bring a document from a person's care into the ledger, from the terminal.

The same reader the /import page uses (documents.py): a PDF or text file is
read, what it holds is printed, and only without --dry-run is anything
written. A file imported before, under the same name, is replaced.

    python3 scripts/import_document.py FILE [--dry-run]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import documents
from database_manager import GeneticProfileDB


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='the PDF or text file to read')
    parser.add_argument('--dry-run', action='store_true',
                        help='read the file and print what would be added, writing nothing')
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.is_file():
        print(f"No such file: {path}")
        return 1

    db = GeneticProfileDB()
    try:
        summary = documents.import_file(db, path, path.name, dry_run=args.dry_run)
    except documents.UnreadableDocument as e:
        print(f"That file could not be read: {e}")
        return 1
    finally:
        db.close()

    pages = f", {summary.page_count} pages" if summary.page_count else ""
    print(f"{summary.file_name}: {summary.kind_label}{pages}, "
          f"{summary.text_characters:,} characters of text")
    if summary.document_date:
        print(f"  dated {summary.document_date}")
    if summary.replaces:
        print(f"  replaces the copy imported before (source {summary.replaces['id']})")
    print(f"  {summary.metric_count} reading(s) found"
          + (f", {summary.abnormal_count} outside the stated range" if summary.abnormal_count else ""))
    for metric in summary.metrics:
        value = metric.get('metric_value_text') or metric.get('metric_value')
        unit = f" {metric['unit']}" if metric.get('unit') else ''
        flag = '  (outside the stated range)' if metric.get('is_abnormal') else ''
        print(f"    - {metric['metric_name']}: {value}{unit}  {metric.get('collection_date')}{flag}")

    if args.dry_run:
        print("\nDry run: nothing was written. Run again without --dry-run to add it.")
    else:
        print(f"\nAdded as source {summary.source_id}.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
