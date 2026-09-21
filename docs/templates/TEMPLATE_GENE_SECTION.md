# Gene Section Template

This template defines the standard format for all gene sections. Use this as a reference when adding or modifying gene sections.

## Section Structure

```markdown
## [Number]. [Gene Name] - [Full Gene Name]

**Genotype:** [Genotype Value]

**SNP:** [SNP ID] ([Source])

### Database Sources

**SNPedia:**

- **SNP:** [SNP ID] (use "SNPs:" if multiple)
- **Link:** <URL> (use "Links:" if multiple)
- **Key Information:** [Description with citation].[citation]

**GWAS Catalog:**

- **Gene Associations:** <URL>
- **Key Information:** [Description with citation].[citation]

**GTR (Genetic Testing Registry):**

- **Gene:** [Gene Symbol]
- **Link:** <URL>
- **Key Information:** [Description with citation].[citation]

**PubMed:**

- [Description text].[citation range]

### Trait Associations

- [Trait name][citation]
- [Trait name] [description][citation]

### Health Condition Associations

- [Condition name][citation]
- [Condition name] [description][citation]

### Gene-Gene Interactions

**Interaction with [Gene Name (Section X)](#link):**
[Description text with citations].[citation]

### Research Findings

**[Subsection Title]:**
[Content with citations].[citation]
```

## Formatting Rules

### Citations

- **ALWAYS use square brackets:** `[1,2,3]` or `[1-15]`
- **NEVER use parentheses:** `(1,2,3)` ❌
- **For descriptive text:** `[description][citation]` not `[description](citation)`

### Database Sources

- **SNPedia:** Use "SNP:" for single, "SNPs:" for multiple
- **GWAS Catalog:** Always use "Key Information:" (not "Key Findings:")
- **GTR:** Always includes Gene, Link, and Key Information
- **All headings:** Must have blank line after heading before bullet points

### Trait/Health Condition Associations

- Use consistent citation format: `[citation]` or `[description][citation]`
- No mixing of formats

### Section Order

1. Gene header with number
2. Genotype
3. SNP
4. Database Sources
5. Trait Associations
6. Health Condition Associations
7. Gene-Gene Interactions
8. Research Findings

## Examples

### Single SNP

```markdown
**SNPedia:**

- **SNP:** rs1800544
- **Link:** <https://www.snpedia.com/index.php/Rs1800544>
- **Key Information:** Description.[128]
```

### Multiple SNPs

```markdown
**SNPedia:**

- **SNPs:** rs3745274, rs28399499
- **Links:** <URL1>, <URL2>
- **Key Information:** Description.[138]
```

### Trait with Description

```markdown
- Working memory capacity [intermediate][21,22,23]
- Stress resilience [HIGHER - protective][28,43,123]
```

### Trait without Description

```markdown
- ADHD susceptibility and severity[1,2,3]
- Attention span and sustained vigilance[4,5]
```
