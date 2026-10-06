"""
The documentation's checkable claims, checked.

Prose never fails a build, so it drifts: on 2026-10-05 the API reference
described five routes that did not exist and left out 37 of the 47 that did,
twenty-odd documents named files that were no longer in the repository, and
two quoted a test count from months before. Each of those is a claim a script
can settle, so a script settles them here, on every run.

What this covers: paths written in backticks exist; routes written in the
docs exist; every route the app serves is in the API reference; `npm run`
names a real script; nobody writes a test count down. What it cannot cover
is whether a sentence about how something works is still true. That part is
read by a person.

`docs/archive/` and `CHANGELOG.md` record the past, including files that were
deleted on purpose, so they are left out.
"""

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API_REFERENCE = ROOT / 'docs' / 'api' / 'API_REFERENCE.md'
HISTORY = ('CHANGELOG.md', 'docs/archive/')

# `path/to/file.ext` in backticks. Bare names without a slash are accepted
# when a file of that name exists anywhere in the repository.
BACKTICKED_PATH = re.compile(
    r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh|ts|js|css|html|sql|md|json|yml|yaml|bat|command|spec|txt|ps1|cjs))`')
# A route as the docs write one: /api/x, /import/preview, /doctor-docs/<specialty>/print
ROUTE = re.compile(
    r'(?<![\w./-])(/(?:api|setup|import|doctor-docs|sources|query|profile|summary|metrics|backup|references|test)'
    r'(?:/[A-Za-z0-9_<>{}:.-]+)*)')
NPM_SCRIPT = re.compile(r'npm run ([a-z][a-z0-9:-]*)')
TEST_COUNT = re.compile(r'\b\d+ (?:tests?|passed|passing)\b')
# [text](relative/path.md#heading): the link target, before any #
RELATIVE_LINK = re.compile(r'\]\(([^)#?\s]+)(?:#[^)]*)?\)')


def tracked(pattern: str):
    out = subprocess.run(['git', '-C', str(ROOT), 'ls-files', pattern],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.split('\n') if line]


def current_docs():
    return [p for p in tracked('*.md') if not p.startswith(HISTORY)]


def normalise(route: str) -> str:
    """`/api/sources/<int:source_id>` and `/api/sources/12` both become `/api/sources/<>`."""
    route = re.sub(r'<[^>]+>|\{[^}]+\}', '<>', route.rstrip('.,;:)'))
    return re.sub(r'/(?:\d+|[a-z]+_[a-z_]+|[A-Z][A-Za-z0-9]*)(?=/|$)', '/<>', route)


class TestDocsAccuracy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import app as app_module
        cls.routes = {}
        for rule in app_module.app.url_map.iter_rules():
            if rule.rule.startswith('/static'):
                continue
            cls.routes[re.sub(r'<[^>]+>', '<>', rule.rule)] = sorted(
                rule.methods - {'HEAD', 'OPTIONS'})
        cls.tracked_files = set(tracked('.'))
        cls.tracked_names = {Path(p).name for p in cls.tracked_files}
        cls.npm_scripts = set(json.loads((ROOT / 'package.json').read_text())['scripts'])
        cls.docs = {p: (ROOT / p).read_text(encoding='utf-8') for p in current_docs()}

    def test_every_path_in_backticks_exists(self):
        missing = []
        for doc, text in self.docs.items():
            for path in BACKTICKED_PATH.findall(text):
                if '*' in path:
                    continue
                here = ROOT / path
                beside = ROOT / Path(doc).parent / path
                if here.exists() or beside.exists():
                    continue
                if '/' not in path and path in self.tracked_names:
                    continue
                missing.append(f'{doc}: `{path}`')
        self.assertEqual(sorted(set(missing)), [], '\n'.join(
            ['documents name files that are not in the repository:'] + sorted(set(missing))))

    def test_every_relative_link_points_at_a_tracked_file(self):
        """A link to a git-ignored or deleted file works here and 404s for everyone else."""
        broken = []
        for doc, text in self.docs.items():
            for target in RELATIVE_LINK.findall(text):
                if target.startswith(('http://', 'https://', 'mailto:', '/')):
                    continue
                if '.' not in target and '/' not in target:
                    continue  # placeholder text in a template, not a link
                normalised = os.path.normpath(os.path.join(os.path.dirname(doc), target))
                if normalised not in self.tracked_files and not (ROOT / normalised).is_dir():
                    broken.append(f'{doc}: ({target})')
        self.assertEqual(sorted(set(broken)), [], '\n'.join(
            ['links to files that are not in the repository:'] + sorted(set(broken))))

    def test_every_route_in_the_docs_exists(self):
        unknown = []
        for doc, text in self.docs.items():
            for route in ROUTE.findall(text):
                if normalise(route) in self.routes or route in self.routes:
                    continue
                unknown.append(f'{doc}: {route}')
        self.assertEqual(sorted(set(unknown)), [], '\n'.join(
            ['documents describe routes the app does not serve:'] + sorted(set(unknown))))

    def test_every_route_the_app_serves_is_in_the_api_reference(self):
        reference = API_REFERENCE.read_text(encoding='utf-8')
        absent = []
        for route, methods in sorted(self.routes.items()):
            pattern = re.escape(route).replace(r'<>', r'[^/\s`]+')
            if not re.search(pattern, reference):
                absent.append(f'{",".join(methods)} {route}')
        self.assertEqual(absent, [], '\n'.join(
            [f'routes missing from {API_REFERENCE.relative_to(ROOT)}:'] + absent))

    def test_every_npm_run_names_a_script(self):
        unknown = sorted({f'{doc}: npm run {name}' for doc, text in self.docs.items()
                          for name in NPM_SCRIPT.findall(text) if name not in self.npm_scripts})
        self.assertEqual(unknown, [], '\n'.join(['`npm run` of scripts package.json does not have:'] + unknown))

    def test_nobody_writes_a_test_count_down(self):
        counted = sorted({f'{doc}: "{m}"' for doc, text in self.docs.items()
                          for m in TEST_COUNT.findall(text)})
        self.assertEqual(counted, [], '\n'.join(
            ['a test count in prose is stale by the next commit; say how to run them instead:']
            + counted))


if __name__ == '__main__':
    unittest.main()
