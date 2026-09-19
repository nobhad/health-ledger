#!/usr/bin/env python3
"""
Patient details: saved with the database, printed at the top of doctor documents.
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
from scripts.generate_doctor_document import (generate_doctor_document_html,
                                              format_date_of_birth)

DETAILS = {
    'full_name': 'Pat Example',
    'date_of_birth': '1980-05-14',
    'address': '1 Example Street\nExampletown, EX 00000',
    'phone': '555-0100',
    'insurance_provider': 'Example Health',
    'insurance_member_id': 'EX123',
    'insurance_group_number': 'G9',
}


class TestPatientDetails(unittest.TestCase):

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

    def test_save_and_read_back(self):
        saved = self.db.save_patient_details(dict(DETAILS, unknown='ignored', phone='  555-0100 '))
        self.assertEqual(saved, DETAILS)
        self.assertEqual(self.db.get_patient_details(), DETAILS)

    def test_blank_value_clears_a_field(self):
        self.db.save_patient_details(DETAILS)
        saved = self.db.save_patient_details(dict(DETAILS, phone=''))
        self.assertNotIn('phone', saved)
        self.assertEqual(saved['full_name'], 'Pat Example')

    def test_values_are_capped(self):
        saved = self.db.save_patient_details({'address': 'x' * 2000})
        self.assertEqual(len(saved['address']), GeneticProfileDB.PATIENT_DETAIL_MAX_LENGTH)

    def test_empty_ledger_has_no_details(self):
        self.assertEqual(self.db.get_patient_details(), {})

    def test_document_prints_details_only_when_included(self):
        self.db.save_patient_details(DETAILS)
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertIn('class="patient-details"', page)
        self.assertIn('<td>Pat Example</td>', page)
        self.assertIn('May 14, 1980', page)
        self.assertIn('Example Health &middot; EX123 &middot; G9', page)
        self.assertIn('555-0100', page)
        without = generate_doctor_document_html(self.db, 'geneticist', include_details=False)
        self.assertNotIn('Pat Example', without)
        self.assertNotIn('Insurance', without)

    def test_document_escapes_details(self):
        self.db.save_patient_details({'full_name': '<b>Pat</b>'})
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertIn('&lt;b&gt;Pat&lt;/b&gt;', page)
        self.assertNotIn('<b>Pat</b>', page)

    def test_document_without_details_and_without_sources_has_no_block(self):
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertNotIn('patient-details', page)

    def test_format_date_of_birth(self):
        self.assertEqual(format_date_of_birth('1980-05-14'), 'May 14, 1980')
        self.assertEqual(format_date_of_birth('14/05/1980'), '14/05/1980')

    def test_save_route_stores_and_redirects(self):
        response = self.client.post('/doctor-docs/details', data=DETAILS)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/doctor-docs?saved=1'))
        self.assertEqual(GeneticProfileDB(self.temp_db.name).get_patient_details(), DETAILS)

    def test_page_shows_saved_details_and_notice(self):
        self.db.save_patient_details(DETAILS)
        page = self.client.get('/doctor-docs?saved=1').get_data(as_text=True)
        self.assertIn('value="Pat Example"', page)
        self.assertIn('value="1980-05-14"', page)
        self.assertIn('Your details are saved', page)
        self.assertIn('id="includeDetails"', page)

    def test_printable_document_honours_details_flag(self):
        self.db.save_patient_details(DETAILS)
        shown = self.client.get('/doctor-docs/geneticist/print').get_data(as_text=True)
        hidden = self.client.get('/doctor-docs/geneticist/print?details=0').get_data(as_text=True)
        self.assertIn('Pat Example', shown)
        self.assertNotIn('Pat Example', hidden)


if __name__ == '__main__':
    unittest.main()
