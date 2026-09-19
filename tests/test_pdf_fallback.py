#!/usr/bin/env python3
"""
PDFs degrade to the browser's print dialog when WeasyPrint cannot load.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import pdf_generator
from app import app
from database_manager import GeneticProfileDB


class TestPdfFallback(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        db = GeneticProfileDB(self.temp_db.name)
        db.add_gene('TEST', 'Test Gene', '1')
        db.close()
        app.config['TESTING'] = True
        self._original_db_path = config.DB_PATH
        config.DB_PATH = Path(self.temp_db.name)
        self.client = app.test_client()

    def tearDown(self):
        config.DB_PATH = self._original_db_path
        for suffix in ('', '-shm', '-wal'):
            path = self.temp_db.name + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_unavailable_reason_is_none_or_text(self):
        reason = pdf_generator.pdf_unavailable_reason()
        self.assertTrue(reason is None or isinstance(reason, str))

    def test_doctor_pdf_answers_503_with_print_url_when_weasyprint_missing(self):
        with mock.patch.object(pdf_generator, 'pdf_unavailable_reason',
                               return_value="cannot load library 'gobject-2.0-0'"):
            response = self.client.post('/api/pdf/doctor/geneticist',
                                        json={'include_stats': False})
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('printable version', data['message'])
        self.assertEqual(data['print_url'],
                         '/doctor-docs/geneticist/print?medications=1&stats=0&pharmacogenomics=1&variants=1&details=1')

    def test_unknown_specialty_still_404_when_weasyprint_missing(self):
        with mock.patch.object(pdf_generator, 'pdf_unavailable_reason',
                               return_value='missing'):
            response = self.client.get('/api/pdf/doctor/astrologer')
        self.assertEqual(response.status_code, 404)

    def test_summary_pdf_answers_503_when_weasyprint_missing(self):
        with mock.patch.object(pdf_generator, 'pdf_unavailable_reason',
                               return_value='missing'):
            response = self.client.get('/api/pdf/summary')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('print_url', response.get_json())

    def test_printable_doctor_document_needs_no_weasyprint(self):
        with mock.patch.object(pdf_generator, '_load_weasyprint', return_value=None):
            response = self.client.get('/doctor-docs/geneticist/print?stats=0')
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('window.print()', page)
        self.assertIn('href="/static/css/pdf.css"', page)
        self.assertIn('class="print-toolbar no-print"', page)

    def test_printable_document_unknown_specialty(self):
        response = self.client.get('/doctor-docs/astrologer/print')
        self.assertEqual(response.status_code, 404)

    def test_doctor_docs_page_hides_generate_button_without_weasyprint(self):
        with mock.patch.object(pdf_generator, 'pdf_unavailable_reason', return_value='missing'):
            page = self.client.get('/doctor-docs').get_data(as_text=True)
        self.assertNotIn('id="generateBtn"', page)
        self.assertIn('id="printBtn"', page)
        self.assertIn('cannot make PDF files yet', page)

    def test_doctor_docs_page_shows_both_buttons_with_weasyprint(self):
        with mock.patch.object(pdf_generator, 'pdf_unavailable_reason', return_value=None):
            page = self.client.get('/doctor-docs').get_data(as_text=True)
        self.assertIn('id="generateBtn"', page)
        self.assertIn('id="printBtn"', page)

    def test_generate_pdf_from_html_reports_failure_without_weasyprint(self):
        with mock.patch.object(pdf_generator, '_load_weasyprint', return_value=None):
            ok = pdf_generator.generate_pdf_from_html('<p>x</p>', os.path.join(
                tempfile.gettempdir(), 'health-ledger-test-never-written.pdf'))
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
