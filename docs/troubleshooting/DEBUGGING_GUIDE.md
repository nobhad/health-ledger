# Debugging Guide

Comprehensive guide for debugging the Genetic Profile Database application.

## Table of Contents

1. [Logging System](#logging-system)
2. [Common Issues](#common-issues)
3. [Database Debugging](#database-debugging)
4. [API Debugging](#api-debugging)
5. [Frontend Debugging](#frontend-debugging)
6. [Performance Debugging](#performance-debugging)

## Logging System

### Log Levels

The application uses Python's standard logging levels:

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause the application to stop

### Log Locations

- **Console**: All logs are printed to stdout/stderr
- **File**: Logs are written to `logs/app.log` (if configured)

### Viewing Logs

```bash
# View live logs
tail -f logs/app.log

# View last 100 lines
tail -n 100 logs/app.log

# Search for errors
grep ERROR logs/app.log

# Search for specific gene queries
grep "gene: COMT" logs/app.log
```

### Configuring Logging

Edit `config.py` to change log levels:

```python
# Enable debug logging
DEBUG = True
LOG_LEVEL = logging.DEBUG

# Disable debug logging
DEBUG = False
LOG_LEVEL = logging.INFO
```

## Common Issues

### 1. Database Connection Errors

**Symptoms:**
- "SQLite objects created in a thread can only be used in that same thread"
- Database locked errors
- Connection timeout errors

**Solutions:**

1. **Check thread-local storage:**
   ```python
   # In app.py, verify get_db() is using thread-local storage
   _local = threading.local()
   ```

2. **Verify database file permissions:**
   ```bash
   ls -la genetic_profile.db
   # Should be readable/writable
   ```

3. **Check for database locks:**
   ```bash
   # Close any other connections
   # Remove lock files if safe
   rm genetic_profile.db-shm genetic_profile.db-wal
   ```

### 2. API Endpoint Errors

**Symptoms:**
- 500 Internal Server Error
- Empty responses
- Timeout errors

**Debugging Steps:**

1. **Check server logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Test endpoint directly:**
   ```bash
   curl http://localhost:5001/api/test
   curl http://localhost:5001/api/all-genes
   ```

3. **Check request parameters:**
   ```bash
   # With parameters
   curl "http://localhost:5001/api/genes-by-condition?condition=ADHD"
   ```

4. **Enable debug mode:**
   ```python
   # In config.py
   DEBUG = True
   ```

### 3. Template Rendering Errors

**Symptoms:**
- Template not found errors
- Template syntax errors
- Missing variables

**Solutions:**

1. **Verify template files exist:**
   ```bash
   ls -la templates/
   ```

2. **Check template syntax:**
   ```python
   from jinja2 import Environment, FileSystemLoader
   env = Environment(loader=FileSystemLoader('templates'))
   template = env.get_template('query.html')
   ```

3. **Check template variables:**
   - Ensure all variables passed to `render_template()` exist
   - Check for typos in variable names

### 4. JavaScript Errors

**Symptoms:**
- Multiselect dropdowns not working
- API calls failing
- Console errors

**Debugging Steps:**

1. **Open browser console:**
   - Chrome/Edge: F12 → Console tab
   - Firefox: F12 → Console tab
   - Safari: Cmd+Option+C

2. **Check for errors:**
   ```javascript
   // Common issues:
   // - CORS errors (check Flask CORS configuration)
   // - Network errors (check server is running)
   // - JavaScript syntax errors
   ```

3. **Test API endpoints:**
   ```javascript
   // In browser console
   fetch('/api/all-genes')
     .then(r => r.json())
     .then(data => console.log(data))
     .catch(err => console.error(err))
   ```

## Database Debugging

### Check Database Schema

```python
from database_manager import GeneticProfileDB
db = GeneticProfileDB()
cursor = db.conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(tables)

# Check table structure
cursor.execute("PRAGMA table_info(genes)")
print(cursor.fetchall())
```

### Verify Data Integrity

```python
from database_manager import GeneticProfileDB
db = GeneticProfileDB()

# Count records
print(f"Genes: {len(db.get_all_genes())}")
print(f"Traits: {db.conn.execute('SELECT COUNT(*) FROM trait_associations').fetchone()[0]}")
print(f"Conditions: {db.conn.execute('SELECT COUNT(*) FROM health_condition_associations').fetchone()[0]}")
```

### Query Debugging

```python
# Enable SQL query logging
import logging
logging.getLogger('database_manager').setLevel(logging.DEBUG)

# Run query
db = GeneticProfileDB()
genes = db.get_genes_with_condition("ADHD")
```

## API Debugging

### Test All Endpoints

```bash
# Health check
curl http://localhost:5001/test

# Get all genes
curl http://localhost:5001/api/all-genes

# Get all conditions
curl http://localhost:5001/api/all-conditions

# Get all traits
curl http://localhost:5001/api/all-traits

# Query by condition
curl "http://localhost:5001/api/genes-by-condition?condition=ADHD"

# Query by trait
curl "http://localhost:5001/api/genes-by-trait?trait=pain+sensitivity"

# Get gene info
curl "http://localhost:5001/api/gene-info?gene=COMT"
```

### Enable Detailed Error Responses

In `config.py`:
```python
DEBUG = True  # Returns traceback in error responses
```

### Monitor API Requests

```python
# Add request logging middleware
@app.before_request
def log_request():
    app_logger.info(f"{request.method} {request.path} - {request.remote_addr}")
```

## Frontend Debugging

### Multiselect Component Issues

**Check JavaScript console for:**
- `multiselectState is not defined`
- `Cannot read property 'selected' of undefined`
- API response errors

**Debug steps:**

1. **Verify state initialization:**
   ```javascript
   console.log(multiselectState);
   ```

2. **Check API responses:**
   ```javascript
   fetch('/api/all-genes')
     .then(r => r.json())
     .then(data => {
       console.log('Genes:', data);
       console.log('Is array?', Array.isArray(data));
     });
   ```

3. **Verify DOM elements:**
   ```javascript
   console.log(document.getElementById('geneInput'));
   console.log(document.getElementById('geneDropdown'));
   ```

### CSS Issues

**Check browser developer tools:**
- Inspect element to see computed styles
- Check for CSS conflicts
- Verify media queries

**Common issues:**
- Z-index conflicts (multiselect dropdowns)
- Flexbox/grid layout issues
- Responsive design breakpoints

## Performance Debugging

### Database Query Performance

```python
import time
from database_manager import GeneticProfileDB

db = GeneticProfileDB()

# Time a query
start = time.time()
genes = db.get_all_genes()
elapsed = time.time() - start
print(f"Query took {elapsed:.3f} seconds")
```

### API Response Times

```bash
# Time API calls
time curl http://localhost:5001/api/all-genes
```

### Memory Usage

```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

## Debugging Tools

### Python Debugger (pdb)

```python
import pdb

# Add breakpoint
pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### Flask Debug Toolbar

```python
# Install
pip install flask-debugtoolbar

# Add to app.py
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)
```

### Database Browser

Use SQLite browser tools:
- DB Browser for SQLite (GUI)
- `sqlite3` command-line tool

```bash
sqlite3 genetic_profile.db
.tables
.schema genes
SELECT * FROM genes LIMIT 5;
```

## Getting Help

1. **Check logs first:** `logs/app.log`
2. **Review error messages:** Look for stack traces
3. **Test individual components:** Isolate the problem
4. **Check documentation:** This guide and other docs
5. **Review code:** Use debugger to step through

## Debug Checklist

- [ ] Check application logs
- [ ] Verify database connection
- [ ] Test API endpoints directly
- [ ] Check browser console for JavaScript errors
- [ ] Verify template files exist
- [ ] Check file permissions
- [ ] Verify environment variables
- [ ] Test with minimal data
- [ ] Check for recent code changes
- [ ] Review error messages carefully

