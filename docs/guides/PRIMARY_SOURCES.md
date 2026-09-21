# Primary Sources Extraction Guide

## Overview

This system extracts and stores all information from primary source documents (PDFs, medical records, lab results, etc.) in the database. It automatically cross-references health logs with other documents to determine if entries were for sick visits.

## Database Tables

### New Tables Created

1. **research_references**: For research papers, studies, and academic references
2. **primary_sources**: For healthcare data, medical records, test results, etc.
3. **primary_source_findings**: Key findings extracted from primary sources

## Running the Extraction

### Extract All Primary Sources

To extract data from all PDFs in the `primary_sources` folder:

```bash
python3 scripts/extract_all_primary_sources.py
```

This script:

1. **First Pass**: Extracts lab results and test data for cross-referencing
2. **Second Pass**: Processes all documents and adds them to the database
3. **Cross-References**: Health logs are analyzed against lab results and test results to determine if entries were for sick visits

### What Gets Extracted

For each primary source:

- Document metadata (date, institution, type)
- Full text content (up to 50,000 characters)
- Key findings and observations
- Visit type classification (sick visit vs routine visit)

### Health Log Processing

Health logs are parsed into individual entries, and each entry is analyzed to determine if it was a sick visit by:

- Checking for sick visit keywords (symptoms, pain, illness, etc.)
- Cross-referencing with lab results from the same time period
- Checking for abnormal test values
- Analyzing visit context

## Document Types Recognized

- **health_log**: Health logs and visit records
- **health_issue**: Health issues documents
- **lab_result**: Lab test results
- **medical_record**: Medical records
- **test_report**: Test reports (genetic testing, etc.)
- **imaging**: CT scans, MRIs, X-rays, ECGs
- **evaluation**: Neuropsychological evaluations
- **health_summary**: Health summaries

## Cross-Referencing Logic

The system determines if a health log entry was a sick visit by:

1. **Keyword Analysis**: Looks for words like "sick", "symptom", "pain", "fever", etc.
2. **Date Matching**: Checks if lab results or test results exist within 7 days of the log entry
3. **Abnormal Values**: If abnormal lab values are found around the same date, it's marked as a sick visit
4. **Context Analysis**: Examines the entry text for diagnostic language

## Adding Healthcare Summaries

After each doctor's appointment, you can add a summary:

```bash
python3 scripts/add_healthcare_summary.py
```

This creates a structured record that can be cross-referenced with other documents.

## Viewing Extracted Data

View all primary sources:

```python
from database_manager import GeneticProfileDB

db = GeneticProfileDB()
sources = db.get_all_primary_sources()
for source in sources:
    print(f"{source['source_name']} - {source['document_date']}")
    findings = db.get_primary_source_findings(source['id'])
    print(f"  Findings: {len(findings)}")
```

## Integration

The extracted data integrates with:

- Gene associations (if genes are mentioned)
- Health condition associations
- Research findings
- Citations and references

## Next Steps

1. Run `extract_all_primary_sources.py` to process all existing documents
2. Use `add_healthcare_summary.py` after each appointment
3. The system will automatically cross-reference new documents with existing data
