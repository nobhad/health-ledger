#!/usr/bin/env python3
"""
Unit tests for database_manager module
"""

import unittest
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB


class TestDatabaseManager(unittest.TestCase):
    """Test database manager operations"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = GeneticProfileDB(self.db_path)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        # Also remove WAL and SHM files
        for ext in ['.db-shm', '.db-wal']:
            path = self.db_path + ext
            if os.path.exists(path):
                os.unlink(path)
    
    def test_add_gene(self):
        """Test adding a gene"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        self.assertIsInstance(gene_id, int)
        self.assertGreater(gene_id, 0)
        
        # Verify gene was added
        gene = self.db.get_gene_by_symbol('TEST')
        self.assertIsNotNone(gene)
        self.assertEqual(gene['gene_symbol'], 'TEST')
        self.assertEqual(gene['gene_name'], 'Test Gene')
    
    def test_get_all_genes(self):
        """Test getting all genes"""
        # Add test genes
        self.db.add_gene('GENE1', 'Gene 1', '1')
        self.db.add_gene('GENE2', 'Gene 2', '2')
        
        genes = self.db.get_all_genes()
        self.assertGreaterEqual(len(genes), 2)
        symbols = [g['gene_symbol'] for g in genes]
        self.assertIn('GENE1', symbols)
        self.assertIn('GENE2', symbols)
    
    def test_get_gene_by_symbol(self):
        """Test getting gene by symbol"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        gene = self.db.get_gene_by_symbol('TEST')
        
        self.assertIsNotNone(gene)
        self.assertEqual(gene['id'], gene_id)
        self.assertEqual(gene['gene_symbol'], 'TEST')
    
    def test_get_gene_not_found(self):
        """Test getting non-existent gene"""
        gene = self.db.get_gene_by_symbol('NONEXISTENT')
        self.assertIsNone(gene)
    
    def test_add_snp(self):
        """Test adding an SNP"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        snp_id = self.db.add_snp('rs123456', gene_id)
        
        self.assertIsInstance(snp_id, int)
        self.assertGreater(snp_id, 0)
    
    def test_add_genotype(self):
        """Test adding a genotype"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        genotype_id = self.db.add_genotype(gene_id, 'A/G', 'Heterozygous')
        
        self.assertIsInstance(genotype_id, int)
        self.assertGreater(genotype_id, 0)
    
    def test_add_trait_association(self):
        """Test adding trait association"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        trait_id = self.db.add_trait_association(
            gene_id=gene_id,
            trait_name='Test Trait',
            association_direction='increased'
        )
        
        self.assertIsInstance(trait_id, int)
        self.assertGreater(trait_id, 0)
        
        # Verify trait was added
        traits = self.db.get_trait_associations_for_gene(gene_id)
        self.assertGreater(len(traits), 0)
        trait_names = [t['trait_name'] for t in traits]
        self.assertIn('Test Trait', trait_names)
    
    def test_add_health_condition_association(self):
        """Test adding health condition association"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        condition_id = self.db.add_health_condition_association(
            gene_id=gene_id,
            condition_name='Test Condition',
            association_type='risk'
        )
        
        self.assertIsInstance(condition_id, int)
        self.assertGreater(condition_id, 0)
        
        # Verify condition was added
        conditions = self.db.get_health_conditions_for_gene(gene_id)
        self.assertGreater(len(conditions), 0)
        condition_names = [c['condition_name'] for c in conditions]
        self.assertIn('Test Condition', condition_names)
    
    def test_get_genes_by_trait(self):
        """Test getting genes by trait"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        self.db.add_trait_association(gene_id, 'Test Trait', 'increased')
        
        genes = self.db.get_genes_by_trait('Test Trait')
        self.assertGreater(len(genes), 0)
        symbols = [g['gene_symbol'] for g in genes]
        self.assertIn('TEST', symbols)
    
    def test_delete_health_metrics_for_source(self):
        """Re-extraction replaces a source's metrics instead of duplicating them"""
        source_id = self.db.add_primary_source('Summary', 'health_summary')
        self.db.add_health_metric(source_id, 'temperature', '2025-01-01', metric_value=98.6, unit='F')
        self.db.add_health_metric(source_id, 'temperature', '2025-01-02', metric_value=98.4, unit='F')
        self.assertEqual(self.db.delete_health_metrics_for_source(source_id), 2)
        self.assertEqual(self.db.get_health_metrics(), [])
    
    def test_add_primary_source_finding_if_not_exists(self):
        source_id = self.db.add_primary_source('Summary', 'health_summary')
        first = self.db.add_primary_source_finding_if_not_exists(source_id, 'Vyvanse', 'medication', '2024-01-01')
        again = self.db.add_primary_source_finding_if_not_exists(source_id, 'Vyvanse', 'medication', '2024-01-01')
        self.assertIsInstance(first, int)
        self.assertIsNone(again)
        self.assertEqual(len(self.db.get_primary_source_findings(source_id)), 1)
    
    def test_category_averages_do_not_mix_units(self):
        """Temperatures in C and F are averaged separately; lab values are left out"""
        source_id = self.db.add_primary_source('Summary', 'health_summary')
        self.db.add_health_metric(source_id, 'temperature', '2025-01-01', metric_value=37.0, unit='C')
        self.db.add_health_metric(source_id, 'temperature', '2025-01-02', metric_value=98.6, unit='F')
        self.db.add_health_metric(source_id, 'lab_value', '2025-01-02', metric_value=5.4, unit='%', metric_name='A1c')
        rows = {(r['metric_type'], r['unit']): r['category_average'] for r in self.db.get_health_metrics_category_averages()}
        self.assertEqual(rows, {('temperature', 'C'): 37.0, ('temperature', 'F'): 98.6})
    
    def test_get_genes_by_condition(self):
        """Test getting genes by condition"""
        gene_id = self.db.add_gene('TEST', 'Test Gene', '1')
        self.db.add_health_condition_association(gene_id, 'Test Condition', 'risk')
        
        genes = self.db.get_genes_by_condition('Test Condition')
        self.assertGreater(len(genes), 0)
        symbols = [g['gene_symbol'] for g in genes]
        self.assertIn('TEST', symbols)


if __name__ == '__main__':
    unittest.main()

