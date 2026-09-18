# Test Suite

This directory contains unit and integration tests for the Genetic Profile Database application.

## Test Structure

- `test_validation.py` - Tests for input validation functions
- `test_database_manager.py` - Tests for database operations
- `test_api_endpoints.py` - Integration tests for API endpoints

## Running Tests

### Using unittest (built-in)
```bash
# Run all tests
python3 -m unittest discover tests

# Run specific test file
python3 -m unittest tests.test_validation

# Run specific test class
python3 -m unittest tests.test_validation.TestGeneSymbolValidation
```

### Using pytest (recommended)
```bash
# Install pytest
pip3 install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_validation.py

# Run with verbose output
pytest tests/ -v
```

## Test Coverage

Current test coverage includes:
- ✅ Input validation (gene symbols, conditions, traits)
- ✅ Database CRUD operations
- ✅ API endpoint validation
- ✅ Error handling

## Adding New Tests

When adding new features:
1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use descriptive test method names: `test_feature_name`
4. Include both positive and negative test cases
5. Clean up test data in `tearDown()` methods

## Example Test

```python
import unittest
from validation import validate_gene_symbol

class TestMyFeature(unittest.TestCase):
    def test_my_feature(self):
        is_valid, error = validate_gene_symbol('COMT')
        self.assertTrue(is_valid)
```

