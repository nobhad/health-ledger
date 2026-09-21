# Pharmacogenomic Data Feature

**Last Updated**: December 7, 2025

## Overview

The Pharmacogenomic Data system manages drug metabolism information, genotype-phenotype relationships, and medication-specific guidance based on genetic variants. It tracks how genetic variations affect medication metabolism, efficacy, and dosing requirements.

**Key Features:**

- 💊 Drug metabolism status tracking
- 🧬 Genotype-phenotype relationships
- 📋 Affected medications database
- ⚠️ Dosing recommendations
- 🔗 Gene-medication associations

---

## Table of Contents

- [Pharmacogenomic Data](#pharmacogenomic-data)
- [Metabolism Status](#metabolism-status)
- [Genotype-Phenotype](#genotype-phenotype)
- [Affected Medications](#affected-medications)
- [Data Import](#data-import)
- [Querying Data](#querying-data)
- [Related Files](#related-files)

---

## Pharmacogenomic Data

### Database Schema

```sql
CREATE TABLE pharmacogenomic_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id INTEGER NOT NULL,
    metabolism_status TEXT NOT NULL,
    genotype_phenotype TEXT,
    citation_id INTEGER,
    FOREIGN KEY (gene_id) REFERENCES genes(id),
    FOREIGN KEY (citation_id) REFERENCES citations(id)
);

CREATE TABLE gene_pharmacogenomic_drugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacogenomic_data_id INTEGER NOT NULL,
    drug_name TEXT NOT NULL,
    FOREIGN KEY (pharmacogenomic_data_id) REFERENCES pharmacogenomic_data(id)
);
```

### Data Structure

Each pharmacogenomic record includes:

- **Gene**: The gene being tested
- **Metabolism Status**: How the gene affects drug metabolism
- **Genotype/Phenotype**: Specific genetic variant
- **Affected Medications**: List of medications affected

---

## Metabolism Status

### Status Types

1. **Normal Metabolizer**
   - Standard metabolism rate
   - Normal dosing appropriate
   - Example: CYP2C19 Normal

2. **Intermediate Metabolizer**
   - Reduced metabolism rate
   - May need lower doses
   - Monitor for side effects
   - Example: CYP2D6 Intermediate

3. **Poor Metabolizer**
   - Very slow metabolism
   - Lower doses required
   - Increased risk of side effects
   - Example: CYP2D6 Poor

4. **Rapid Metabolizer**
   - Fast metabolism
   - May need higher doses
   - Reduced drug efficacy
   - Example: CYP2D6 Rapid

5. **Ultrarapid Metabolizer**
   - Very fast metabolism
   - Significantly higher doses may be needed
   - Risk of treatment failure
   - Example: CYP2D6 Ultrarapid

### Example Data

```python
{
    "gene_symbol": "CYP2D6",
    "metabolism_status": "Intermediate Metabolizer",
    "genotype_phenotype": "*1/*4",
    "affected_medications": [
        "Citalopram",
        "Venlafaxine",
        "Codeine",
        "Tramadol"
    ]
}
```

---

## Genotype-Phenotype

### Common Genotypes

**CYP2D6:**

- `*1/*1` - Normal Metabolizer
- `*1/*4` - Intermediate Metabolizer
- `*4/*4` - Poor Metabolizer
- `*1/*1xN` - Ultrarapid Metabolizer

**CYP2C19:**

- `*1/*1` - Normal Metabolizer
- `*1/*2` - Intermediate Metabolizer
- `*2/*2` - Poor Metabolizer

**COMT:**

- `Val/Val` - Fast COMT activity
- `Val/Met` - Intermediate activity
- `Met/Met` - Slow COMT activity

### Phenotype Mapping

```python
GENOTYPE_PHENOTYPE_MAP = {
    "CYP2D6": {
        "*1/*1": "Normal Metabolizer",
        "*1/*4": "Intermediate Metabolizer",
        "*4/*4": "Poor Metabolizer"
    },
    "CYP2C19": {
        "*1/*1": "Normal Metabolizer",
        "*1/*2": "Intermediate Metabolizer",
        "*2/*2": "Poor Metabolizer"
    }
}
```

---

## Affected Medications

### Medication Categories

1. **Antidepressants**
   - SSRIs (Citalopram, Escitalopram)
   - SNRIs (Venlafaxine, Duloxetine)
   - Tricyclics (Amitriptyline, Nortriptyline)

2. **Antipsychotics**
   - Risperidone
   - Haloperidol
   - Aripiprazole

3. **Pain Medications**
   - Codeine
   - Tramadol
   - Oxycodone

4. **Stimulants**
   - Amphetamines
   - Methylphenidate

5. **Other**
   - Warfarin (VKORC1, CYP2C9)
   - Clopidogrel (CYP2C19)

### Gene-Medication Associations

**CYP2D6:**

- Citalopram, Venlafaxine, Codeine, Tramadol, Risperidone

**CYP2C19:**

- Citalopram, Escitalopram, Clopidogrel, Omeprazole

**CYP2C9:**

- Warfarin, Phenytoin, Ibuprofen

**CYP1A2:**

- Clozapine, Olanzapine, Theophylline

---

## Data Import

### Import Script

**Location**: `scripts/add_pharmacogenomic.py`

### Import Process

1. **Read GeneSight Report**
   - Extract pharmacogenomic data
   - Parse genotype-phenotype information
   - Identify affected medications

2. **Add to Database**

   ```python
   # Add pharmacogenomic data
   pharm_id = db.add_pharmacogenomic_data(
       gene_id=gene_id,
       metabolism_status="Intermediate Metabolizer",
       genotype_phenotype="*1/*4",
       citation_id=163  # GeneSight report
   )
   
   # Add affected medications
   for medication in medications:
       db.add_gene_pharmacogenomic_drug(
           pharmacogenomic_data_id=pharm_id,
           drug_name=medication
       )
   ```

### Usage

```bash
python3 scripts/add_pharmacogenomic.py
```

---

## Querying Data

### Get Pharmacogenomic Data for Gene

```python
from database_manager import GeneticProfileDB

db = GeneticProfileDB()

# Get data for specific gene
pharm_data = db.get_pharmacogenomic_data_for_gene(gene_id)

print(f"Metabolism Status: {pharm_data['metabolism_status']}")
print(f"Genotype: {pharm_data['genotype_phenotype']}")
print(f"Medications: {pharm_data['affected_medications']}")

db.close()
```

### Get All Pharmacogenomic Data

```python
all_pharm = db.get_all_pharmacogenomic_data()

for pharm in all_pharm:
    print(f"{pharm['gene_symbol']}: {pharm['metabolism_status']}")
```

### Get Medications for Gene

```python
medications = db.get_medications_for_gene(gene_id)
# Returns: ["Citalopram", "Venlafaxine", "Codeine"]
```

### Get Genes for Medication

```python
genes = db.get_genes_for_medication("Citalopram")
# Returns genes that affect Citalopram metabolism
```

### API Endpoint

```bash
# Get all pharmacogenomic data
curl http://localhost:5001/api/pharmacogenomic

# Get gene info (includes pharmacogenomic data)
curl http://localhost:5001/api/gene-info?gene=CYP2D6
```

---

## Clinical Implications

### Dosing Considerations

**Intermediate Metabolizer:**

- Start with lower doses
- Monitor for side effects
- May need dose adjustments

**Poor Metabolizer:**

- Use lower starting doses
- Consider alternative medications
- Close monitoring required

**Rapid/Ultrarapid Metabolizer:**

- May need higher doses
- Monitor for treatment failure
- Consider alternative medications

### Example Recommendations

**CYP2D6 Intermediate Metabolizer:**

```text
For medications metabolized by CYP2D6:
- Start with 50% of standard dose
- Monitor for side effects
- Consider therapeutic drug monitoring
- Alternative: Use medications not metabolized by CYP2D6
```

**CYP2C19 Poor Metabolizer:**

```text
For clopidogrel:
- Consider alternative antiplatelet therapy
- If using clopidogrel, may need higher doses
- Monitor for treatment efficacy
```

---

## Related Files

### Scripts

- `scripts/add_pharmacogenomic.py` - Import pharmacogenomic data
- `scripts/add_pharmacogenomic_to_document.py` - Add to markdown document

### Python

- `database_manager.py` - Pharmacogenomic database operations
- `app.py` - API endpoints for pharmacogenomic data

### Source Data

- `primary_sources/<LastFirst>_GeneticTesting_Genesight_<date>.pdf` - GeneSight report

---

## Debugging

### Missing Pharmacogenomic Data

1. **Check gene exists**:

   ```python
   gene = db.get_gene_by_symbol("CYP2D6")
   if not gene:
       print("Gene not found")
   ```

2. **Check pharmacogenomic data**:

   ```python
   pharm = db.get_pharmacogenomic_data_for_gene(gene['id'])
   if not pharm:
       print("No pharmacogenomic data found")
   ```

### Medication Not Listed

1. **Check medication associations**:

   ```python
   medications = db.get_medications_for_gene(gene_id)
   if "Citalopram" not in medications:
       print("Medication not associated with gene")
   ```

2. **Add missing medication**:

   ```python
   db.add_gene_pharmacogenomic_drug(
       pharmacogenomic_data_id=pharm_id,
       drug_name="Citalopram"
   )
   ```

### Incorrect Metabolism Status

1. **Verify genotype-phenotype mapping**:

   ```python
   pharm = db.get_pharmacogenomic_data_for_gene(gene_id)
   print(f"Genotype: {pharm['genotype_phenotype']}")
   print(f"Status: {pharm['metabolism_status']}")
   ```

2. **Check GeneSight report** for correct classification

---

## Future Enhancements

- [ ] Drug interaction checker
- [ ] Dosing calculator
- [ ] Medication recommendations engine
- [ ] Clinical decision support
- [ ] Integration with medication databases
- [ ] Alert system for significant findings
- [ ] Export medication list
- [ ] Medication history tracking
