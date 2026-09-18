"""
The repository holds the software and never the record. Every tracked text
file is scanned for the shapes private data takes (record file names, home
paths, the data folder, clinical narrative about a named person). See
scripts/check_private_data.py for the patterns.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestNoPrivateData(unittest.TestCase):

    def test_tracked_files_hold_no_private_data(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_private_data.py')],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
