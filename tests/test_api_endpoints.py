#!/usr/bin/env python3
"""
Integration tests for API endpoints
"""

import unittest
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from app import app
from database_manager import GeneticProfileDB


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        """Set up test client and database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Set up test database with sample data
        # Note: Database manager will create pharmacogenomic tables automatically
        db = GeneticProfileDB(self.db_path)
        self.test_gene_id = db.add_gene('TEST', 'Test Gene', '1')
        db.add_trait_association(self.test_gene_id, 'Test Trait', 'increased')
        db.add_health_condition_association(self.test_gene_id, 'Test Condition', 'risk')
        db.close()
        
        # Configure Flask app for testing. Each request opens its connection
        # from config.DB_PATH, so pointing that at the temp database isolates
        # the tests from the real records.
        app.config['TESTING'] = True
        self._original_db_path = config.DB_PATH
        config.DB_PATH = Path(self.db_path)
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up test database"""
        config.DB_PATH = self._original_db_path
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        for ext in ['.db-shm', '.db-wal']:
            path = self.db_path + ext
            if os.path.exists(path):
                os.unlink(path)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/test')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
    
    def test_all_genes_endpoint(self):
        """Test /api/all-genes endpoint"""
        response = self.client.get('/api/all-genes')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual([g['gene_symbol'] for g in data], ['TEST'])
    
    def test_no_cross_origin_access(self):
        """The API must not be readable cross-origin (privacy: localhost app)"""
        response = self.client.get('/api/all-genes', headers={'Origin': 'https://evil.example'})
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
    
    def test_genes_by_trait_rejects_markup(self):
        """Trait names go through the same validation as condition names"""
        response = self.client.get('/api/genes-by-trait?trait=<script>')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())
    
    def test_genes_by_trait_found(self):
        response = self.client.get('/api/genes-by-trait?trait=Test Trait')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([g['gene_symbol'] for g in response.get_json()], ['TEST'])
    
    def test_pharmacogenomic_empty(self):
        response = self.client.get('/api/pharmacogenomic')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])
    
    def test_doctor_pdf_unknown_specialty(self):
        """Unknown specialties are rejected instead of silently using the GP template"""
        response = self.client.get('/api/pdf/doctor/astrologer')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.get_json()['success'])
    
    def test_metrics_routine_only_toggle(self):
        """The checkbox defaults on, and an unchecked submission turns it off"""
        default = self.client.get('/metrics').get_data(as_text=True)
        self.assertIn('name="routine_only" value="true" checked', default)
        submitted = self.client.get('/metrics?metric_type=&start_date=&end_date=').get_data(as_text=True)
        self.assertIn('name="routine_only" value="true" >', submitted.replace('value="true"  ', 'value="true" '))
        self.assertNotIn('value="true" checked', submitted)
    
    def test_gene_info_missing_parameter(self):
        """Test /api/gene-info with missing parameter"""
        response = self.client.get('/api/gene-info')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_gene_info_invalid_gene(self):
        """Test /api/gene-info with invalid gene symbol"""
        response = self.client.get('/api/gene-info?gene=INVALID123!')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_gene_info_not_found(self):
        """Test /api/gene-info with non-existent gene"""
        response = self.client.get('/api/gene-info?gene=NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_genes_by_condition_missing_parameter(self):
        """Test /api/genes-by-condition with missing parameter"""
        response = self.client.get('/api/genes-by-condition')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_genes_by_trait_missing_parameter(self):
        """Test /api/genes-by-trait with missing parameter"""
        response = self.client.get('/api/genes-by-trait')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()

