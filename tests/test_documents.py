#!/usr/bin/env python3
"""
Documents from a person's care: read on the /import page, previewed before
anything is written, and filed with the readings they hold.
"""

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import documents
from app import app
from database_manager import GeneticProfileDB

LAB_TEXT = """Example Clinic Laboratory
Collected March 14, 2024
Specimen: blood
Reference Range
Glucose 95 mg/dL 70-99
Hemoglobin A1c 5.4 % 4.0-5.6
Cholesterol Total 240 mg/dL 100-199
"""

LOG_TEXT = """Blood Pressure
Nov 18, 2019, 8:56 AM 110/70 mmHg Clinic
Nov 20, 2019, 9:10 AM 118/76 mmHg Home
"""

LETTER_TEXT = """Example Practice
March 2, 2024

Dear colleague, thank you for seeing this patient. No further action is needed
at this time. Kind regards.
"""


class TestDocuments(unittest.TestCase):

    def setUp(self):
        self.data_root = tempfile.mkdtemp(prefix='ledger-docs-')
        self._original_root = config.DATA_ROOT
        self._original_db = config.DB_PATH
        self._original_sources = config.PRIMARY_SOURCES_DIR
        config.set_data_root(self.data_root)
        self.db = GeneticProfileDB(str(config.DB_PATH))
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        self.db.close()
        config.DATA_ROOT = self._original_root
        config.DB_PATH = self._original_db
        config.PRIMARY_SOURCES_DIR = self._original_sources

    def write(self, name, text):
        path = Path(self.data_root) / name
        path.write_text(text)
        return path

    # --- reading -----------------------------------------------------------

    def test_lab_results_are_recognised(self):
        summary = documents.read(self.write('labs.txt', LAB_TEXT))
        self.assertEqual(summary.kind, 'lab_result')
        self.assertEqual(summary.kind_label, 'Lab results')
        self.assertEqual(summary.document_date, '2024-03-14')
        self.assertEqual(summary.metric_count, 3)
        self.assertEqual(summary.abnormal_count, 1)

    def test_health_log_readings_are_not_counted_twice(self):
        summary = documents.read(self.write('log.txt', LOG_TEXT))
        self.assertEqual(summary.kind, 'health_log')
        self.assertEqual([m['metric_value_text'] for m in summary.metrics], ['110/70', '118/76'])

    def test_a_letter_is_filed_for_its_text(self):
        summary = documents.read(self.write('letter.txt', LETTER_TEXT))
        self.assertEqual(summary.metrics, [])
        self.assertIn('Dear colleague', summary.excerpt)

    def test_unreadable_kinds_are_refused(self):
        with self.assertRaises(documents.UnreadableDocument):
            documents.read(self.write('scan.heic', 'x'))

    def test_a_file_with_no_text_is_refused(self):
        with self.assertRaises(documents.UnreadableDocument):
            documents.read(self.write('blank.txt', '   \n  '))

    # --- writing -----------------------------------------------------------

    def test_a_dry_run_writes_nothing(self):
        documents.import_file(self.db, self.write('labs.txt', LAB_TEXT), dry_run=True)
        self.assertEqual(self.db.get_all_primary_sources(), [])
        self.assertEqual(self.db.get_health_metrics(), [])

    def test_importing_files_the_document_and_its_readings(self):
        summary = documents.import_file(self.db, self.write('labs.txt', LAB_TEXT))
        sources = self.db.get_all_primary_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]['source_type'], 'lab_result')
        self.assertEqual(len(self.db.get_health_metrics()), 3)
        self.assertIsNotNone(summary.source_id)

    def test_the_file_is_copied_into_the_data_folder(self):
        documents.import_file(self.db, self.write('labs.txt', LAB_TEXT))
        stored = Path(config.PRIMARY_SOURCES_DIR) / 'documents' / 'labs.txt'
        self.assertTrue(stored.is_file())

    def test_importing_the_same_file_again_replaces_it(self):
        path = self.write('labs.txt', LAB_TEXT)
        first = documents.import_file(self.db, path)
        again = documents.import_file(self.db, path)
        self.assertEqual(first.source_id, again.source_id)
        self.assertIsNotNone(again.replaces)
        self.assertEqual(len(self.db.get_all_primary_sources()), 1)
        self.assertEqual(len(self.db.get_health_metrics()), 3)

    # --- the page ----------------------------------------------------------

    def upload(self, name, text):
        return self.client.post('/import/preview', content_type='multipart/form-data',
                                data={'file': (io.BytesIO(text.encode()), name)})

    def test_the_page_previews_a_document_without_writing(self):
        response = self.upload('labs.txt', LAB_TEXT)
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('What the document holds', page)
        self.assertIn('Glucose', page)
        self.assertEqual(self.db.get_all_primary_sources(), [])

    def test_the_page_confirms_and_writes(self):
        page = self.upload('labs.txt', LAB_TEXT).get_data(as_text=True)
        token = page.split('name="token" value="', 1)[1].split('"', 1)[0]
        response = self.client.post('/import/document', data={'token': token})
        self.assertEqual(response.status_code, 302)
        self.assertIn('notice=document', response.headers['Location'])
        self.assertEqual(len(GeneticProfileDB(str(config.DB_PATH)).get_all_primary_sources()), 1)

    def test_the_page_explains_a_file_it_cannot_read(self):
        response = self.upload('holiday.heic', 'nonsense')
        self.assertEqual(response.status_code, 400)
        self.assertIn('not a kind this page reads', response.get_data(as_text=True))

    def test_dna_files_still_reach_the_dna_reader(self):
        raw = "# rsid\tchromosome\tposition\tgenotype\nrs4244285\t10\t94781859\tAG\n"
        page = self.upload('dna.txt', raw).get_data(as_text=True)
        self.assertIn('variants called', page)


if __name__ == '__main__':
    unittest.main()
