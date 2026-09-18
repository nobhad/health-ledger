#!/usr/bin/env python3
"""
Refuse private data in tracked files.

Health Ledger holds one person's medical records, and the repository must
never hold any of them: no record file names, no home paths, no results, no
profile text. This scans text files for the shapes that data takes and exits
non-zero naming every hit. Run it on the whole tree (default: every file git
tracks), on the staged files (--staged, what the pre-commit hook does), or on
explicit paths.

    python3 scripts/check_private_data.py
    python3 scripts/check_private_data.py --staged
    python3 scripts/check_private_data.py path/to/file.md

The patterns are deliberately generic: a real-name file prefix, a user's home
directory, the private data folder, a results-style line, a "Re: <name>"
letter header. Add a pattern when a new shape slips through; never weaken one
to make a commit pass.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    # A record file named LastFirst_TestType_Institution_YYYY-MM-DD(.ext)
    (re.compile(r'\b[A-Z][a-z]+[A-Z][a-z]+_[A-Za-z]+_[A-Za-z-]+_\d{4}-\d{2}-\d{2}'), 'record file name'),
    # A home directory path, macOS or Linux
    (re.compile(r'/(?:Users|home)/[A-Za-z0-9._-]+/'), 'home directory path'),
    # The private data folder, wherever it is
    (re.compile(r'Documents/Personal|health-ledger-private'), 'private data folder'),
    # A letter header naming the patient
    (re.compile(r'^\s*Re:\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', re.M), 'letter addressed to a named person'),
    # Clinical narrative about a named person
    (re.compile(r'\bM(?:s|r|rs)\.\s+[A-Z][a-z]+\s+(?:has|was|is|had|reports|denies)\b'), 'narrative about a named person'),
    # A date of birth — unless it belongs to the placeholder "Patient" a
    # fixture uses, which is nobody.
    (re.compile(r'(?<!Patient \| )\b(?:DOB|Date of Birth)\s*[:=]\s*\d'), 'date of birth'),
    # An MRN or patient identifier
    (re.compile(r'\b(?:MRN|Medical Record Number)\s*[:#]\s*\d'), 'medical record number'),
]

# Files the scan never reads: binaries, vendored bundles, the lockfile.
SKIP_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.tif', '.tiff',
                 '.woff', '.woff2', '.ttf', '.otf', '.db', '.pyc', '.zip', '.gz'}
SKIP_PARTS = {'node_modules', 'venv', '.git', '__pycache__'}
SKIP_FILES = {'package-lock.json'}


def git_files(staged: bool) -> list:
    cmd = ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'] if staged else ['git', 'ls-files']
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def scan(rel: str) -> list:
    path = ROOT / rel
    if (not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES
            or path.name in SKIP_FILES or SKIP_PARTS & set(path.parts)):
        return []
    # This file must be allowed to describe the patterns it looks for.
    if path.resolve() == Path(__file__).resolve():
        return []
    try:
        text = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return []
    hits = []
    for pattern, label in PATTERNS:
        for m in pattern.finditer(text):
            line = text.count('\n', 0, m.start()) + 1
            hits.append(f'{rel}:{line}: {label}: {m.group(0).strip()[:60]}')
    return hits


def main(argv: list) -> int:
    if '--staged' in argv:
        files = git_files(staged=True)
    elif len(argv) > 1:
        files = argv[1:]
    else:
        files = git_files(staged=False)
    hits = [h for f in files for h in scan(f)]
    if hits:
        print('Private data must not be committed. Move it under HEALTH_LEDGER_DATA_DIR and use placeholders:')
        for h in hits:
            print('  ' + h)
        return 1
    print(f'check_private_data: {len(files)} files clean')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
