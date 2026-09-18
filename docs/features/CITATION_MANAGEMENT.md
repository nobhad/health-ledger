# Citation Management Feature

**Last Updated**: December 7, 2025

## Overview

The Citation Management system handles all references, citations, and bibliographic data in the genetic profile. It ensures proper citation numbering, deduplication, linking, and formatting according to academic standards.

**Key Features:**

- 📚 Citation deduplication
- 🔢 Sequential numbering
- 🔗 Citation linking
- 📝 Multiple reference types
- ✅ Validation and integrity checks

---

## Table of Contents

- [Citation System](#citation-system)
- [Citation Types](#citation-types)
- [Citation Overhaul](#citation-overhaul)
- [Database Schema](#database-schema)
- [Citation Linking](#citation-linking)
- [Usage](#usage)
- [Related Files](#related-files)

---

## Citation System

### Citation Numbering

Citations are numbered sequentially starting from 1. Each citation has a unique number that appears in the document as `[1]`, `[2,3]`, etc.

### Citation Format

**In-Text Citations:**
```markdown
This finding is supported by research [1,2,3].
```

**Reference List:**
```markdown
## References

1. Author, A. (2024). Title. *Journal*, 10(2), 123-145. doi:10.1234/example
2. GeneSight. (2022). Get to know a gene: ADRA2A. https://genesight.com/...
3. PubMed. (2023). SNP rs1800544. https://pubmed.ncbi.nlm.nih.gov/...
```

### Citation Standards

**Allowed Sources:**
- ✅ PubMed peer-reviewed journals
- ✅ NCBI databases (GTR, Bookshelf, MedlinePlus Genetics)
- ✅ SNPedia
- ✅ GWAS Catalog
- ✅ Primary source documents (GeneSight, Center for Human Genetics)

**Not Allowed:**
- ❌ Wikipedia
- ❌ Commercial genetics blogs
- ❌ Non-peer-reviewed sources
- ❌ Personal blogs

---

## Citation Types

### 1. Journal Articles

**Format:**
```python
db.add_reference(
    citation_number=1,
    authors="Smith, J., & Jones, A.",
    year=2024,
    title="Genetic associations with ADHD",
    journal="Journal of Genetics",
    volume="10",
    pages="123-145",
    doi="10.1234/example",
    pubmed_id="12345678",
    reference_type="journal"
)
```

### 2. Websites

**Format:**
```python
db.add_reference(
    citation_number=163,
    authors="GeneSight",
    year=2022,
    title="Get to know a gene: ADRA2A",
    url="https://genesight.com/genes/adra2a",
    reference_type="website"
)
```

### 3. Database Entries

**Format:**
```python
db.add_reference(
    citation_number=50,
    authors="SNPedia",
    title="rs1800544",
    url="https://www.snpedia.com/index.php/rs1800544",
    reference_type="database"
)
```

### 4. Primary Sources

**Format:**
```python
db.add_reference(
    citation_number=164,
    authors="Center for Human Genetics",
    year=2025,
    title="Clinical Consultation Report",
    reference_type="primary_source"
)
```

### 5. Research References

**New Feature**: Enhanced research references with abstracts and keywords

```python
db.add_research_reference(
    reference_number=1,
    authors="Smith, J.",
    year=2024,
    title="Genetic Study",
    journal="Nature Genetics",
    abstract="Full abstract text...",
    keywords="genetics, ADHD, COMT",
    pubmed_id="12345678",
    reference_type="journal"
)
```

---

## Citation Overhaul

### Purpose

The citation overhaul script (`scripts/citation_overhaul.py`) fixes and deduplicates citations in the markdown document.

### Process

1. **Extract All Citations**
   - Parse references section
   - Extract citation details
   - Store in structured format

2. **Deduplicate**
   - Compare citations by content
   - Identify duplicates
   - Merge duplicate entries

3. **Renumber**
   - Assign sequential numbers
   - Update all in-text citations
   - Maintain relationships

4. **Generate Corrected Document**
   - Create new markdown file
   - Update all citation numbers
   - Preserve document structure

### Usage

```bash
python3 scripts/citation_overhaul.py
```

### Output

- `Genetic_Profile_Non_Pharmacogenomic_Corrected.md` - Corrected document
- Deduplication report
- Citation mapping (old → new numbers)

---

## Database Schema

### Citations Table

```sql
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_number INTEGER UNIQUE NOT NULL,
    authors TEXT,
    year INTEGER,
    title TEXT,
    journal TEXT,
    volume TEXT,
    pages TEXT,
    doi TEXT,
    pubmed_id TEXT,
    url TEXT,
    reference_type TEXT DEFAULT 'journal'
);
```

### Research References Table

**New Feature**: Enhanced research references table

```sql
CREATE TABLE research_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number INTEGER UNIQUE NOT NULL,
    authors TEXT,
    year INTEGER,
    title TEXT,
    journal TEXT,
    volume TEXT,
    pages TEXT,
    doi TEXT,
    pubmed_id TEXT,
    url TEXT,
    reference_type TEXT DEFAULT 'journal',
    abstract TEXT,
    keywords TEXT
);
```

### Citation Linking Tables

- `gene_trait_citations` - Links citations to trait associations
- `gene_health_citations` - Links citations to health condition associations
- `research_finding_citations` - Links citations to research findings

---

## Citation Linking

### Link Citation to Trait Association

```python
trait_id = db.add_trait_association(
    gene_id=gene_id,
    trait_name="ADHD susceptibility",
    reference_ids=[1, 2, 3]  # Citation numbers
)
```

### Link Citation to Health Condition

```python
condition_id = db.add_health_condition_association(
    gene_id=gene_id,
    condition_name="ADHD",
    reference_ids=[1, 2]  # Citation numbers
)
```

### Link Citation to Research Finding

```python
finding_id = db.add_research_finding(
    gene_id=gene_id,
    finding_text="COMT Val/Val associated with pain sensitivity",
    reference_ids=[5, 6, 7]  # Citation numbers
)
```

### Query Citations for Gene

```python
citations = db.get_references_for_gene(gene_id)
# Returns all citations linked to the gene through any association
```

---

## Usage

### Add Citation

```python
from database_manager import GeneticProfileDB

db = GeneticProfileDB()

# Get next citation number
max_citation = db.get_max_citation_number()
next_citation = max_citation + 1

# Add citation
citation_id = db.add_reference(
    citation_number=next_citation,
    authors="Smith, J.",
    year=2024,
    title="Genetic Study",
    journal="Nature",
    doi="10.1234/example",
    pubmed_id="12345678"
)

db.close()
```

### Add Research Reference

```python
ref_id = db.add_research_reference(
    reference_number=next_citation,
    authors="Smith, J.",
    year=2024,
    title="Comprehensive Genetic Analysis",
    journal="Nature Genetics",
    abstract="This study examines...",
    keywords="genetics, ADHD, COMT",
    pubmed_id="12345678"
)
```

### Link Citations

```python
# Add trait with citations
trait_id = db.add_trait_association(
    gene_id=gene_id,
    trait_name="pain sensitivity",
    association_direction="increased",
    reference_ids=[1, 2, 3]  # Multiple citations
)
```

### Query Citations

```python
# Get all citations
all_citations = db.get_all_references()

# Get citations for gene
gene_citations = db.get_references_for_gene(gene_id)

# Get citation by number
citation = db.get_citation_by_number(1)
```

---

## Citation Validation

### Required Fields

- `citation_number` (required, unique)
- At least one of: `title`, `authors`, `url`

### Validation Rules

```python
def validate_citation(citation_data):
    if not citation_data.get('citation_number'):
        raise ValueError("Citation number is required")
    
    if not any([
        citation_data.get('title'),
        citation_data.get('authors'),
        citation_data.get('url')
    ]):
        raise ValueError("Citation must have title, authors, or URL")
    
    return True
```

### Duplicate Detection

```python
def check_duplicate(citation_data):
    # Check by title and authors
    existing = db.search_citations(citation_data['title'])
    for cit in existing:
        if cit['authors'] == citation_data['authors']:
            return cit['citation_number']
    return None
```

---

## Related Files

### Scripts
- `scripts/citation_overhaul.py` - Citation deduplication and renumbering
- `scripts/add_primary_sources.py` - Add primary source citations

### Python
- `database_manager.py` - Citation database operations
- `generate_html.py` - Citation link generation

### Documentation
- `docs/CITATION_OVERHAUL_SUMMARY.md` - Citation overhaul details

---

## Debugging

### Citation Number Conflicts

1. **Check for duplicates**:
   ```python
   db = GeneticProfileDB()
   citations = db.get_all_citations()
   numbers = [c['citation_number'] for c in citations]
   duplicates = [n for n in numbers if numbers.count(n) > 1]
   print(f"Duplicate numbers: {duplicates}")
   ```

2. **Get max citation number**:
   ```python
   max_citation = db.get_max_citation_number()
   print(f"Max citation number: {max_citation}")
   ```

### Missing Citation Links

1. **Check trait associations**:
   ```python
   traits = db.get_trait_associations_for_gene(gene_id)
   for trait in traits:
       print(f"Trait: {trait['trait_name']}, Citations: {trait.get('citation_numbers')}")
   ```

2. **Verify linking tables**:
   ```sql
   SELECT * FROM gene_trait_citations WHERE trait_association_id = ?;
   ```

### Citation Format Issues

1. **Check citation format**:
   ```python
   citation = db.get_citation_by_number(1)
   print(f"Title: {citation['title']}")
   print(f"Authors: {citation['authors']}")
   print(f"Year: {citation['year']}")
   ```

2. **Validate required fields**:
   - Ensure citation_number is unique
   - Verify at least one identifying field exists

---

## Future Enhancements

- [ ] Automatic citation extraction from URLs
- [ ] PubMed API integration
- [ ] Citation style formatting (APA, MLA, etc.)
- [ ] Citation export (BibTeX, RIS)
- [ ] Citation impact metrics
- [ ] Duplicate detection algorithms
- [ ] Citation network visualization
- [ ] Automated reference checking

