# Database Query Feature

**Last Updated**: December 7, 2025

## Overview

The database query system provides programmatic access to genetic profile data through the `GeneticProfileDB` class. It supports complex queries for genes, traits, health conditions, interactions, and pharmacogenomic data.

**Key Features:**

- 🔍 Comprehensive query methods for all data types
- 🔗 Relationship queries (gene-gene interactions)
- 💊 Pharmacogenomic data queries
- 📊 View-based queries for common patterns
- 🛡️ Thread-safe database connections

---

## Table of Contents

- [Database Connection](#database-connection)
- [Gene Queries](#gene-queries)
- [Trait Queries](#trait-queries)
- [Health Condition Queries](#health-condition-queries)
- [Interaction Queries](#interaction-queries)
- [Pharmacogenomic Queries](#pharmacogenomic-queries)
- [Citation Queries](#citation-queries)
- [Database Views](#database-views)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)
- [Related Files](#related-files)

---

## Database Connection

### Basic Usage

```python
from database_manager import GeneticProfileDB

# Create database connection
db = GeneticProfileDB()

# Always close when done
db.close()
```

### Thread Safety

The database uses SQLite's WAL (Write-Ahead Logging) mode for better concurrency:

```python
# Automatically enabled in _connect()
self.conn.execute('PRAGMA journal_mode=WAL')
```

### Connection Pooling (Flask)

In Flask applications, use thread-local storage:

```python
from flask import g

def get_db():
    if 'db' not in g:
        g.db = GeneticProfileDB()
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()
```

---

## Gene Queries

### Get All Genes

```python
genes = db.get_all_genes()
# Returns: List[Dict] with gene_symbol, gene_name, chromosome
```

### Get Gene by Symbol

```python
gene = db.get_gene_by_symbol("COMT")
# Returns: Dict with id, gene_symbol, gene_name, chromosome
# Returns: None if not found
```

### Get Gene by ID

```python
gene = db.get_gene_by_id(1)
# Returns: Dict with gene information
```

### Search Genes

```python
# Search by symbol or name
results = db.search_genes("COMT")
# Returns: List[Dict] matching search term
```

---

## Trait Queries

### Get Traits for Gene

```python
traits = db.get_trait_associations_for_gene(gene_id)
# Returns: List[Dict] with trait_name, association_direction, notes
```

### Get Genes with Trait

```python
genes = db.get_genes_with_trait("pain sensitivity")
# Returns: List[Dict] with gene information and trait details
```

### Search Traits

```python
traits = db.search_traits("pain")
# Returns: List[str] of matching trait names
```

### Get All Traits

```python
traits = db.get_all_traits()
# Returns: List[str] of all unique trait names
```

---

## Health Condition Queries

### Get Conditions for Gene

```python
conditions = db.get_health_conditions_for_gene(gene_id)
# Returns: List[Dict] with condition_name, association_type, notes
```

### Get Genes with Condition

```python
genes = db.get_genes_with_condition("ADHD")
# Returns: List[Dict] with gene information and condition details
```

### Search Conditions

```python
conditions = db.search_conditions("ADHD")
# Returns: List[str] of matching condition names
```

### Get All Conditions

```python
conditions = db.get_all_conditions()
# Returns: List[str] of all unique condition names
```

---

## Interaction Queries

### Get Interacting Genes

```python
interactions = db.get_interacting_genes("COMT")
# Returns: List[Dict] with interacting gene information
```

### Get Interaction Details

```python
interaction = db.get_gene_interaction("COMT", "ADRA2A")
# Returns: Dict with interaction_type, description, notes
```

### Add Gene Interaction

```python
interaction_id = db.add_gene_interaction(
    gene_id=1,
    interacting_gene_symbol="ADRA2A",
    interaction_type="modulates",
    description="COMT modulates ADRA2A activity",
    notes="Val/Val genotype increases interaction"
)
```

---

## Pharmacogenomic Queries

### Get Pharmacogenomic Data for Gene

```python
pharm_data = db.get_pharmacogenomic_data_for_gene(gene_id)
# Returns: Dict with metabolism_status, genotype_phenotype, affected_medications
```

### Get All Pharmacogenomic Data

```python
all_pharm = db.get_all_pharmacogenomic_data()
# Returns: List[Dict] with gene and medication information
```

### Get Medications for Gene

```python
medications = db.get_medications_for_gene(gene_id)
# Returns: List[str] of medication names
```

### Query by Medication

```python
genes = db.get_genes_for_medication("Citalopram")
# Returns: List[Dict] of genes affecting this medication
```

---

## Citation Queries

### Get Citations for Gene

```python
citations = db.get_citations_for_gene(gene_id)
# Returns: List[Dict] with citation information
```

### Get Citation by Number

```python
citation = db.get_citation_by_number(1)
# Returns: Dict with full citation details
```

### Get All Citations

```python
citations = db.get_all_citations()
# Returns: List[Dict] of all citations
```

### Search Citations

```python
results = db.search_citations("ADHD")
# Returns: List[Dict] matching search term
```

---

## Database Views

The database includes several views for common query patterns:

### gene_summary View

```sql
SELECT * FROM gene_summary WHERE gene_symbol = 'COMT';
```

Returns: Gene with trait and condition counts.

### gene_trait_view

```sql
SELECT * FROM gene_trait_view WHERE gene_symbol = 'COMT';
```

Returns: All traits associated with a gene.

### gene_health_view

```sql
SELECT * FROM gene_health_view WHERE gene_symbol = 'COMT';
```

Returns: All health conditions associated with a gene.

### gene_interaction_view

```sql
SELECT * FROM gene_interaction_view WHERE gene_symbol = 'COMT';
```

Returns: All gene-gene interactions.

### gene_pharmacogenomic_view

```sql
SELECT * FROM gene_pharmacogenomic_view WHERE gene_symbol = 'COMT';
```

Returns: Pharmacogenomic data with affected medications.

---

## Error Handling

### Common Exceptions

#### sqlite3.OperationalError

- Database locked: Another process is using the database
- No such table: Schema not initialized
- Solution: Check database file permissions and schema

#### sqlite3.IntegrityError

- UNIQUE constraint failed: Duplicate entry
- FOREIGN KEY constraint failed: Invalid reference
- Solution: Check data before insertion

### Error Handling Pattern

```python
try:
    gene = db.get_gene_by_symbol("COMT")
    if not gene:
        print("Gene not found")
        return
    
    traits = db.get_trait_associations_for_gene(gene['id'])
    print(f"Found {len(traits)} traits")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    db.close()
```

---

## Performance Tips

### Use Views for Complex Queries

Views are pre-computed and faster than JOIN queries:

```python
# Fast: Using view
cursor.execute("SELECT * FROM gene_summary WHERE gene_symbol = ?", ("COMT",))

# Slower: Multiple JOINs
cursor.execute("""
    SELECT g.*, COUNT(DISTINCT t.id) as trait_count
    FROM genes g
    LEFT JOIN trait_associations t ON g.id = t.gene_id
    WHERE g.gene_symbol = ?
    GROUP BY g.id
""", ("COMT",))
```

### Batch Operations

For multiple inserts, use transactions:

```python
db.conn.execute("BEGIN")
try:
    for gene in genes:
        db.add_gene(gene['symbol'], gene['name'])
    db.conn.commit()
except:
    db.conn.rollback()
    raise
```

### Index Usage

The schema includes indexes on frequently queried columns:

- `gene_symbol` (unique index)
- `trait_name`
- `condition_name`
- `citation_number`

---

## Related Files

### Python

- `database_manager.py` - Main database interface class
- `genetic_profile_db_schema.sql` - Database schema definition

### Documentation

- `docs/DATABASE_README.md` - Database architecture documentation
- `docs/DEBUGGING_GUIDE.md` - Debugging database issues

---

## Example Queries

### Find All Genes Related to ADHD

```python
db = GeneticProfileDB()
genes = db.get_genes_with_condition("ADHD")
for gene in genes:
    print(f"{gene['gene_symbol']}: {gene['gene_name']}")
db.close()
```

### Get Complete Gene Profile

```python
db = GeneticProfileDB()
gene = db.get_gene_by_symbol("COMT")
if gene:
    traits = db.get_trait_associations_for_gene(gene['id'])
    conditions = db.get_health_conditions_for_gene(gene['id'])
    interactions = db.get_interacting_genes("COMT")
    pharm = db.get_pharmacogenomic_data_for_gene(gene['id'])
    
    print(f"Gene: {gene['gene_symbol']}")
    print(f"Traits: {len(traits)}")
    print(f"Conditions: {len(conditions)}")
    print(f"Interactions: {len(interactions)}")
    print(f"Pharmacogenomic: {pharm is not None}")
db.close()
```

### Find Medications Affected by Gene

```python
db = GeneticProfileDB()
gene = db.get_gene_by_symbol("CYP2D6")
if gene:
    pharm = db.get_pharmacogenomic_data_for_gene(gene['id'])
    if pharm:
        medications = pharm.get('affected_medications', '').split(',')
        print(f"Medications: {', '.join(medications)}")
db.close()
```

---

## Debugging

### Enable Query Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# SQLite will log queries
db = GeneticProfileDB()
```

### Check Database Integrity

```python
cursor = db.conn.cursor()
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()
print(result[0])  # Should be "ok"
```

### View Table Structure

```python
cursor = db.conn.cursor()
cursor.execute("PRAGMA table_info(genes)")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[1]} ({col[2]})")
```
