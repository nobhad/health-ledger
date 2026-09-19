#!/usr/bin/env python3
"""
Every generated document carries the same disclaimer the screen shows.

The web app shows it in templates/footer.html on each page; a document handed
to a doctor is the copy that leaves the app, so it has to say the same thing.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from app import app
from database_manager import GeneticProfileDB
from pdf_generator import wrap_pdf_document
from scripts.generate_doctor_document import generate_doctor_document_html

REPO = Path(__file__).parent.parent


class TestDocumentDisclaimer(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = GeneticProfileDB(self.temp_db.name)
        self.db.add_gene('TEST', 'Test Gene', '1')
        app.config['TESTING'] = True
        self._original_db_path = config.DB_PATH
        config.DB_PATH = Path(self.temp_db.name)
        self.client = app.test_client()

    def tearDown(self):
        self.db.close()
        config.DB_PATH = self._original_db_path
        for suffix in ('', '-shm', '-wal'):
            path = self.temp_db.name + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_screen_and_documents_use_the_same_wording(self):
        """If the footer text is reworded, the constant has to move with it."""
        footer = (REPO / 'templates' / 'footer.html').read_text()
        self.assertIn(config.DOCUMENT_DISCLAIMER, footer)

    def test_summary_profile_and_source_wrapper(self):
        page = wrap_pdf_document('A Title', '<p>body</p>')
        self.assertIn(config.DOCUMENT_DISCLAIMER, page)
        self.assertIn('class="footer-disclaimer"', page)
        # inside the document body, not after it
        self.assertLess(page.index(config.DOCUMENT_DISCLAIMER), page.index('</body>'))

    def test_doctor_document(self):
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertIn(config.DOCUMENT_DISCLAIMER, page)
        self.assertIn('class="footer-disclaimer"', page)
        self.assertLess(page.index(config.DOCUMENT_DISCLAIMER), page.index('</body>'))

    def test_printable_web_version_keeps_it_when_printed(self):
        page = self.client.get('/doctor-docs/geneticist/print').get_data(as_text=True)
        self.assertIn(config.DOCUMENT_DISCLAIMER, page)
        # The print toolbar is hidden on paper (.no-print); the disclaimer is not.
        disclaimer_tag = page[page.index('footer-disclaimer') - 40:page.index('footer-disclaimer') + 40]
        self.assertNotIn('no-print', disclaimer_tag)

    def test_present_even_with_every_section_switched_off(self):
        page = generate_doctor_document_html(
            self.db, 'geneticist', include_medications=False, include_stats=False,
            include_pharmacogenomics=False, include_details=False)
        self.assertIn(config.DOCUMENT_DISCLAIMER, page)


if __name__ == '__main__':
    unittest.main()
