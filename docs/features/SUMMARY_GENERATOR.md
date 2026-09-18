# Summary Generator Feature

**Last Updated**: December 7, 2025

## Overview

The Summary Generator creates a personalized summary of the genetic profile, synthesizing key findings, strengths, sensitivities, medication metabolism, gene-gene interactions, and clinical recommendations into a concise, actionable document.

**Key Features:**

- 📊 Personalized genetic summary
- 💊 Medication metabolism overview
- 🔗 Gene-gene interaction networks
- 🎯 Clinical recommendations
- 📈 Key findings and insights

---

## Table of Contents

- [Script Overview](#script-overview)
- [Generation Process](#generation-process)
- [Summary Sections](#summary-sections)
- [Data Sources](#data-sources)
- [Output Format](#output-format)
- [Usage](#usage)
- [Customization](#customization)
- [Related Files](#related-files)

---

## Script Overview

### Location

`scripts/generate_personalized_summary.py`

### Purpose

Generates a personalized summary document that:
- Highlights key genetic findings
- Summarizes medication metabolism status
- Identifies gene-gene interactions
- Provides clinical recommendations
- Creates an actionable overview

### Dependencies

```python
from database_manager import GeneticProfileDB
from pathlib import Path
import markdown
```

---

## Generation Process

### Step 1: Load Database

```python
db = GeneticProfileDB()
```

### Step 2: Gather Data

The script collects:
- All genes and their information
- Trait associations
- Health condition associations
- Pharmacogenomic data
- Gene-gene interactions
- Clinical findings from primary sources

### Step 3: Analyze and Synthesize

- Identifies key patterns
- Groups related findings
- Prioritizes important information
- Creates actionable insights

### Step 4: Generate Markdown

Creates structured markdown with:
- Executive summary
- Key findings
- Strengths and sensitivities
- Medication metabolism
- Gene interactions
- Clinical recommendations

### Step 5: Convert to HTML

Converts markdown to HTML for web display.

---

## Summary Sections

### 1. Executive Summary

**Purpose**: High-level overview of genetic profile

**Content**:
- Total genes analyzed
- Key genetic patterns
- Overall health implications

**Example**:
```markdown
## Executive Summary

Your genetic profile includes N genes with significant associations
to mental health, pain sensitivity, and medication metabolism...
```

### 2. Key Genetic Findings

**Purpose**: Highlight most important genetic variants

**Content**:
- Significant genotypes
- Notable trait associations
- Important health condition links

**Example**:
```markdown
### Key Findings

- **COMT Val/Val**: Associated with increased pain sensitivity
- **HTR2A T/T**: Linked to improved SSRI response
- **CYP2D6 Intermediate Metabolizer**: Affects multiple medications
```

### 3. Strengths and Sensitivities

**Purpose**: Identify genetic advantages and vulnerabilities

**Content**:
- Genetic strengths (protective variants)
- Sensitivities (increased risk variants)
- Balanced presentation

**Example**:
```markdown
### Strengths

- Strong stress response regulation (ADRA2A)
- Efficient serotonin processing (SLC6A4)

### Sensitivities

- Increased pain sensitivity (COMT)
- Slower medication metabolism (CYP2D6)
```

### 4. Medication Metabolism

**Purpose**: Summarize pharmacogenomic findings

**Content**:
- Metabolism status by gene
- Affected medications
- Dosing considerations

**Example**:
```markdown
### Medication Metabolism Overview

**CYP2D6**: Intermediate Metabolizer
- Affected medications: Citalopram, Venlafaxine, Codeine
- Consider: Lower starting doses, monitor for side effects

**CYP2C19**: Normal Metabolizer
- Standard dosing appropriate
```

### 5. Gene-Gene Interactions

**Purpose**: Highlight important genetic interactions

**Content**:
- Interaction networks
- Combined effects
- Clinical significance

**Example**:
```markdown
### Key Interactions

**COMT ↔ ADRA2A**: 
- Combined effect on stress response
- May influence ADHD symptom severity

**HTR2A ↔ SLC6A4**:
- Serotonin system regulation
- Affects antidepressant response
```

### 6. Clinical Recommendations

**Purpose**: Actionable guidance based on genetic profile

**Content**:
- Medication considerations
- Lifestyle recommendations
- Monitoring suggestions
- Healthcare provider guidance

**Example**:
```markdown
### Recommendations

1. **Medication Management**:
   - Start with lower doses for CYP2D6-metabolized medications
   - Monitor for side effects closely

2. **Pain Management**:
   - Consider non-pharmacological approaches
   - Be aware of increased pain sensitivity

3. **Mental Health**:
   - SSRI medications may be particularly effective
   - Monitor mood and response closely
```

---

## Data Sources

### Database Queries

The script queries:
- `get_all_genes()` - All genes
- `get_trait_associations_for_gene()` - Trait data
- `get_health_conditions_for_gene()` - Condition data
- `get_pharmacogenomic_data_for_gene()` - Medication data
- `get_interacting_genes()` - Interaction data

### Primary Sources

Integrates findings from:
- Pharmacogenomic test reports
- Genetics consultation letters
- Clinical health records

---

## Output Format

### Markdown File

**Location**: `Your_Genetic_Profile_Summary.md`

**Structure**:
```markdown
# Your Genetic Profile Summary

## Executive Summary
...

## Key Genetic Findings
...

## Strengths and Sensitivities
...

## Medication Metabolism
...

## Gene-Gene Interactions
...

## Clinical Recommendations
...
```

### HTML Generation

**Generated dynamically from database** - No static files

- Generated on-demand from database
- Styled for readability
- Includes navigation
- Clickable citations
- Always up-to-date with latest database content

---

## Usage

### Command Line

```bash
# From project root
python3 scripts/generate_personalized_summary.py
```

### Python Script

```python
from scripts.generate_personalized_summary import generate_summary

# Generate summary
generate_summary()
```

### Output

- **Generated dynamically** from database on each request
- **No static files** - always reflects current database state
- Access via `/summary` route in web application

---

## Customization

### Modify Summary Sections

Edit `scripts/generate_personalized_summary.py`:

```python
def generate_summary():
    # Customize section generation
    summary = []
    summary.append(generate_executive_summary())
    summary.append(generate_custom_section())  # Add custom section
    # ...
```

### Adjust Detail Level

Control how much detail to include:

```python
# Detailed mode
include_detailed_findings = True

# Concise mode
include_detailed_findings = False
```

### Filter by Category

Focus on specific areas:

```python
# Only mental health genes
mental_health_genes = ['COMT', 'HTR2A', 'SLC6A4', 'ADRA2A']

# Only pharmacogenomic genes
pharm_genes = ['CYP2D6', 'CYP2C19', 'CYP1A2']
```

---

## Related Files

### Scripts
- `scripts/generate_personalized_summary.py` - Main generation script

### Output
- `Your_Genetic_Profile_Summary.md` - Markdown source
- `output/Your_Genetic_Profile_Summary.html` - HTML output

### Templates
- `templates/summary.html` - Summary page template

### Python
- `app.py` - Summary route handler
- `database_manager.py` - Data access

---

## Debugging

### Summary Not Generating

1. **Check database connection**:
   ```python
   from database_manager import GeneticProfileDB
   db = GeneticProfileDB()
   genes = db.get_all_genes()
   print(f"Found {len(genes)} genes")
   ```

2. **Verify data exists**:
   ```python
   # Check for required data
   db = GeneticProfileDB()
   genes = db.get_all_genes()
   traits = db.get_trait_associations_for_gene(1)
   pharm = db.get_pharmacogenomic_data_for_gene(1)
   ```

3. **Check file permissions**:
   ```bash
   ls -la Your_Genetic_Profile_Summary.md
   chmod 644 Your_Genetic_Profile_Summary.md
   ```

### Missing Sections

1. **Check data availability**:
   - Verify genes have trait associations
   - Check pharmacogenomic data exists
   - Confirm interactions are recorded

2. **Review generation logic**:
   - Check conditional statements
   - Verify data filtering
   - Review section generation functions

### HTML Not Rendering

1. **Regenerate HTML**:
   ```bash
   # Summary is generated automatically from database
   # Access via web interface at /summary route
   ```

2. **Check markdown syntax**:
   - Verify proper heading levels
   - Check list formatting
   - Ensure proper markdown structure

---

## Future Enhancements

- [ ] Interactive summary with expandable sections
- [ ] Comparison with population averages
- [ ] Risk scoring for conditions
- [ ] Medication interaction checker
- [ ] Personalized lifestyle recommendations
- [ ] Export to PDF
- [ ] Shareable summary links
- [ ] Version history tracking

