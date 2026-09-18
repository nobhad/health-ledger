#!/usr/bin/env python3
"""
Unit tests for validation module
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import (
    validate_gene_symbol,
    validate_condition_name,
    validate_trait_name,
    validate_list_param,
    create_error_response
)
from app import app


class TestGeneSymbolValidation(unittest.TestCase):
    """Test gene symbol validation"""
    
    def test_valid_gene_symbols(self):
        """Test valid gene symbols"""
        valid_symbols = ['ADRA2A', 'COMT', 'CYP2D6', 'HTR2A', 'SLC6A4']
        for symbol in valid_symbols:
            is_valid, error = validate_gene_symbol(symbol)
            self.assertTrue(is_valid, f"{symbol} should be valid: {error}")
            self.assertIsNone(error)
    
    def test_invalid_gene_symbols(self):
        """Test invalid gene symbols"""
        invalid_cases = [
            ('', 'empty string'),
            ('abc123!', 'special characters'),
            ('a' * 25, 'too long'),
        ]
        
        for symbol, description in invalid_cases:
            is_valid, error = validate_gene_symbol(symbol)
            self.assertFalse(is_valid, f"{description} should be invalid")
            self.assertIsNotNone(error)
    
    def test_none_gene_symbol(self):
        """Test None gene symbol validation"""
        # validate_gene_symbol handles None by converting to string
        is_valid, error = validate_gene_symbol(None)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_case_insensitive(self):
        """Test that validation accepts any case"""
        is_valid, error = validate_gene_symbol('comt')
        self.assertTrue(is_valid, "Should accept lowercase")
        
        is_valid, error = validate_gene_symbol('Comt')
        self.assertTrue(is_valid, "Should accept mixed case")


class TestConditionValidation(unittest.TestCase):
    """Test condition name validation"""
    
    def test_valid_conditions(self):
        """Test valid condition names"""
        valid_conditions = ['ADHD', 'Anxiety', 'Depression', 'Type 2 Diabetes']
        for condition in valid_conditions:
            is_valid, error = validate_condition_name(condition)
            self.assertTrue(is_valid, f"{condition} should be valid: {error}")
            self.assertIsNone(error)
    
    def test_invalid_conditions(self):
        """Test invalid condition names"""
        invalid_cases = [
            ('', 'empty string'),
            ('a' * 250, 'too long'),
            ('Test<script>', 'XSS attempt'),
            ('Test>alert', 'XSS attempt'),
        ]
        
        for condition, description in invalid_cases:
            is_valid, error = validate_condition_name(condition)
            self.assertFalse(is_valid, f"{description} should be invalid")
            self.assertIsNotNone(error)


class TestTraitValidation(unittest.TestCase):
    """Test trait name validation"""
    
    def test_valid_traits(self):
        """Test valid trait names"""
        valid_traits = ['pain sensitivity', 'stress response', 'ADHD susceptibility']
        for trait in valid_traits:
            is_valid, error = validate_trait_name(trait)
            self.assertTrue(is_valid, f"{trait} should be valid: {error}")
            self.assertIsNone(error)
    
    def test_invalid_traits(self):
        """Test invalid trait names"""
        invalid_cases = [
            ('', 'empty string'),
            ('a' * 250, 'too long'),
            ('Test<script>', 'XSS attempt'),
        ]
        
        for trait, description in invalid_cases:
            is_valid, error = validate_trait_name(trait)
            self.assertFalse(is_valid, f"{description} should be invalid")
            self.assertIsNotNone(error)


class TestListParamValidation(unittest.TestCase):
    """Test list parameter validation"""
    
    def test_string_to_list(self):
        """Test converting string to list"""
        is_valid, error, result = validate_list_param('ADHD', 'condition')
        self.assertTrue(is_valid)
        self.assertEqual(result, ['ADHD'])
    
    def test_list_param(self):
        """Test list parameter"""
        is_valid, error, result = validate_list_param(['ADHD', 'Anxiety'], 'condition')
        self.assertTrue(is_valid)
        self.assertEqual(len(result), 2)
    
    def test_empty_list(self):
        """Test empty list"""
        is_valid, error, result = validate_list_param(None, 'condition')
        self.assertTrue(is_valid)
        self.assertEqual(result, [])
    
    def test_max_items(self):
        """Test max items limit"""
        large_list = ['item'] * 101
        is_valid, error, result = validate_list_param(large_list, 'condition', max_items=100)
        self.assertFalse(is_valid)
        self.assertIn('100', error)


class TestErrorResponse(unittest.TestCase):
    """Test error response creation"""
    
    def test_basic_error(self):
        """Test basic error response"""
        with app.app_context():
            response, status = create_error_response('Test error', 400)
            self.assertEqual(status, 400)
            # Response is a Flask Response object
            self.assertIsNotNone(response)
            # Check response has JSON data
            data = response.get_json()
            self.assertIn('error', data)
            self.assertEqual(data['status'], 400)
    
    def test_error_with_details(self):
        """Test error with details"""
        with app.app_context():
            response, status = create_error_response('Test error', 400, {'field': 'value'})
            self.assertEqual(status, 400)
            # Response is a Flask Response object
            self.assertIsNotNone(response)
            data = response.get_json()
            self.assertIn('error', data)
            self.assertIn('details', data)


if __name__ == '__main__':
    unittest.main()

