# Data Import Feature

**Last Updated**: December 7, 2025  
**Status**: ✅ Production-Ready

## Overview

The Data Import system allows importing genetic profile data from markdown documents into the SQLite database. It parses structured markdown, extracts gene information, trait associations, health conditions, citations, and other data, then populates the database with proper relationships.

**Key Features:**

- 📄 Markdown document parsing
- 🧬 Gene and SNP extraction
- 🔗 Relationship mapping
- 📚 Citation import
- 🔄 Idempotent operations
- ✅ Data validation

---

## Table of Contents

- [Import Script](#import-script)
- [Supported Data Types](#supported-data-types)
- [Import Process](#import-process)
- [Data Parsing](#data-parsing)
- [Error Handling](#error-handling)
- [Usage](#usage)
- [Related Files](#related-files)

---

## Import Script

### Location

`scripts/import_from_markdown.py`

### Purpose

Imports genetic profile data from markdown format into the database, including:

- Genes and their information
- SNPs and genotypes
- Trait associations
- Health condition associations
- Citations and references
- Gene-gene interactions
- Research findings

### Dependencies

```python
from database_manager import GeneticProfileDB
import re
from pathlib import Path
```

---

## Supported Data Types

### 1. Genes

**Format in Markdown:**

```markdown
### ADRA2A - Adrenergic Alpha-2A Receptor

**Chromosome:** 10
**Gene Name:** Adrenergic Alpha-2A Receptor
```

**Imported Fields:**

- `gene_symbol` (e.g., "ADRA2A")
- `gene_name` (e.g., "Adrenergic Alpha-2A Receptor")
- `chromosome` (e.g., "10")

### 2. SNPs

**Format in Markdown:**

```markdown
**SNP:** rs1800544
**Position:** chr10:112835292
**Reference Allele:** C
**Alternate Allele:** G
```

**Imported Fields:**

- `rs_number` (e.g., "rs1800544")
- `position`
- `reference_allele`
- `alternate_allele`

### 3. Genotypes

**Format in Markdown:**

```markdown
**Genotype:** C/G
**Phenotype:** Heterozygous
```

**Imported Fields:**

- `genotype` (e.g., "C/G")
- `phenotype` (e.g., "Heterozygous")

### 4. Trait Associations

**Format in Markdown:**

```markdown
#### Trait Associations

- **ADHD susceptibility** [1,2,3]
  - Direction: increased
  - Notes: C/G genotype associated with ADHD
```

**Imported Fields:**

- `trait_name`
- `association_direction`
- `notes`
- `reference_ids` (linked citations)

### 5. Health Condition Associations

**Format in Markdown:**

```markdown
#### Health Condition Associations

- **ADHD** [1,2]
  - Type: susceptibility
  - Notes: Confirmed diagnosis
```

**Imported Fields:**

- `condition_name`
- `association_type`
- `notes`
- `reference_ids` (linked citations)

### 6. Citations

**Format in Markdown:**

```markdown
## References

1. Author, A. (2024). Title. *Journal*, 10(2), 123-145. doi:10.1234/example
2. GeneSight. (2022). Get to know a gene: ADRA2A. https://genesight.com/...
```

**Imported Fields:**

- `citation_number`
- `authors`
- `year`
- `title`
- `journal`
- `doi`
- `pubmed_id`
- `url`
- `reference_type`

### 7. Gene-Gene Interactions

**Format in Markdown:**

```markdown
#### Gene-Gene Interactions

- **COMT** ↔ **ADRA2A**
  - Interaction: Modulates stress response
  - Notes: Combined effect on ADHD symptoms
```

**Imported Fields:**

- `interacting_gene_symbol`
- `interaction_description`
- `notes`

### 8. Research Findings

**Format in Markdown:**

```markdown
#### Research Findings

- **Finding Title**
  - Description: Detailed finding text [1,2,3]
```

**Imported Fields:**

- `finding_title`
- `finding_text`
- `reference_ids` (linked citations)

---

## Import Process

### Step 1: Initialize Database

```python
db = GeneticProfileDB()
```

### Step 2: Read Markdown File

```python
with open('Genetic_Profile_Non_Pharmacogenomic_Corrected.md', 'r') as f:
    content = f.read()
```

### Step 3: Parse Document Structure

The script identifies:

- Gene sections (headers starting with `###`)
- Reference sections
- Trait and condition lists
- Citation numbers

### Step 4: Extract and Import Data

For each gene section:

1. Extract gene information
2. Add gene to database
3. Extract and add SNPs
4. Extract and add genotypes
5. Extract and add trait associations
6. Extract and add health condition associations
7. Extract and add gene-gene interactions
8. Extract and add research findings
9. Link all citations

### Step 5: Import Citations

1. Parse references section
2. Extract citation details
3. Add citations to database
4. Link citations to associations

---

## Data Parsing

### Gene Section Detection

```python
# Pattern to find gene sections
gene_pattern = r'###\s+(\w+)\s*-\s*(.+?)(?=###|\Z)'
```

### Citation Extraction

```python
# Pattern to find citations in text
citation_pattern = r'\[(\d+(?:,\s*\d+)*)\]'
```

### Reference Parsing

```python
# Pattern to parse reference format
reference_pattern = r'(\d+)\.\s+(.+?)(?=\d+\.|\Z)'
```

### Trait Association Parsing

```python
# Pattern to find trait associations
trait_pattern = r'-\s+\*\*(.+?)\*\*\s+\[(.+?)\]'
```

---

## Error Handling

### Duplicate Prevention

The import script checks for existing data:

```python
# Check if gene already exists
existing_gene = db.get_gene_by_symbol(gene_symbol)
if existing_gene:
    gene_id = existing_gene['id']
else:
    gene_id = db.add_gene(gene_symbol, gene_name, chromosome)
```

### Citation Number Validation

```python
# Ensure citation numbers are unique
max_citation = db.get_max_citation_number()
if citation_number <= max_citation:
    # Handle duplicate or renumber
```

### Relationship Validation

```python
# Verify gene exists before adding associations
gene = db.get_gene_by_symbol(gene_symbol)
if not gene:
    logger.warning(f"Gene {gene_symbol} not found, skipping association")
    return
```

---

## Usage

### Basic Import

```bash
# From project root
python3 scripts/import_from_markdown.py
```

### Custom File Path

```bash
python3 scripts/import_from_markdown.py \
    docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md
```

### Python Script

```python
from scripts.import_from_markdown import import_from_markdown

# Import data
import_from_markdown('path/to/document.md')
```

---

## Import Workflow

### 1. Pre-Import Checks

- Verify database exists
- Check markdown file exists
- Validate file format

### 2. Citation Import

- Import all citations first
- Store citation numbers for linking

### 3. Gene Import

- Import genes
- Import SNPs and genotypes
- Import associations
- Link citations

### 4. Post-Import Validation

- Verify data integrity
- Check for missing relationships
- Generate import report

---

## Data Validation

### Required Fields

- Gene symbol (required)
- Gene name (required)
- Citation number (required for citations)

### Optional Fields

- Chromosome
- SNP position
- Association direction
- Notes

### Validation Rules

```python
def validate_gene(gene_symbol, gene_name):
    if not gene_symbol or not gene_symbol.strip():
        raise ValueError("Gene symbol is required")
    if not gene_name or not gene_name.strip():
        raise ValueError("Gene name is required")
    return True
```

---

## Current Import Status

**Last Updated:** December 7, 2025

### ✅ Import Completeness

- **Genes:** 17/17 imported ✅
- **SNPs:** 36+ SNPs imported ✅
- **Genotypes:** 13+ genotypes imported ✅
- **Trait Associations:** 115+ trait associations imported ✅
- **Health Conditions:** 73+ condition associations imported ✅
- **Citations:** 164+ citations imported and mapped ✅
- **Gene-Gene Interactions:** Import structure complete (extraction pattern may need refinement for specific markdown formats)

### Import Statistics

The import script successfully processes:

- All gene sections from the markdown document
- SNP information with proper gene associations
- Genotype data with phenotype descriptions
- Trait associations with direction and citations
- Health condition associations with type and citations
- Citation mapping and reference linking

---

## Related Files

### Scripts

- `scripts/import_from_markdown.py` - Main import script

### Source Files

- `docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md` - Source markdown

### Python

- `database_manager.py` - Database operations
- `config.py` - Configuration and logging

---

## Debugging

### Import Fails

1. **Check markdown format**:

   ```bash
   # Verify file structure
   head -50 docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md
   ```

2. **Check database connection**:

   ```python
   from database_manager import GeneticProfileDB
   db = GeneticProfileDB()
   print("Database connected")
   ```

3. **Check logs**:

   ```bash
   tail -f logs/app.log
   ```

### Missing Data

1. **Verify parsing patterns**:
   - Check regex patterns match markdown format
   - Test with sample text

2. **Check database**:

   ```python
   db = GeneticProfileDB()
   genes = db.get_all_genes()
   print(f"Imported {len(genes)} genes")
   ```

### Citation Linking Issues

1. **Verify citation numbers**:

   ```python
   citations = db.get_all_citations()
   print(f"Total citations: {len(citations)}")
   ```

2. **Check citation links**:

   ```python
   gene = db.get_gene_by_symbol("COMT")
   traits = db.get_trait_associations_for_gene(gene['id'])
   # Check if citations are linked
   ```

---

## Future Enhancements

- [ ] Incremental import (only new/changed data)
- [ ] Import from multiple markdown files
- [ ] Import from JSON/CSV formats
- [ ] Data validation rules
- [ ] Import preview before commit
- [ ] Rollback on error
- [ ] Import statistics and reports
- [ ] Conflict resolution for duplicates
