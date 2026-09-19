#!/usr/bin/env python3
"""
The person's own genotypes, shown where they are useful: on the gene pages
(`/api/gene-info`) and in the doctor documents.
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
from variant_reference import VARIANT_CAUTION
from scripts.generate_doctor_document import generate_doctor_document_html

# Three variants the ledger knows (see variant_reference.KNOWN_VARIANTS) and
# one it does not. Genotypes are made up; no real file is involved.
CALLED = [
    ('rs4244285', '10', '94781859', 'AG'),      # CYP2C19 *2
    ('rs12248560', '10', '94761900', 'CC'),     # CYP2C19 *17
    ('rs3892097', '22', '42126611', 'GG'),      # CYP2D6 *4
    ('rs99999999', '1', '1', 'AA'),             # not in the reference table
]


class TestVariantGenotypes(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = GeneticProfileDB(self.temp_db.name)
        self.db.add_gene('CYP2C19', 'Cytochrome P450 2C19', '10')
        self.db.add_gene('CYP2D6', 'Cytochrome P450 2D6', '22')
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

    def import_genotypes(self, rows=CALLED):
        import_id = self.db.add_dna_import('example.txt', 'Example', 'GRCh37',
                                           len(rows), 0, 3)
        self.db.replace_snp_genotypes(import_id, rows)

    def test_lookup_pairs_the_file_with_the_reference(self):
        self.import_genotypes()
        variants = self.db.get_variant_genotypes_for_gene('CYP2C19')
        self.assertEqual([v['rsid'] for v in variants], ['rs4244285', 'rs12248560'])
        self.assertEqual(variants[0]['genotype'], 'AG')
        self.assertIn('*2', variants[0]['description'])

    def test_lookup_takes_the_symbol_in_any_case(self):
        self.import_genotypes()
        self.assertEqual(self.db.get_variant_genotypes_for_gene('cyp2c19'),
                         self.db.get_variant_genotypes_for_gene('CYP2C19'))

    def test_variants_the_file_did_not_call_are_left_out(self):
        self.import_genotypes()
        # rs4986893 (*3) is in the reference for CYP2C19 but not in this file.
        self.assertNotIn('rs4986893',
                         [v['rsid'] for v in self.db.get_variant_genotypes_for_gene('CYP2C19')])

    def test_no_import_means_no_variants(self):
        self.assertEqual(self.db.get_variant_genotypes_for_gene('CYP2C19'), [])

    def test_gene_the_reference_does_not_cover(self):
        self.import_genotypes()
        self.assertEqual(self.db.get_variant_genotypes_for_gene('NOTAGENE'), [])

    def test_gene_page_lists_them(self):
        self.import_genotypes()
        response = self.client.get('/api/gene-info?gene=CYP2C19')
        self.assertEqual(response.status_code, 200)
        variants = response.get_json()['variants']
        self.assertEqual([v['rsid'] for v in variants], ['rs4244285', 'rs12248560'])

    def test_gene_page_without_an_import(self):
        response = self.client.get('/api/gene-info?gene=CYP2C19')
        self.assertEqual(response.get_json()['variants'], [])

    def test_doctor_document_shows_them(self):
        self.import_genotypes()
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertIn('Variants in your DNA file', page)
        self.assertIn('rs4244285', page)
        self.assertIn('AG', page)

    def test_doctor_document_cautions_once(self):
        self.import_genotypes()
        page = generate_doctor_document_html(self.db, 'geneticist')
        # Two genes carry variants; the caution is printed under the first.
        self.assertEqual(page.count('Variants in your DNA file'), 2)
        self.assertEqual(page.count(VARIANT_CAUTION), 1)

    def test_doctor_document_can_leave_them_out(self):
        self.import_genotypes()
        page = generate_doctor_document_html(self.db, 'geneticist', include_variants=False)
        self.assertNotIn('Variants in your DNA file', page)
        self.assertNotIn('rs4244285', page)

    def test_doctor_document_without_an_import(self):
        page = generate_doctor_document_html(self.db, 'geneticist')
        self.assertNotIn('Variants in your DNA file', page)

    def test_printable_document_honours_the_flag(self):
        self.import_genotypes()
        with_variants = self.client.get('/doctor-docs/geneticist/print')
        self.assertIn(b'rs4244285', with_variants.data)
        without = self.client.get('/doctor-docs/geneticist/print?variants=0')
        self.assertNotIn(b'rs4244285', without.data)


if __name__ == '__main__':
    unittest.main()
