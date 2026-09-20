"""
The design system under `static/css/design-system/` is a VENDORED copy of the
no-bhad-codes token layer, pulled by `scripts/sync_design_system.sh` and pinned
by commit in `VENDORED.md`. None of it is hand-maintained.

Two things can go wrong with that arrangement, and CSS reports neither. An
unknown custom property is not an error: the browser resolves it to nothing and
carries on, so the page just renders wrong and nobody finds out by running the
app.

  1. Somebody edits a vendored file in place. It works, it survives review, and
     the next sync silently reverts it.
  2. Upstream renames or drops a token this project reads. Upstream cannot
     notice — from inside no-bhad-codes the rename is clean, and its own tests
     approve it. This project reads 159 of those names.

`test_vendored_files_match_the_pinned_commit` catches the first by rebuilding
every vendored file from the commit VENDORED.md names.
`test_no_dangling_token_references` catches the second, and needs nothing but
this repository.

Lagging behind upstream is NOT a failure here. The pin is deliberate: a sync
takes whatever upstream has changed, which can include values tuned for a
surface this project does not have. Run `npm run sync:design-system` when you
mean to, and look at what moved.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / 'static' / 'css'
VENDORED = CSS / 'design-system'
SYNC_SCRIPT = ROOT / 'scripts' / 'sync_design_system.sh'

# Same default as the sync script.
UPSTREAM = Path(os.environ.get(
    'NO_BHAD_CODES_DIR',
    Path.home() / 'Projects' / 'Development' / 'Active' / 'no-bhad-codes'))

# Where each vendored file comes from upstream. Files under tokens/ are mapped
# by name; these are the ones that move between directories on the way over.
SOURCE_OF = {
    'index.css': 'src/design-system/index.css',
    'layer-order.css': 'src/styles/core/layer-order.css',
    'reset.css': 'src/styles/base/reset.css',
    'fonts.css': 'src/styles/base/fonts.css',
}
TOKENS_SOURCE_DIR = 'src/design-system/tokens'

# The patches the sync script applies on copy, keyed by vendored path.
# test_declared_patches_match_the_sync_script keeps this list honest.
PATCHES = {
    'fonts.css': [('url("/fonts/', 'url("/static/fonts/')],
    'tokens/portal-theme.css': [('data-page="client"', 'data-page="ledger"')],
    'tokens/buttons.css': [('data-page="client"', 'data-page="ledger"')],
}

DEFINITION = re.compile(r'^\s*(--[A-Za-z0-9-]+)\s*:', re.MULTILINE)
REFERENCE = re.compile(r'var\(\s*(--[A-Za-z0-9-]+)')

# `s<delim>find<delim>replace<delim>g` plus the files it is applied to.
SED_CALL = re.compile(
    r"sed\s+-i\s+''\s+'s(?P<delim>.)(?P<find>.+?)(?P=delim)"
    r"(?P<replace>.*?)(?P=delim)g'(?P<targets>[^\n]*)")
SED_TARGET = re.compile(r'\$DST/([^"\s]+)')


def css_sources():
    """Every stylesheet this project maintains or vendors, minus the build output."""
    return [p for p in CSS.rglob('*.css') if 'dist' not in p.parts]


def pinned_revision():
    text = (VENDORED / 'VENDORED.md').read_text()
    match = re.search(r'at commit ([0-9a-f]{7,40})', text)
    assert match, 'VENDORED.md does not name a commit'
    return match.group(1)


def upstream_available(rev):
    if not (UPSTREAM / '.git').exists():
        return False
    return subprocess.run(['git', '-C', str(UPSTREAM), 'cat-file', '-e', rev + '^{commit}'],
                          capture_output=True).returncode == 0


class TestVendoredDesignSystem(unittest.TestCase):

    def test_no_dangling_token_references(self):
        """Every var(--token) resolves to a token something defines."""
        defined = set()
        for path in css_sources():
            defined.update(DEFINITION.findall(path.read_text()))

        readers = css_sources() + sorted(ROOT.glob('templates/**/*.html'))
        readers += [p for p in ROOT.glob('static/js/**/*.js') if 'vendor' not in p.parts]

        dangling = {}
        for path in readers:
            for name in REFERENCE.findall(path.read_text()):
                if name not in defined:
                    dangling.setdefault(name, set()).add(
                        str(path.relative_to(ROOT)))

        self.assertEqual(dangling, {}, '\n'.join(
            ['tokens read but never defined — an upstream rename lands here:']
            + [f'  {name}  <- {", ".join(sorted(files))}'
               for name, files in sorted(dangling.items())]))

    def test_vendored_files_match_the_pinned_commit(self):
        """Nothing under design-system/ has been hand-edited since the sync."""
        rev = pinned_revision()
        if not upstream_available(rev):
            self.skipTest(f'no-bhad-codes not available at {UPSTREAM} (or {rev} unknown)')

        sources = dict(SOURCE_OF)
        for path in sorted((VENDORED / 'tokens').glob('*.css')):
            sources[f'tokens/{path.name}'] = f'{TOKENS_SOURCE_DIR}/{path.name}'

        present = {str(p.relative_to(VENDORED)) for p in VENDORED.rglob('*.css')}
        self.assertEqual(present, set(sources), 'vendored file set does not match the map')

        edited = []
        for vendored_path, source_path in sorted(sources.items()):
            expected = subprocess.run(
                ['git', '-C', str(UPSTREAM), 'show', f'{rev}:{source_path}'],
                capture_output=True, text=True, check=True).stdout
            for find, replace in PATCHES.get(vendored_path, []):
                expected = expected.replace(find, replace)
            if (VENDORED / vendored_path).read_text() != expected:
                edited.append(vendored_path)

        self.assertEqual(edited, [], (
            f'vendored files differ from {rev}, which VENDORED.md says they came '
            f'from: {", ".join(edited)}. Change it upstream and re-sync; a hand '
            f'edit here is reverted by the next sync.'))

    def test_declared_patches_match_the_sync_script(self):
        """PATCHES above is what the script really does, not what it used to do."""
        script = SYNC_SCRIPT.read_text()
        actual = {}
        for call in SED_CALL.finditer(script):
            for target in SED_TARGET.findall(call.group('targets')):
                actual.setdefault(target, []).append(
                    (call.group('find'), call.group('replace')))

        self.assertEqual(actual, {k: v for k, v in PATCHES.items()}, (
            'the sync script patches different files than this test replicates, '
            'so test_vendored_files_match_the_pinned_commit is comparing against '
            'the wrong content. Update PATCHES.'))


if __name__ == '__main__':
    unittest.main()
