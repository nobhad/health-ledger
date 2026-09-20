#!/usr/bin/env python3
"""
Documents from a person's care: read on the /import page, previewed before
anything is written, and filed with the readings they hold.
"""

import io
import os
import sys
from unittest import mock
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


class DocumentsCase(unittest.TestCase):
    """A ledger in a temporary data folder, and the helpers for feeding it files."""

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

    def upload(self, name, text):
        return self.client.post('/import/preview', content_type='multipart/form-data',
                                data={'file': (io.BytesIO(text.encode()), name)})


class TestDocuments(DocumentsCase):

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

    def test_a_file_with_no_text_is_described_not_refused(self):
        summary = documents.read(self.write('blank.txt', '   \n  '))
        self.assertFalse(summary.has_text)
        self.assertEqual(summary.text_source, documents.TEXT_FROM_NOTHING)
        self.assertEqual(summary.metrics, [])

    def test_a_file_with_no_text_can_still_be_kept(self):
        summary = documents.import_file(self.db, self.write('blank.txt', '   \n  '))
        sources = self.db.get_all_primary_sources()
        self.assertEqual(len(sources), 1)
        self.assertIsNone(sources[0]['extracted_text'])
        self.assertTrue((Path(config.PRIMARY_SOURCES_DIR) / 'documents' / 'blank.txt').is_file())
        self.assertIsNotNone(summary.source_id)

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

    def test_the_page_offers_to_keep_a_file_it_cannot_read(self):
        response = self.upload('scan.txt', '  ')
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('No text could be read', page)
        self.assertIn('Add to my ledger', page)

    def test_dna_files_still_reach_the_dna_reader(self):
        raw = "# rsid\tchromosome\tposition\tgenotype\nrs4244285\t10\t94781859\tAG\n"
        page = self.upload('dna.txt', raw).get_data(as_text=True)
        self.assertIn('variants called', page)


class TestScannedDocuments(DocumentsCase):
    """A page with no text layer: OCR when it is installed, kept either way."""

    def scanned_pdf(self, name='scan.pdf', message='Glucose 95 mg/dL 70-99'):
        """A PDF that holds a picture of text and no text layer."""
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (1200, 400), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((40, 40), 'Example Clinic Laboratory', fill='black')
        draw.text((40, 90), 'Collected March 14, 2024', fill='black')
        draw.text((40, 140), message, fill='black')
        path = Path(self.data_root) / name
        image.save(path, 'PDF', resolution=150)
        return path

    def test_a_scan_has_no_text_layer(self):
        import pdfplumber
        with pdfplumber.open(self.scanned_pdf()) as pdf:
            self.assertFalse((pdf.pages[0].extract_text() or '').strip())

    @unittest.skipUnless(documents.ocr_available(), 'OCR extras are not installed')
    def test_ocr_reads_a_scan(self):
        summary = documents.read(self.scanned_pdf())
        self.assertEqual(summary.text_source, documents.TEXT_FROM_OCR)
        self.assertTrue(summary.read_by_ocr)
        self.assertIn('Clinic', summary.excerpt)

    def test_without_ocr_a_scan_is_still_kept(self):
        with mock.patch.object(documents, 'read_by_ocr', return_value=''):
            summary = documents.import_file(self.db, self.scanned_pdf())
        self.assertEqual(summary.text_source, documents.TEXT_FROM_NOTHING)
        self.assertFalse(summary.has_text)
        self.assertEqual(len(self.db.get_all_primary_sources()), 1)
        self.assertEqual(summary.page_count, 1)


REPORT_TEXT = """Pharmacogenomic Panel Report
Collected March 14, 2024
Gene Phenotype Summary
CYP2D6 Intermediate Metabolizer
CYP2C19 Extensive (Normal) Metabolizer
HTR2A Increased Sensitivity
XYZ9 Poor Metabolizer

Use as Directed
citalopram (Celexa®)
sertraline (Zoloft®)
Moderate Gene-Drug Interaction
paroxetine (Paxil®) 6
Significant Gene-Drug Interaction
nortriptyline (Pamelor®) 7
"""


class TestReportImport(DocumentsCase):
    """A pharmacogenomic report fills the drug-metabolism tables from the page."""

    def setUp(self):
        super().setUp()
        for symbol in ('CYP2D6', 'CYP2C19', 'HTR2A'):
            self.db.add_gene(symbol, f'{symbol} gene', '1')

    def report(self, name='report.txt'):
        return self.write(name, REPORT_TEXT)

    def test_a_report_is_recognised_as_one(self):
        self.assertEqual(documents.read(self.report()).kind, 'test_report')

    def test_the_preview_lists_the_genes_and_writes_nothing(self):
        summary = documents.import_file(self.db, self.report(), dry_run=True)
        self.assertEqual(sorted(f['gene'] for f in summary.gene_findings),
                         ['CYP2C19', 'CYP2D6', 'HTR2A'])
        self.assertEqual(summary.unknown_genes, ['XYZ9'])
        self.assertEqual(summary.medication_count, 4)
        self.assertEqual(self.db.get_all_primary_sources(), [])
        self.assertIsNone(self.db.get_pharmacogenomic_data_for_gene(
            self.db.get_gene_by_symbol('CYP2D6')['id']))

    def test_confirming_fills_the_drug_metabolism_tables(self):
        summary = documents.import_file(self.db, self.report())
        record = self.db.get_pharmacogenomic_data_for_gene(
            self.db.get_gene_by_symbol('CYP2D6')['id'])
        self.assertIsNotNone(record)
        self.assertEqual(record['metabolism_status'], 'Intermediate Metabolizer')
        self.assertEqual(len(self.db.get_medication_interactions(summary.source_id)), 4)

    def test_genes_the_ledger_lacks_are_skipped_unless_asked_for(self):
        documents.import_file(self.db, self.report())
        self.assertIsNone(self.db.get_gene_by_symbol('XYZ9'))

    def test_genes_the_ledger_lacks_can_be_started(self):
        documents.import_file(self.db, self.report(), add_genes=True)
        self.assertIsNotNone(self.db.get_gene_by_symbol('XYZ9'))

    def test_importing_the_report_again_does_not_duplicate(self):
        first = documents.import_file(self.db, self.report())
        documents.import_file(self.db, self.report())
        self.assertEqual(len(self.db.get_all_primary_sources()), 1)
        self.assertEqual(len(self.db.get_medication_interactions(first.source_id)), 4)

    def test_the_page_previews_then_writes_the_findings(self):
        response = self.client.post('/import/preview', content_type='multipart/form-data',
                                    data={'file': (io.BytesIO(REPORT_TEXT.encode()), 'report.txt')})
        page = response.get_data(as_text=True)
        self.assertIn('Drug-metabolism findings', page)
        self.assertIn('Intermediate Metabolizer', page)
        self.assertIn('XYZ9', page)
        self.assertEqual(self.db.get_all_primary_sources(), [])

        token = page.split('name="token" value="', 1)[1].split('"', 1)[0]
        self.client.post('/import/document', data={'token': token, 'add_genes': '1'})
        fresh = GeneticProfileDB(str(config.DB_PATH))
        self.assertIsNotNone(fresh.get_gene_by_symbol('XYZ9'))
        self.assertIsNotNone(fresh.get_pharmacogenomic_data_for_gene(
            fresh.get_gene_by_symbol('CYP2D6')['id']))


if __name__ == '__main__':
    unittest.main()
