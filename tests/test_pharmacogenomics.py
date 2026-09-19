#!/usr/bin/env python3
"""
scripts/import_pharmacogenomics.py: reading a panel report's phenotypes and
medication categories, writing them idempotently, and the doctor document's
optional drug section. The report text here is made up.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB
from scripts import import_pharmacogenomics as imp
from scripts.generate_doctor_document import generate_doctor_document_html, medication_guidance_html
from pharmacogenomic_reference import drugs_for_gene, GENE_DRUGS

REPORT = """
Pharmacogenomic Panel Report
Gene Phenotype Summary
CYP2D6 Intermediate Metabolizer CYP2C19 Extensive (Normal) Metabolizer
HLA-B*1502 Normal Risk
HTR2A Increased Sensitivity
XYZ9 Poor Metabolizer
CYP2D6 Intermediate Metabolizer is repeated further down the report.

Use as Directed
Gene-drug Interaction Gene-drug Interaction
amitriptyline (Elavil®) paroxetine (Paxil®) 6
bupropion (Wellbutrin®)

Gene-drug Interactions
Use as Directed
citalopram (Celexa®)
sertraline (Zoloft®)
Use as Directed (Continued)
escitalopram (Lexapro®)
Moderate Gene-Drug Interaction
paroxetine (Paxil®) 6
venlafaxine (Effexor®) 1, 6
Significant Gene-Drug Interaction
nortriptyline (Pamelor®) 7
Clinical Considerations
6: Use of this drug may increase risk of side effects.
"""


class PharmacogenomicsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmp.close()
        self.db = GeneticProfileDB(self.tmp.name)
        self.gene_ids = {}
        for symbol in ('CYP2D6', 'CYP2C19', 'HLA-B', 'HTR2A', 'COMT'):
            self.gene_ids[symbol] = self.db.add_gene(symbol, f'{symbol} gene', '1')
        self.db.add_genotype(self.gene_ids['CYP2D6'], '*1/*4')
        self.db.add_genotype(self.gene_ids['CYP2D6'], '*1/*4 (Heterozygous)')
        self.source_id = self.db.add_primary_source(
            'Panel report', 'test_report', document_date='2025-01-01',
            institution='Lab', extracted_text=REPORT)

    def tearDown(self):
        self.db.close()
        for ext in ('', '-wal', '-shm'):
            path = self.tmp.name + ext
            if os.path.exists(path):
                os.unlink(path)


class TestParsing(unittest.TestCase):
    def test_phenotypes_first_statement_wins_and_allele_is_kept(self):
        found = imp.parse_phenotypes(REPORT)
        self.assertEqual(found['CYP2D6'], {'phenotype': 'Intermediate Metabolizer', 'allele': None})
        self.assertEqual(found['CYP2C19']['phenotype'], 'Extensive (Normal) Metabolizer')
        self.assertEqual(found['HLA-B'], {'phenotype': 'Normal Risk', 'allele': '*1502'})
        self.assertEqual(found['HTR2A']['phenotype'], 'Increased Sensitivity')
        self.assertIn('XYZ9', found)

    def test_medication_categories(self):
        items = {i['drug_name']: i for i in imp.parse_medication_categories(REPORT)}
        # The collapsed two-column row and the row after a non-canonical
        # heading are not assigned.
        self.assertNotIn('amitriptyline', items)
        self.assertNotIn('bupropion', items)
        self.assertEqual(items['citalopram']['category'], 'use_as_directed')
        self.assertEqual(items['escitalopram']['category'], 'use_as_directed')
        self.assertEqual(items['paroxetine']['category'], 'moderate')
        self.assertEqual(items['paroxetine']['notes'], '6')
        self.assertEqual(items['venlafaxine']['notes'], '1, 6')
        self.assertEqual(items['nortriptyline'], {
            'drug_name': 'nortriptyline', 'brand_name': 'Pamelor', 'category': 'significant', 'notes': '7'})
        self.assertEqual([i['drug_name'] for i in imp.parse_medication_categories(REPORT)][:3],
                         ['nortriptyline', 'paroxetine', 'venlafaxine'])

    def test_page_furniture_keeps_the_list_open(self):
        text = ("Use as Directed\nCYP2D6 CYP2C19 CYP2C9\nNormal Normal Normal\nAntidepressants\n"
                "sertraline (Zoloft®)\n3\nStimulants\nmethylphenidate (Ritalin®)\n"
                "Use of this drug may increase risk. See page 4.\nfluoxetine (Prozac®)\n")
        items = {i['drug_name']: i['category'] for i in imp.parse_medication_categories(text)}
        self.assertEqual(items, {'sertraline': 'use_as_directed', 'methylphenidate': 'use_as_directed'})

    def test_most_significant_category_wins(self):
        text = "Use as Directed\nsertraline (Zoloft®)\nSignificant Gene-Drug Interaction\nsertraline (Zoloft®) 2\n"
        items = imp.parse_medication_categories(text)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['category'], 'significant')

    def test_reference_lists_are_lowercase_generic_names(self):
        for gene, entry in GENE_DRUGS.items():
            self.assertIn(entry['evidence'], ('guideline', 'substrate', 'limited'), gene)
            for drug in entry['drugs']:
                self.assertEqual(drug, drug.lower(), (gene, drug))
        self.assertIn('warfarin', drugs_for_gene('cyp2c9'))
        self.assertEqual(drugs_for_gene('NOPE'), [])


class TestImport(PharmacogenomicsCase):
    def test_plan_pairs_genotype_reference_and_reports_unknown_genes(self):
        genes, meds, unknown = imp.plan_import(self.db, imp.test_report_sources(self.db))
        by_gene = {g['gene']: g for g in genes}
        self.assertEqual(sorted(by_gene), ['CYP2C19', 'CYP2D6', 'HLA-B', 'HTR2A'])
        self.assertEqual(by_gene['CYP2D6']['genotype_phenotype'], '*1/*4 (Heterozygous) — Intermediate Metabolizer')
        self.assertEqual(by_gene['HLA-B']['genotype_phenotype'], 'HLA-B*1502 — Normal Risk')
        self.assertIn('codeine', by_gene['CYP2D6']['drugs'])
        self.assertEqual(unknown, ['XYZ9'])
        self.assertEqual(len(meds), 1)
        self.assertEqual(meds[0]['source']['id'], self.source_id)

    def test_override_adds_a_phenotype(self):
        genes, _, _ = imp.plan_import(self.db, imp.test_report_sources(self.db), {'comt': 'Normal Activity'})
        comt = next(g for g in genes if g['gene'] == 'COMT')
        self.assertEqual(comt['metabolism_status'], 'Normal Activity')
        self.assertEqual(comt['genotype_phenotype'], 'Normal Activity')

    def test_apply_is_idempotent(self):
        sources = imp.test_report_sources(self.db)
        for _ in range(2):
            genes, meds, _ = imp.plan_import(self.db, sources)
            imp.apply_import(self.db, genes, meds)
        cursor = self.db.conn.cursor()
        self.assertEqual(cursor.execute('SELECT COUNT(*) FROM pharmacogenomic_data').fetchone()[0], 4)
        pg = self.db.get_pharmacogenomic_data_for_gene(self.gene_ids['CYP2D6'])
        self.assertEqual(pg['metabolism_status'], 'Intermediate Metabolizer')
        self.assertEqual(len(pg['affected_medications']), len(drugs_for_gene('CYP2D6')))
        rows = self.db.get_medication_interactions()
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['drug_name'], 'nortriptyline')

    def test_add_missing_genes(self):
        genes, meds, unknown = imp.plan_import(self.db, imp.test_report_sources(self.db), add_missing_genes=True)
        self.assertEqual(unknown, [])
        new = next(g for g in genes if g['gene'] == 'XYZ9')
        self.assertIsNone(new['gene_id'])
        imp.apply_import(self.db, genes, meds)
        self.assertIsNotNone(self.db.get_gene_by_symbol('XYZ9'))
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM pharmacogenomic_data').fetchone()[0], 5)

    def test_dry_run_writes_nothing(self):
        code = imp.main(['--db', self.tmp.name, '--dry-run'])
        self.assertEqual(code, 0)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM pharmacogenomic_data').fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM medication_interactions').fetchone()[0], 0)

    def test_main_writes_and_set_override(self):
        code = imp.main(['--db', self.tmp.name, '--set', 'COMT=Normal Activity'])
        self.assertEqual(code, 0)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM pharmacogenomic_data').fetchone()[0], 5)


class TestDoctorDocument(PharmacogenomicsCase):
    def setUp(self):
        super().setUp()
        genes, meds, _ = imp.plan_import(self.db, imp.test_report_sources(self.db))
        imp.apply_import(self.db, genes, meds)

    def test_drug_section_is_optional(self):
        with_drugs = generate_doctor_document_html(self.db, 'psychiatrist')
        self.assertIn('Pharmacogenomic Information', with_drugs)
        self.assertIn('Medication Guidance from the Genetic Test Report', with_drugs)
        self.assertIn('Significant gene-drug interaction (1)', with_drugs)
        self.assertIn('nortriptyline (Pamelor)', with_drugs)
        without = generate_doctor_document_html(self.db, 'psychiatrist', include_pharmacogenomics=False)
        self.assertNotIn('Pharmacogenomic Information', without)
        self.assertNotIn('Medication Guidance', without)

    def test_guidance_absent_when_nothing_imported(self):
        self.db.replace_medication_interactions_for_source(self.source_id, [])
        self.assertEqual(medication_guidance_html(self.db), [])


if __name__ == '__main__':
    unittest.main()
