# Display Inconsistencies in Genetic Profile Document

## Summary
This document identifies all inconsistencies in how data is displayed across the 17 gene sections in `Genetic_Profile_Non_Pharmacogenomic_Corrected.md`.

---

## 1. SNPedia Section Field Names

### Inconsistency: SNP vs SNPs vs Gene Page

**Pattern 1: "SNP:" (singular) - Used in:**
- ADRA2A (Section 1)
- CES1A1 (Section 2) 
- COMT (Section 3)
- CYP1A2 (Section 4)
- CYP3A4 (Section 9)
- CYP3A5 (Section 10)
- SLC6A4 (Section 14)
- UGT2B15 (Section 16)

**Pattern 2: "SNPs:" (plural) - Used in:**
- CYP2B6 (Section 5)
- CYP2C9 (Section 6)
- CYP2C19 (Section 7)
- HLA-A (Section 11)
- HLA-B (Section 12)
- HTR2A (Section 13)
- UGT1A1 (Section 15)
- VKORC1 (Section 17)

**Pattern 3: "Gene Page:" - Used in:**
- CYP2D6 (Section 8) - Unique format, no SNP field

**Recommendation:** Standardize to "SNP:" for single, "SNPs:" for multiple, or always use "SNPs:" regardless of count.

---

## 2. SNPedia "Genotype" Field

### Inconsistency: Only ADRA2A has Genotype field

**Has Genotype field:**
- ADRA2A (Section 1): `- **Genotype:** C/G`

**Missing Genotype field:**
- All other 16 sections

**Recommendation:** Either add Genotype to all sections or remove from ADRA2A for consistency.

---

## 3. SNPedia Link Field Names

### Inconsistency: Link vs Links

**Pattern 1: "Link:" (singular) - Used when:**
- Single SNP listed (ADRA2A, CES1A1, COMT, CYP1A2, CYP3A4, CYP3A5, SLC6A4, UGT2B15)
- CYP2D6 (Gene Page format)

**Pattern 2: "Links:" (plural) - Used when:**
- Multiple SNPs listed (CYP2B6, CYP2C9, CYP2C19, HLA-A, HLA-B, HTR2A, UGT1A1, VKORC1)

**Status:** This is actually CONSISTENT - plural matches plural SNPs. No change needed.

---

## 4. GWAS Catalog "Gene Associations" Format

### Inconsistency: Direct link vs "Search available at"

**Pattern 1: Direct link (no prefix) - Used in:**
- ADRA2A: `<https://www.ebi.ac.uk/gwas/genes/ADRA2A>`
- COMT: `<https://www.ebi.ac.uk/gwas/genes/COMT>`
- CYP1A2: `<https://www.ebi.ac.uk/gwas/genes/CYP1A2>`
- UGT1A1: `<https://www.ebi.ac.uk/gwas/genes/UGT1A1>`

**Pattern 2: "Search available at" prefix - Used in:**
- CES1A1: `Search available at <https://www.ebi.ac.uk/gwas/genes/CES1>`
- CYP2B6: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP2B6>`
- CYP2C9: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP2C9>`
- CYP2C19: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP2C19>`
- CYP2D6: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP2D6>`
- CYP3A4: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP3A4>`
- CYP3A5: `Search available at <https://www.ebi.ac.uk/gwas/genes/CYP3A5>`
- HLA-A: `Search available at <https://www.ebi.ac.uk/gwas/genes/HLA-A>`
- HLA-B: `Search available at <https://www.ebi.ac.uk/gwas/genes/HLA-B>`
- HTR2A: `Search available at <https://www.ebi.ac.uk/gwas/genes/HTR2A>`
- SLC6A4: `Search available at <https://www.ebi.ac.uk/gwas/genes/SLC6A4>`
- UGT2B15: `Search available at <https://www.ebi.ac.uk/gwas/genes/UGT2B15>`
- VKORC1: `Search available at <https://www.ebi.ac.uk/gwas/genes/VKORC1>`

**Recommendation:** Standardize to one format. Either always use direct links or always use "Search available at" prefix.

---

## 5. GWAS Catalog "Key Findings" Citations

### Inconsistency: Some have citations, some don't

**Has citations:**
- ADRA2A: `[130]`
- COMT: `[135]`
- CYP1A2: `[137]`
- HLA-A: `[14]`
- UGT1A1: `[159,160]`

**Missing citations:**
- CES1A1: "Associations with lipid metabolism and cardiovascular traits."
- CYP2B6: "Associations with drug metabolism and environmental chemical processing."
- CYP2C9: "Associations with arachidonic acid metabolism and cardiovascular disease."
- CYP2C19: "Associations with steroid hormone metabolism and cardiovascular traits."
- CYP2D6: "Associations with neurosteroid metabolism and environmental toxin processing."
- CYP3A4: "Associations with vitamin D processing, testosterone and estrogen metabolism, and cancer risk."
- CYP3A5: "Associations with blood pressure regulation and hypertension susceptibility."
- HLA-B: "Strong associations with autoimmune diseases, infectious disease responses, and drug hypersensitivity reactions."
- HTR2A: "Associations with personality traits, anxiety, and mood disorders."
- SLC6A4: "Associations with stress resilience, anxiety, and mood regulation traits."
- UGT2B15: "Associations with hormone-sensitive cancers and sex hormone regulation."
- VKORC1: "Multiple GWAS studies identify VKORC1 as a principal genetic determinant of warfarin maintenance dose and bleeding risk."

**Recommendation:** Either add citations to all Key Findings or remove citations from all for consistency.

---

## 6. GWAS Catalog Additional Fields

### Inconsistency: UGT1A1 has extra field

**Unique to UGT1A1:**
- Has additional field: `- **Bilirubin Trait:** <https://www.ebi.ac.uk/gwas/efotraits/EFO_0004570>`

**All other sections:**
- Only have "Gene Associations" and "Key Findings"

**Recommendation:** Either remove this field from UGT1A1 or add similar trait-specific fields to other sections where relevant.

---

## 7. Gene Section Header Format

### Inconsistency: Blank line after section number

**Pattern 1: Has blank line after section number:**
- All sections appear to have blank lines consistently

**Pattern 2: Genotype field placement:**
- Most sections: Genotype on line after blank line
- CYP3A5 (Section 10): Has "**SNP:**" instead of "**Genotype:**"
- VKORC1 (Section 17): Has "**SNPs:**" instead of "**Genotype:**"

**Recommendation:** Standardize all sections to use "**Genotype:**" field, or document why CYP3A5 and VKORC1 are different.

---

## 8. Trait Associations Format

### Inconsistency: Citation formatting in brackets

**Pattern 1: Citations in square brackets:**
- Most entries: `[1,2,3]` or `[16,17]`

**Pattern 2: Citations in parentheses:**
- COMT (Section 3): `[intermediate](21,22,23)` - has descriptive text in brackets before citation
- COMT: `[balanced](24,25,26)`
- COMT: `[moderate](28,29)`
- COMT: `[moderate](32,33,34)`
- COMT: `[balanced](35)`
- COMT: `[intermediate/balanced](35,36)`
- HLA-B (Section 12): `[MHC](112)` - has descriptive text in brackets
- HLA-B: `[type-specific](110,114)`
- HLA-B: `[IBS](0)`
- SLC6A4 (Section 14): `[LOWER baseline](28,122)`
- SLC6A4: `[LOWER susceptibility](122,124)`
- SLC6A4: `[LOWER risk](125,126)`
- SLC6A4: `[associated with longer lifespan](0)`

**Recommendation:** Standardize citation format. Either:
- Use square brackets for all: `[1,2,3]`
- Or use descriptive format consistently: `[description][1,2,3]`

---

## 9. Health Condition Associations Format

### Inconsistency: Citation formatting

**Pattern 1: Standard citations:**
- Most entries: `[1,2,3]`

**Pattern 2: Citations with [0]:**
- Multiple sections use `[0]` which may be a placeholder

**Pattern 3: Descriptive text in brackets:**
- HLA-B: `[type-specific](110,114)`
- SLC6A4: `[LOWER baseline](28,122)`, `[LOWER susceptibility](122,124)`, `[LOWER risk](125,126)`

**Recommendation:** Standardize format across all sections.

---

## 10. Database Sources Section Order

### Status: CONSISTENT
All sections follow the same order:
1. SNPedia
2. GWAS Catalog
3. GTR (Genetic Testing Registry)
4. PubMed

No changes needed.

---

## 11. GTR Section Format

### Status: CONSISTENT
All sections have:
- `- **Gene:** [Gene Name]`
- `- **Link:** [URL]`
- `- **Key Information:** [Text with citation]`

No changes needed.

---

## 12. PubMed Section Format

### Status: CONSISTENT
All sections have:
- `- [Description text].[citation range]`

No changes needed.

---

## Priority Recommendations

### High Priority (Affects readability):
1. **Standardize GWAS Catalog format** - Choose either direct links or "Search available at" prefix
2. **Standardize Key Findings citations** - Either all have citations or none do
3. **Standardize SNPedia field names** - Use consistent "SNP:" vs "SNPs:" pattern
4. **Standardize Trait/Health Condition citation format** - Remove mixed bracket/parentheses usage

### Medium Priority (Affects completeness):
5. **Add or remove Genotype field** - Make consistent across all sections
6. **Remove or standardize extra GWAS fields** - UGT1A1's "Bilirubin Trait" field

### Low Priority (Minor formatting):
7. **Standardize section header spacing** - Ensure consistent blank lines

