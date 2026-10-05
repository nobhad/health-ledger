"""
The References page: what the server sends, and the rules its script keeps.

Nothing here touches the network. The page's own behaviour (selection, buttons)
lives in static/js/references.ts and is checked in a browser, not here.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config  # noqa: E402
from app import app  # noqa: E402
from database_manager import GeneticProfileDB  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE = PROJECT_ROOT / 'templates' / 'references.html'
SCRIPT_TS = PROJECT_ROOT / 'static' / 'js' / 'references.ts'
SCRIPT_JS = PROJECT_ROOT / 'static' / 'js' / 'references.js'

LOOKUP_SENTENCE = ('Pressing Look up sends only these words to Europe PMC, a public index of '
                   'journal articles. Nothing from your records is sent.')
PANEL_HEADERS = ('Find articles', 'Article', 'Your excerpts')


class ReferencesPageTestCase(unittest.TestCase):

    def setUp(self):
        self._original_root = config.DATA_ROOT
        self._original_db_path = config.DB_PATH
        self.root = tempfile.mkdtemp()
        config.set_data_root(self.root)
        self.db_path = os.path.join(self.root, 'test.db')
        GeneticProfileDB(self.db_path).close()
        config.DB_PATH = Path(self.db_path)
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        config.set_data_root(self._original_root)
        config.DB_PATH = self._original_db_path
        shutil.rmtree(self.root, ignore_errors=True)

    def page(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_page_says_what_look_up_sends(self):
        self.assertIn(LOOKUP_SENTENCE, self.page('/references'))

    def test_page_has_three_panel_headers(self):
        html = self.page('/references')
        for header in PANEL_HEADERS:
            self.assertIn(f'<div class="panel-header">{header}</div>', html)

    def test_page_loads_its_script(self):
        self.assertIn('js/references.js', self.page('/references'))

    def test_sidebar_marks_references_active(self):
        html = self.page('/references')
        self.assertRegex(html, r'<a href="/references" class="nav-btn is-active"')

    def test_sidebar_links_references_from_other_pages(self):
        html = self.page('/sources')
        self.assertIn('href="/references"', html)
        self.assertNotRegex(html, r'<a href="/references" class="nav-btn is-active"')

    def test_doctor_docs_offers_journal_excerpts(self):
        self.assertIn('id="includeReferences"', self.page('/doctor-docs'))

    def test_template_has_no_inline_style(self):
        self.assertNotIn('style=', TEMPLATE.read_text())

    def test_script_is_compiled_and_builds_no_html_strings(self):
        self.assertTrue(SCRIPT_JS.is_file())
        source = SCRIPT_TS.read_text()
        for forbidden in ('innerHTML', 'confirm(', 'alert('):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()


class TestSharedPanels(unittest.TestCase):
    """Sources and References resize their panels with one script, not a copy each."""

    def test_both_pages_load_the_shared_script_and_name_their_state(self):
        for template, state in (('sources.html', 'sourcesPanel'),
                                ('references.html', 'referencesPanel')):
            page = (PROJECT_ROOT / 'templates' / template).read_text(encoding='utf-8')
            self.assertIn("filename='js/panels.js'", page, template)
            self.assertIn(f'data-panel-state="{state}"', page, template)
            self.assertEqual(page.count('class="panel-splitter"'), 2, template)

    def test_the_page_scripts_do_not_carry_their_own_copy(self):
        for script in ('sources.ts', 'references.ts'):
            source = (PROJECT_ROOT / 'static' / 'js' / script).read_text(encoding='utf-8')
            self.assertNotIn('mousedown', source, script)
        self.assertTrue((PROJECT_ROOT / 'static' / 'js' / 'panels.js').is_file())
